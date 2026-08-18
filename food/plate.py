"""Restaurant plate — a revolved coupe profile.

This one is pure CAD and it is the case a B-rep kernel is genuinely best at: a
plate is a surface of revolution, so the whole thing is one closed profile spun
about Z. No displacement is applied to it at all - glazed porcelain really is
that smooth, and any noise would only make it look worse.

Units are millimetres, Z up, resting on Z=0, centred on the origin.
"""

from __future__ import annotations

from build123d import (
    Axis,
    BuildLine,
    BuildPart,
    BuildSketch,
    Line,
    Plane,
    Polyline,
    Spline,
    make_face,
    revolve,
)

PLATE_DIA = 280.0
RIM_HEIGHT = 24.0
WELL_DEPTH = 6.0
FOOT_DIA = 104.0
FOOT_HEIGHT = 4.0


def make_plate():
    r_out = PLATE_DIA / 2.0
    r_foot = FOOT_DIA / 2.0

    with BuildPart() as plate:
        with BuildSketch(Plane.XZ) as profile:
            with BuildLine() as outline:
                # Upper surface: flat well sweeping up into the rim.
                top = Spline(
                    (0.0, WELL_DEPTH),
                    (46.0, WELL_DEPTH + 0.4),
                    (86.0, WELL_DEPTH + 2.6),
                    (114.0, WELL_DEPTH + 9.0),
                    (132.0, RIM_HEIGHT - 1.5),
                    (r_out, RIM_HEIGHT),
                )
                # Underside back to the axis, over the foot ring. Every station
                # must stay clearly BELOW the top curve - an underside that
                # crosses it splits the profile into two loops and the revolve
                # then produces a stunted plate rather than failing outright.
                under = Polyline(
                    (r_out, RIM_HEIGHT),
                    (r_out, RIM_HEIGHT - 5.2),      # visible edge thickness
                    (137.0, RIM_HEIGHT - 6.4),
                    (132.0, 16.0),
                    (114.0, 9.4),
                    (95.0, 5.2),
                    (70.0, 3.2),
                    (r_foot + 5.0, 2.8),
                    (r_foot, 2.8),
                    (r_foot, 0.0),
                    (r_foot - 9.0, 0.0),
                    (r_foot - 9.0, 2.8),
                    (34.0, 3.0),
                    (0.0, 3.2),
                )
                Line(under @ 1, top @ 0)

            wires = outline.line.wires()
            if len(wires) != 1 or not wires[0].is_closed:
                raise ValueError(
                    f"plate profile made {len(wires)} wire(s); the underside "
                    "probably crosses the top surface"
                )
            make_face()
        revolve(axis=Axis.Z)

    return plate.part


def gen_step():
    from cadpy.assembly import label_shape

    return label_shape(make_plate(), "plate")


if __name__ == "__main__":
    gen_step()
