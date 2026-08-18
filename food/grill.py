"""Grilled elements: charred chicken thighs and corn cob rounds.

The corn uses the same instancing route as the rice, for the same reason: the
brief asks for *defined individual kernels in rows*, and displacement can only
push a cylinder around - it cannot make a surface into separate kernels. So a
cob core carries the mass and kernels are instanced onto it in a staggered
lattice, which is how they actually grow.

The chicken is the displacement route: it IS one continuous surface, just a
very irregular one, so ridged noise and char colouring do the work.

Units are millimetres, Z up.
"""

from __future__ import annotations

import numpy as np
from build123d import (
    Align,
    Box,
    BuildPart,
    BuildSketch,
    Circle,
    Ellipse,
    Locations,
    Plane,
    Pos,
    Rot,
    loft,
)

from mesh_kit import frame_from_normal, instance
from rice import uv_ellipsoid

# --------------------------------------------------------------------------
# corn cob rounds
# --------------------------------------------------------------------------

COB_RADIUS = 21.0
COB_LENGTH = 30.0
KERNEL_ROWS = 18          # around the circumference
KERNEL_COLS = 7           # along the axis
KERNEL = (4.4, 3.6, 2.8)  # along cob, around cob, radial


def make_cob_core(radius=COB_RADIUS, length=COB_LENGTH, inset=1.6):
    """The cob itself: a plain cylinder just inside the kernel layer."""
    with BuildPart() as core:
        with BuildSketch(Plane.YZ):
            Circle(radius - inset)
        from build123d import extrude
        extrude(amount=length)
    box = core.part.bounding_box()
    return Pos(-box.center().X, -box.center().Y, -box.center().Z) * core.part


def kernel_shell(radius=COB_RADIUS, length=COB_LENGTH, rows=KERNEL_ROWS,
                 cols=KERNEL_COLS, seed=5):
    """Kernels in a staggered lattice around the cob, running along X."""
    rng = np.random.default_rng(seed)
    base_v, base_f = uv_ellipsoid(*KERNEL, u_steps=8, v_steps=5)

    placements = []
    for c in range(cols):
        x = (c + 0.5) / cols * length - length / 2.0
        # Alternate rows are offset by half a step - corn kernels are packed in
        # a staggered lattice, not a square grid.
        stagger = 0.5 * (c % 2)
        for r in range(rows):
            theta = 2.0 * np.pi * (r + stagger) / rows
            normal = np.array([0.0, np.cos(theta), np.sin(theta)])
            pos = np.array([x, 0.0, 0.0]) + normal * (radius - KERNEL[2] * 0.45)
            rot = frame_from_normal(normal, tangent_hint=(1.0, 0.0, 0.0))
            jitter = rng.uniform(0.90, 1.10, 3)
            placements.append((rot, pos, jitter))

    return instance(base_v, base_f, placements)


# --------------------------------------------------------------------------
# charred chicken thighs
# --------------------------------------------------------------------------

# Flatter and wider than the fried chicken in the meal box: a grilled thigh
# spreads out rather than staying plump.
THIGH_SECTIONS = [
    (0.00, 10.0,  4.0,  0.0),
    (0.14, 24.0,  9.0,  1.5),
    (0.34, 33.0, 13.0,  2.5),
    (0.55, 35.0, 14.5,  1.0),
    (0.74, 31.0, 13.0, -1.5),
    (0.90, 22.0,  9.5, -3.0),
    (1.00, 11.0,  4.5, -3.5),
]

THIGH_LENGTH = 108.0


def make_thigh(length=THIGH_LENGTH, sections=THIGH_SECTIONS, flatten=2.6):
    with BuildPart() as core:
        for frac, half_w, half_h, lean in sections:
            with BuildSketch(Plane.XY.offset(frac * length)):
                with Locations((lean, 0.0)):
                    Ellipse(half_w, half_h)
        loft(ruled=True)

    piece = Rot(90.0, 0.0, 0.0) * (Rot(0.0, 90.0, 0.0) * core.part)
    box = piece.bounding_box()
    knife = Box(4000.0, 2000.0, 900.0, align=(Align.CENTER, Align.CENTER, Align.MAX))
    piece = piece - Pos(0.0, 0.0, box.min.Z + flatten) * knife
    box = piece.bounding_box()
    return Pos(-box.center().X, -box.center().Y, -box.min.Z) * piece


def char_skin(verts, faces, seed=21, blister=3.1, blister_freq=0.26,
              grill=1.7, grill_freq=0.070, fine=0.55, fine_freq=0.85):
    """Blistered, grill-marked skin.

    Three scales: ridged blistering for the bubbled crisp skin, a low-frequency
    banding across the piece for grill bars, and a fine crisping pass. All are
    masked to the upward face - the underside sat on the grill and stays flat.
    """
    from mesh_kit import ridged, roughen, vertex_normals

    n = vertex_normals(verts, faces)
    up = np.clip(n[:, 2], 0.0, 1.0)

    r = ridged(verts, octaves=3, frequency=blister_freq, seed=seed, sharpness=2.4)
    v = verts + n * ((r - 0.42) * blister * up)[:, None]

    # Grill bars: bands ACROSS the piece, so the field varies quickly along X.
    v = roughen(v, faces, amplitude=grill, frequency=grill_freq, octaves=2,
                seed=seed + 51, bias=0.0, axis_scale=(1.0, 0.12, 0.12), mask=up)
    v = roughen(v, faces, amplitude=fine, frequency=fine_freq, octaves=2,
                seed=seed + 133, bias=0.0, mask=up)
    return v
