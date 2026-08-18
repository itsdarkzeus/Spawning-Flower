"""Per-vertex colour for the food meshes.

glTF carries a COLOR_0 attribute that multiplies into the base colour, so a
mesh can vary in colour across its surface with no texture and no UVs at all.
That is what makes char marks on a leek, browning on a seared fillet and
density variation in a sauce possible.

Every function here returns an Nx3 array of **sRGB** colours, one per vertex.
`mesh_kit.write_glb` converts them to linear on the way out; the preview
renderer takes them as-is, which is the same split the flat colours use.

The colour fields are driven by the same noise used for displacement, so the
shading lines up with the geometry - dark char sits in the charred dents, not
somewhere unrelated.
"""

from __future__ import annotations

import numpy as np

from mesh_kit import fbm, vertex_normals


def _mix(colour_a, colour_b, t):
    """Per-vertex blend. `t` is 0-1, shape (N,)."""
    a = np.asarray(colour_a, dtype=float)[None, :]
    b = np.asarray(colour_b, dtype=float)[None, :]
    t = np.clip(np.asarray(t, dtype=float), 0.0, 1.0)[:, None]
    return a * (1.0 - t) + b * t


def _smoothstep(edge0, edge1, x):
    t = np.clip((x - edge0) / max(edge1 - edge0, 1e-9), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def _unit(x):
    """Map fbm output (about -1..1) onto 0..1."""
    return np.clip(x * 0.5 + 0.5, 0.0, 1.0)


# --------------------------------------------------------------------------

def fish(verts, faces, seed=11,
         pale=(0.62, 0.45, 0.25), gold=(0.46, 0.28, 0.12), brown=(0.26, 0.14, 0.06)):
    """Seared fillet: gold overall, browner in the seared patches and at edges.

    Two contributions. A patchy browning field follows the grain, so the darker
    areas read as where the pan actually caught. Then the edges darken, because
    a fillet's rim always colours harder than its middle - that is done from the
    normal's Z component rather than from noise, since it is a fact about the
    geometry, not a random variation.
    """
    grain = _unit(fbm(verts * np.array([0.22, 1.0, 1.0]), octaves=4,
                      frequency=0.10, seed=seed))
    patch = _smoothstep(0.28, 0.66, grain)

    normals = vertex_normals(verts, faces)
    col = _mix(pale, gold, patch)

    # Browned border. Doing this from the surface normal only darkens the
    # silhouette, which is nearly invisible from directly above - and top-down
    # is how a plated dish is photographed. So the falloff is a 2D elliptical
    # distance from the fillet's centreline instead, which paints a visible
    # band around the edge of the top face.
    ax = max(np.abs(verts[:, 0]).max(), 1e-6)
    ay = max(np.abs(verts[:, 1]).max(), 1e-6)
    radial = np.sqrt((verts[:, 0] / ax) ** 2 + (verts[:, 1] / ay) ** 2)
    border = _smoothstep(0.58, 1.0, radial)
    col = _mix_arr(col, brown, 0.80 * border)

    # Plus the true silhouette, which catches the sides in an angled view.
    rim = np.power(1.0 - np.abs(normals[:, 2]), 1.6)
    col = _mix_arr(col, brown, 0.55 * rim)

    # The centre seam reads as a dark line, not just a groove.
    seam = np.exp(-(verts[:, 1] / 5.0) ** 2) * np.clip(normals[:, 2], 0.0, 1.0)
    col = _mix_arr(col, brown, 0.60 * seam)
    return np.clip(col, 0.0, 1.0)


def leek(verts, faces, seed=31, length_axis=0,
         green=(0.22, 0.34, 0.10), tip=(0.15, 0.25, 0.07),
         root=(0.72, 0.74, 0.60), char=(0.04, 0.04, 0.03)):
    """Charred leek: pale at the root, green along the stalk, black char bands.

    The root-to-tip gradient replaces what used to be a mesh split - one mesh
    with a colour ramp says the same thing and costs nothing.

    Char is deliberately high contrast and banded: real char sits in discrete
    scorched patches where the stalk touched the pan, not as a gentle wash, so
    the noise is pushed through a hard smoothstep.
    """
    x = verts[:, length_axis]
    span = max(x.max() - x.min(), 1e-6)
    t = (x - x.min()) / span

    col = _mix(root, green, _smoothstep(0.02, 0.13, t))
    col = col * (1.0 - _smoothstep(0.55, 1.0, t)[:, None]) + \
        np.asarray(tip)[None, :] * _smoothstep(0.55, 1.0, t)[:, None]

    scorch = _unit(fbm(verts * np.array([0.55, 1.0, 1.0]), octaves=3,
                       frequency=0.11, seed=seed))
    # Only the stalk chars, not the pale root end.
    burn = _smoothstep(0.50, 0.74, scorch) * _smoothstep(0.10, 0.24, t)
    return np.clip(_mix_arr(col, char, burn), 0.0, 1.0)


def _mix_arr(col, colour_b, t):
    b = np.asarray(colour_b, dtype=float)[None, :]
    t = np.clip(np.asarray(t, dtype=float), 0.0, 1.0)[:, None]
    return col * (1.0 - t) + b * t


def tomato(verts, faces, seed=41,
           skin=(0.46, 0.06, 0.04), bright=(0.60, 0.13, 0.07),
           blister=(0.13, 0.035, 0.03)):
    """Roasted cherry tomato: red skin with blackened blistered spots."""
    n = _unit(fbm(verts, octaves=3, frequency=0.16, seed=seed))
    col = _mix(skin, bright, _smoothstep(0.35, 0.62, n))
    burst = _smoothstep(0.70, 0.88, n)
    return np.clip(_mix_arr(col, blister, burst), 0.0, 1.0)


def sauce(verts, faces, seed=51, base=(0.50, 0.12, 0.035), deep=(0.28, 0.055, 0.02),
          thin=(0.62, 0.24, 0.08), axis_scale=(0.10, 1.0, 1.0)):
    """Sauce: darker where it pools, thinner and lighter along the comb streaks.

    Uses the same anisotropic field as the displacement, so the colour bands
    line up with the ridges a spoon would leave rather than drifting across
    them.
    """
    n = _unit(fbm(verts * np.asarray(axis_scale), octaves=3, frequency=0.30, seed=seed))
    col = _mix(deep, base, _smoothstep(0.25, 0.60, n))
    return np.clip(_mix_arr(col, thin, _smoothstep(0.68, 0.92, n)), 0.0, 1.0)


def herb(verts, faces, seed=61, blade=(0.23, 0.37, 0.13), vein=(0.33, 0.47, 0.19)):
    """Micro herb leaf: slightly paler towards the centre line."""
    y = verts[:, 1]
    span = max(np.abs(y).max(), 1e-6)
    centre = 1.0 - np.clip(np.abs(y) / span, 0.0, 1.0)
    return np.clip(_mix(blade, vein, centre * 0.5), 0.0, 1.0)
