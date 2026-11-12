"""End rail for a horizontal PS5 Slim stand (one of a mirrored pair).

Coordinate convention
    Origin : centre of the stand footprint, on the desk surface
    X      : the console's long axis (358 mm)
    Y      : the console's depth axis (216 mm)
    +Z     : up

Design intent
    The console lies flat, long axis along X. Two rails sit under its two ends,
    lifting it off the desk so the underside breathes, and a pair of retaining
    tabs on each rail stop it sliding off along X. The tabs are short and sit at
    the front and back only, so the middle of each end face - where the vents
    are - stays open.

Dimensions
    Console (Sony published, both editions share width and depth):
        358 W x 216 D x 96 H  (Disc)      358 x 216 x 80 (Digital)
    The cradle only touches the ends, so height does not matter for fit and the
    same rails serve both editions.

    This is the +X rail; the -X rail is its mirror image (see ps5_slim_stand.py).
"""

from build123d import (
    Align,
    Axis,
    Box,
    BuildPart,
    BuildSketch,
    Circle,
    Locations,
    Mode,
    Plane,
    chamfer,
    extrude,
)

from cadpy.assembly import label_shape

# --- Console envelope (published) -------------------------------------------
console_w = 358.0   # long axis, X
console_d = 216.0   # depth, Y
console_h = 96.0    # disc edition; digital is 80

# --- Fit --------------------------------------------------------------------
fit_clear = 1.5     # per end, console to tab inner face

# --- Rail -------------------------------------------------------------------
rail_len = 236.0    # Y; 10 mm longer than the console each side, and under a
                    # 256 mm print bed
rail_w = 40.0       # X, support under the console end
rail_h = 14.0       # lifts the console off the desk

# --- Retaining tabs ---------------------------------------------------------
tab_t = 3.5         # X thickness
tab_h = 16.0        # above the rail top
tab_len = 60.0      # Y length of each tab, at the two rail ends

# --- Underside feet pockets (stick-on rubber pads) --------------------------
foot_d = 12.0
foot_depth = 1.5
foot_y = 85.0

edge_chamfer = 1.0
cut_overshoot = 1.0

inner_x = console_w / 2.0 + fit_clear     # tab inner face
outer_x = inner_x + tab_t                 # tab outer face
rail_x0 = inner_x - rail_w                # rail inner edge


def make_rail():
    with BuildPart() as rail:
        # Rail bar, from its inner edge out to the tab's outer face.
        with Locations((rail_x0, 0.0, 0.0)):
            Box(
                outer_x - rail_x0,
                rail_len,
                rail_h,
                align=(Align.MIN, Align.CENTER, Align.MIN),
            )

        # Retaining tabs at the two Y ends. They start inside the bar by 1 mm so
        # the fuse is not a face-coincident one.
        for sign in (-1.0, 1.0):
            y0 = sign * (rail_len / 2.0 - tab_len / 2.0)
            with Locations((inner_x, y0, rail_h - 1.0)):
                Box(
                    tab_t,
                    tab_len,
                    tab_h + 1.0,
                    align=(Align.MIN, Align.CENTER, Align.MIN),
                )

        # Rubber-foot pockets in the underside.
        foot_x = rail_x0 + (outer_x - rail_x0) / 2.0
        with BuildSketch(Plane.XY.offset(-cut_overshoot)):
            with Locations(*[(foot_x, sy * foot_y) for sy in (-1.0, 1.0)]):
                Circle(foot_d / 2.0)
        extrude(amount=cut_overshoot + foot_depth, mode=Mode.SUBTRACT)

        # Soften the outside corners of the bar.
        vertical = rail.edges().filter_by_position(
            Axis.X, outer_x - 0.01, outer_x + 0.01
        )
        chamfer(vertical.filter_by(Axis.Z), edge_chamfer)

    return rail.part


def gen_step():
    return label_shape(make_rail(), "ps5_slim_rail")


if __name__ == "__main__":
    gen_step()
