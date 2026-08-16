"""Fried chicken pieces — lofted CAD cores.

Only the *form* lives here: a stack of ellipses lofted along the piece's
length, which build123d does exactly and quickly. The craggy breading is NOT
modelled as CAD.

That is deliberate. Fusing hundreds of spheres onto the core to fake breading
either takes minutes or makes OCCT return a null shape once the boolean
arguments pile up - both were tried. Surface detail of this kind belongs in the
mesh domain, so the crust is applied by `mesh_kit.roughen()` at export time.
The STEP files therefore contain the smooth core; the GLB contains the crust.

Units are millimetres. Each piece is returned lying along X, centred in XY and
resting on Z=0.
"""

from __future__ import annotations

from build123d import (
    BuildPart,
    BuildSketch,
    Ellipse,
    Locations,
    Plane,
    Pos,
    Rot,
    loft,
)

from cadpy.assembly import label_shape

# Section stack along the piece's length:
#   (length fraction, cross-section half-width, half-height, lean x, lean y)
THIGH_SECTIONS = [
    (0.00, 12.0, 10.0,  0.0,  0.0),
    (0.14, 25.0, 21.0,  1.5,  0.8),
    (0.34, 33.0, 27.0,  2.5,  0.0),
    (0.55, 34.0, 27.0,  1.0, -1.0),
    (0.75, 28.0, 22.0, -1.5, -1.5),
    (0.90, 19.0, 15.0, -3.0, -1.0),
    (1.00,  9.0,  7.0, -4.0,  0.0),
]

TENDER_SECTIONS = [
    (0.00,  8.0,  6.5,  0.0,  0.0),
    (0.20, 16.0, 12.5,  1.0,  0.5),
    (0.45, 19.0, 14.5,  1.5,  0.0),
    (0.70, 17.0, 13.0,  0.5, -0.8),
    (0.88, 12.0,  9.0, -1.0, -1.0),
    (1.00,  6.0,  4.5, -2.0, -0.5),
]

WING_SECTIONS = [
    (0.00,  7.0,  6.0,  0.0,  0.0),
    (0.22, 14.0, 12.0,  1.0,  1.0),
    (0.50, 17.5, 14.0,  2.0,  0.0),
    (0.76, 14.0, 11.0,  1.0, -1.0),
    (1.00,  7.5,  6.0, -1.0, -1.0),
]


def _interp(sections, t):
    """Linear interpolation through the section stack at length fraction t."""
    for i in range(len(sections) - 1):
        t0, *a = sections[i]
        t1, *b = sections[i + 1]
        if t0 <= t <= t1:
            f = 0.0 if t1 == t0 else (t - t0) / (t1 - t0)
            return [a[k] + (b[k] - a[k]) * f for k in range(4)]
    return list(sections[-1][1:])




def make_piece(
    sections=THIGH_SECTIONS,
    length: float = 118.0,
    seed: int = 1,
):
    """Return one smooth chicken core, lying along X and resting on Z=0."""
    with BuildPart() as core:
        for frac, rx, ry, dx, dy in sections:
            with BuildSketch(Plane.XY.offset(frac * length)):
                with Locations((dx, dy)):
                    Ellipse(rx, ry)
        loft()

    # Lay it down: the loft runs along Z, the piece should run along X.
    piece = Rot(0, 90, 0) * core.part
    box = piece.bounding_box()
    return Pos(-box.center().X, -box.center().Y, -box.min.Z) * piece


def make_thigh(seed: int = 1):
    return make_piece(THIGH_SECTIONS, 118.0, seed)


def make_tender(seed: int = 7):
    return make_piece(TENDER_SECTIONS, 92.0, seed)


def make_wing(seed: int = 13):
    return make_piece(WING_SECTIONS, 74.0, seed)


def gen_step():
    return label_shape(make_thigh(), "chicken_thigh")


if __name__ == "__main__":
    gen_step()
