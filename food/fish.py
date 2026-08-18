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
FILLET_SECTIONS = [
    (0.00,  5.0,  2.2,  0.0),   # tail tip
    (0.10, 13.0,  5.4,  1.5),
    (0.26, 22.0,  9.6,  2.5),
    (0.44, 27.5, 11.8,  1.5),
    (0.62, 29.0, 12.2, -0.5),
    (0.80, 26.0, 10.6, -2.0),
    (0.92, 19.0,  7.4, -2.5),
    (1.00, 10.0,  4.0, -2.0),
]

FILLET_LENGTH = 178.0
UNDERCUT = 3.2          # how much of the rounded underside is sliced flat


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


def sear(verts, faces, seed=11, grain=2.2, grain_freq=0.10,
         mottle=1.1, mottle_freq=0.30, crisp=0.45, crisp_freq=0.72,
         seam_depth=3.8, seam_width=8.0):
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
