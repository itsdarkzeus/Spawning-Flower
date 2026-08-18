"""Pan-seared fish fillet — lofted core, flattened underside.

Same division of labour as the fried chicken: the CAD stage gives the fillet its
mass and taper, and the mesh stage gives it the seared surface. The difference
is the *kind* of noise. Breading is isotropic - crumbs are equally lumpy in
every direction. A fish fillet is not: it has grain running along its length,
where the muscle flakes separate. That is what `axis_scale` in
`mesh_kit.roughen` is for - squash the noise field along the fillet's long axis
and the lumps stretch into streaks that follow the flake lines.

The fillet also carries a seam down the centre where the two muscle lobes meet.
That is a deterministic crease, not noise, so it is applied as an explicit
Gaussian groove rather than left to the fractal.

Units are millimetres. The fillet is returned lying along X, centred in XY,
resting on Z=0 with a flattened underside so it sits on the plate.
"""

from __future__ import annotations

import numpy as np
from build123d import (
    Align,
    Box,
    BuildPart,
    BuildSketch,
    Ellipse,
    Locations,
    Mode,
    Plane,
    Pos,
    Rot,
    loft,
)

# (length fraction, half-width, half-height, lateral lean)
# A sole/plaice fillet is FLAT - roughly 190 x 62 x 13 mm. An earlier version
# ran 24 mm thick and read as a chicken tender rather than fish; the thickness
# of these sections is the single thing that decides whether the silhouette is
# right.
FILLET_SECTIONS = [
    (0.00,  4.0, 1.2,  0.0),   # tail tip
    (0.10, 14.0, 3.4,  1.2),
    (0.26, 24.0, 5.2,  2.2),
    (0.46, 30.0, 6.4,  1.2),
    (0.64, 31.0, 6.6, -0.5),
    (0.80, 27.0, 5.8, -1.6),
    (0.92, 18.0, 4.0, -2.2),
    (1.00,  8.0, 2.0, -2.2),
]

FILLET_LENGTH = 190.0
UNDERCUT = 1.8          # how much of the rounded underside is sliced flat


def make_fillet(sections=FILLET_SECTIONS, length: float = FILLET_LENGTH):
    """Smooth CAD core of the fillet, flat-bottomed and lying along X."""
    with BuildPart() as core:
        for frac, half_w, half_h, lean in sections:
            with BuildSketch(Plane.XY.offset(frac * length)):
                with Locations((lean, 0.0)):
                    Ellipse(half_w, half_h)
        loft()

    # Lay it down. The loft runs along Z with the section's x-radius as width,
    # so it takes TWO rotations: Ry brings the length onto X, then Rx swaps the
    # section's axes back so half-width reads across the plate and half-height
    # reads upward. Ry alone stands the fillet on its side.
    piece = Rot(90.0, 0.0, 0.0) * (Rot(0.0, 90.0, 0.0) * core.part)

    # Slice the rounded underside flat so the fillet sits on the plate rather
    # than balancing on a tangent line.
    box = piece.bounding_box()
    knife = Box(600.0, 400.0, 200.0, align=(Align.CENTER, Align.CENTER, Align.MAX))
    piece = piece - Pos(0.0, 0.0, box.min.Z + UNDERCUT) * knife

    box = piece.bounding_box()
    return Pos(-box.center().X, -box.center().Y, -box.min.Z) * piece


def sear(verts, faces, seed=11, grain=0.85, grain_freq=0.11,
         mottle=0.42, mottle_freq=0.32, crisp=0.18, crisp_freq=0.75,
         flake=2.4, flake_freq=0.34, micro=0.55, micro_freq=1.05, seam_depth=2.4, seam_width=6.5):
    """Seared surface: grain along the length, mottling, and a centre seam.

    `axis_scale` compresses the noise sample along X so the features elongate
    into flake lines instead of reading as generic bumpiness.
    """
    from mesh_kit import roughen, vertex_normals

    # Fade the displacement out towards the tips. The loft converges to a very
    # small section there, so full-amplitude noise on a handful of tightly
    # packed vertices throws visible spikes off the ends.
    x = verts[:, 0]
    half = max(abs(x).max(), 1e-6)
    t = np.clip((1.0 - abs(x) / half) / 0.16, 0.0, 1.0)
    fade = 0.12 + 0.88 * (t * t * (3.0 - 2.0 * t))

    v = roughen(verts, faces, amplitude=grain, frequency=grain_freq, octaves=4,
                seed=seed, bias=0.05, axis_scale=(0.22, 1.0, 1.0), mask=fade)
    v = roughen(v, faces, amplitude=mottle, frequency=mottle_freq, octaves=3,
                seed=seed + 613, bias=0.0, axis_scale=(0.55, 1.0, 1.0), mask=fade)
    v = roughen(v, faces, amplitude=crisp, frequency=crisp_freq, octaves=2,
                seed=seed + 1289, bias=0.0, axis_scale=(0.4, 1.0, 1.0), mask=fade)

    # Flaking. Fish flakes separate ACROSS the fillet, so the field has to vary
    # quickly along X and slowly across Y - the opposite anisotropy to the
    # lengthwise grain above. Ridged noise, not fbm: taking 1-|n| puts a crease
    # where the field crosses zero, which is what reads as a flake edge instead
    # of a soft bump.
    from mesh_kit import ridged, vertex_normals as _vn

    n = _vn(v, faces)
    up = np.clip(n[:, 2], 0.0, 1.0)          # crust only on the seared face

    r = ridged(v * np.array([1.0, 0.22, 0.22]), octaves=3, frequency=flake_freq,
               seed=seed + 77, sharpness=2.3)
    v = v + n * ((r - 0.45) * flake * fade * up)[:, None]

    # A second, finer ridge pass for the crisped micro-texture on top of the
    # flakes. Sub-millimetre displacement is invisible at plate scale, so both
    # passes are deliberately coarse enough to catch the light.
    n = _vn(v, faces)
    r2 = ridged(v * np.array([1.0, 0.45, 0.45]), octaves=2, frequency=micro_freq,
                seed=seed + 401, sharpness=2.8)
    v = v + n * ((r2 - 0.45) * micro * fade * up)[:, None]

    # Centre seam: a Gaussian groove along y = 0, pressed only into the upward
    # facing surface so the flat underside is untouched.
    normals = vertex_normals(v, faces)
    upward = np.clip(normals[:, 2], 0.0, 1.0)
    groove = np.exp(-(v[:, 1] / seam_width) ** 2) * upward * fade
    v = v - normals * (groove * seam_depth)[:, None]
    return v


def gen_step():
    from cadpy.assembly import label_shape

    return label_shape(make_fillet(), "fish_fillet")


if __name__ == "__main__":
    gen_step()
