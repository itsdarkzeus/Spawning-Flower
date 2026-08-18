"""Jollof rice mound built from individually instanced grains.

Why not displacement
    Every other surface in this project is a CAD solid pushed around by noise.
    That cannot work here. Displacement moves an existing surface; it can never
    separate one body into many, so a noise-roughened dome reads as lumpy
    porridge, never as rice. Grains have to be actual separate geometry.

    So: a smooth CAD core carries the mound's mass, and a few thousand grain
    ellipsoids are instanced across its surface, laid tangent to it with random
    azimuth. The core stops you seeing through the gaps between grains.

Units are millimetres, Z up, mound resting on Z=0 and centred on the origin.
"""

from __future__ import annotations

import numpy as np
from build123d import BuildPart, BuildSketch, Circle, Locations, Plane, loft

from mesh_kit import frame_from_normal, instance

# Mound profile: (height fraction, radius). A timbale - near-cylindrical with
# a rounded shoulder into a slightly domed top.
MOUND_PROFILE = [
    (0.00, 58.0),
    (0.40, 62.0),
    (0.72, 63.0),
    (0.88, 60.5),
    (0.95, 55.0),
    (0.99, 50.0),
    (1.00, 47.0),
]
MOUND_HEIGHT = 54.0

GRAIN_LEN = 7.4
GRAIN_W = 2.7
GRAIN_H = 2.3
# The core must sit clearly inside the grain shell AND be darker than the
# grains. At a small inset its smooth silhouette pokes through the gaps and
# reads as a solid flange around the mound; darker and further in, the same
# peek-through reads as shadow between grains, which is what it should be.
CORE_INSET = 4.2


def _profile_radius(u):
    us = [p[0] for p in MOUND_PROFILE]
    rs = [p[1] for p in MOUND_PROFILE]
    return np.interp(u, us, rs)


def make_core(inset: float = CORE_INSET, height: float = MOUND_HEIGHT):
    """Smooth CAD mound that sits just inside the grain shell."""
    with BuildPart() as core:
        for u, r in MOUND_PROFILE:
            radius = max(r - inset, 0.6)
            with BuildSketch(Plane.XY.offset(u * (height - inset * 0.5))):
                Circle(radius)
        # ruled=True is essential here. The default smooth loft fits a spline
        # through the sections and, with four of them crammed into the top 12%
        # of the profile, it overshoots wildly - the core came out 151 mm across
        # instead of 118 and swallowed the grain shell.
        loft(ruled=True)
    return core.part


def uv_ellipsoid(rx, ry, rz, u_steps=8, v_steps=5):
    """A low-poly ellipsoid as raw arrays.

    Built directly rather than tessellated from CAD: a grain is instanced
    thousands of times, so its triangle count is the whole budget and it needs
    to be chosen, not inherited from a mesher.
    """
    verts = [(0.0, 0.0, rz)]
    for j in range(1, v_steps):
        phi = np.pi * j / v_steps
        for i in range(u_steps):
            theta = 2.0 * np.pi * i / u_steps
            verts.append((rx * np.sin(phi) * np.cos(theta),
                          ry * np.sin(phi) * np.sin(theta),
                          rz * np.cos(phi)))
    verts.append((0.0, 0.0, -rz))
    verts = np.array(verts, dtype=float)

    faces = []
    for i in range(u_steps):
        faces.append([0, 1 + i, 1 + (i + 1) % u_steps])
    for j in range(v_steps - 2):
        base = 1 + j * u_steps
        nxt = base + u_steps
        for i in range(u_steps):
            a, b = base + i, base + (i + 1) % u_steps
            c, d = nxt + i, nxt + (i + 1) % u_steps
            faces += [[a, c, b], [b, c, d]]
    last = 1 + (v_steps - 1) * u_steps
    tip = len(verts) - 1
    base = last - u_steps
    for i in range(u_steps):
        faces.append([tip, base + (i + 1) % u_steps, base + i])
    return verts, np.array(faces, dtype=np.int32)


def _surface_samples(count, seed, height=MOUND_HEIGHT):
    """Points and normals on the mound, area-weighted.

    The top is sampled as its own disc. Weighting height bands by circumference
    alone leaves the flat top bald, because the profile's radius stops changing
    there and the band weights collapse.
    """
    rng = np.random.default_rng(seed)

    top_radius = float(_profile_radius(1.0))
    top_area = np.pi * top_radius ** 2
    side_area = 2.0 * np.pi * float(np.mean(_profile_radius(np.linspace(0, 1, 64)))) * height
    n_top = int(round(count * top_area / max(top_area + side_area, 1e-9)))
    n_side = max(count - n_top, 0)

    # --- top disc ---
    r_top = top_radius * np.sqrt(rng.uniform(0.0, 1.0, n_top))
    th_top = rng.uniform(0.0, 2.0 * np.pi, n_top)
    pts_top = np.column_stack([r_top * np.cos(th_top), r_top * np.sin(th_top),
                               np.full(n_top, height)])
    n_vec_top = np.tile(np.array([0.0, 0.0, 1.0]), (n_top, 1))

    count = n_side

    # Weight each height band by its circumference so the sides do not end up
    # sparser than the top.
    us = np.linspace(0.02, 1.0, 400)
    radii = _profile_radius(us)
    weights = np.maximum(radii, 1e-6)
    weights = weights / weights.sum()
    picked = rng.choice(len(us), size=count, p=weights)
    u = np.clip(us[picked] + rng.normal(0.0, 0.006, count), 0.0, 1.0)

    r = _profile_radius(u)
    theta = rng.uniform(0.0, 2.0 * np.pi, count)

    # Surface normal from the profile slope: dr/du against dz/du.
    du = 1e-3
    dr = (_profile_radius(np.clip(u + du, 0, 1)) - _profile_radius(np.clip(u - du, 0, 1)))
    dz = 2.0 * du * height
    slope = np.arctan2(-dr, dz)          # tilt of the normal away from radial

    nx = np.cos(theta) * np.cos(slope)
    ny = np.sin(theta) * np.cos(slope)
    nz = np.sin(slope)

    # The very top is a cap, not a wall: blend the normal to vertical.
    cap = np.clip((u - 0.93) / 0.07, 0.0, 1.0)
    nz = nz * (1 - cap) + cap
    nx *= (1 - cap * 0.85)
    ny *= (1 - cap * 0.85)

    normals = np.column_stack([nx, ny, nz])
    normals /= np.linalg.norm(normals, axis=1, keepdims=True)

    pts = np.column_stack([r * np.cos(theta), r * np.sin(theta), u * height])

    pts = np.vstack([pts, pts_top])
    normals = np.vstack([normals, n_vec_top])
    return pts, normals, rng


def grain_shell(count=4200, seed=3, height=MOUND_HEIGHT):
    """Instanced grains covering the mound. Returns (verts, faces)."""
    base_v, base_f = uv_ellipsoid(GRAIN_LEN / 2.0, GRAIN_W / 2.0, GRAIN_H / 2.0)
    pts, normals, rng = _surface_samples(count, seed, height)

    placements = []
    for i in range(len(pts)):
        rot = frame_from_normal(normals[i], rng=rng)
        # Sit each grain slightly proud so it stands off the core.
        offset = pts[i] + normals[i] * (GRAIN_H * 0.30)
        scale = rng.uniform(0.82, 1.18, 3) * np.array([1.0, 1.0, 1.0])
        placements.append((rot, offset, scale))

    return instance(base_v, base_f, placements)


def crown_bits(count=520, seed=9, radius=44.0, height=MOUND_HEIGHT,
               size=(2.6, 1.5, 1.1)):
    """Chopped spring onion scattered over the crown."""
    rng = np.random.default_rng(seed)
    base_v, base_f = uv_ellipsoid(*size, u_steps=6, v_steps=4)

    r = radius * np.sqrt(rng.uniform(0.0, 1.0, count))
    theta = rng.uniform(0.0, 2.0 * np.pi, count)
    u = 1.0 - (r / max(radius, 1e-6)) ** 2 * 0.10

    placements = []
    for i in range(count):
        n = np.array([0.0, 0.0, 1.0])
        rot = frame_from_normal(n, rng=rng)
        pos = np.array([r[i] * np.cos(theta[i]), r[i] * np.sin(theta[i]),
                        u[i] * height + 1.6])
        placements.append((rot, pos, rng.uniform(0.75, 1.3)))
    return instance(base_v, base_f, placements)
