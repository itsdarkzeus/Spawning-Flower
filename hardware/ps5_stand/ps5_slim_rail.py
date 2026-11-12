"""Adjustable end rail for a horizontal PS5 stand - print two, identical.

Each rail carries one telescoping bar and one sleeve. Rotate one rail 180 deg
about Z and the bar on each slides into the sleeve on the other, so the pair
expands and contracts like a curtain rod and a single part serves as both sides.

Coordinate convention (rail local frame)
    Origin : centre of the rail's INNER edge, on the desk surface
    +X     : outward, towards the console end (tab side)
    -X     : inward, bar and sleeve extend this way
    Y      : console depth axis
    +Z     : up

Design intent
    The console lies flat on two rails under its ends, lifted off the desk. A
    short retaining tab at each rail's front and back stops it sliding off
    along its length; the middle of the end face stays open for vents.
    The bar and sleeve live BELOW the console underside (2.5 mm gap) and carry
    no weight - the rails do. Set the width with the console off, tighten the
    thumbscrews, then lower the console on.

Dimensions
    Console (Sony published, both Slim editions): 358 W x 216 D x 96 / 80 H.
    Adjustment range, tab face to tab face: 340 - 400 mm, which covers the
    PS5 Slim (358) and the original PS5 (390).
"""

from build123d import (
    Align,
    Axis,
    Box,
    BuildPart,
    BuildSketch,
    Circle,
    Cylinder,
    Locations,
    Mode,
    Plane,
    Pos,
    Rot,
    add,
    chamfer,
    extrude,
)

from cadpy.assembly import label_shape

# --- Console envelope (published) -------------------------------------------
console_w = 358.0
console_d = 216.0
console_h = 96.0

# --- Fit --------------------------------------------------------------------
fit_clear = 1.5     # per end, console to tab inner face
gap_min = 340.0     # tab face to tab face, fully closed
gap_max = 400.0     # fully extended

# --- Rail -------------------------------------------------------------------
rail_len = 236.0    # Y; under a 256 mm print bed
rail_w = 40.0       # X, support under the console end
rail_h = 16.0       # lifts the console off the desk

# --- Retaining tabs ---------------------------------------------------------
tab_t = 3.5
tab_h = 16.0
tab_len = 60.0

# --- Telescoping bar / sleeve ----------------------------------------------
bar_y = 60.0        # bar and sleeve sit at +/- this Y; clear of the foot pockets
bar_w = 12.0        # Y
bar_h = 8.0         # Z
slide_clear = 0.35  # per side, printed fit - snug but free
sleeve_wall = 2.4
lock_wall = 6.5     # thick side wall that holds the lock insert
bar_len = 200.0
sleeve_len = 170.0

# M4 heat-set insert (5.6 mm x 5.7 mm) in the lock wall + M4 thumbscrew
lock_hole_d = 5.6
lock_from_mouth = 14.0

# --- Underside feet pockets (stick-on rubber pads) --------------------------
foot_d = 12.0
foot_depth = 1.5
foot_y = 85.0

edge_chamfer = 1.0
cut_overshoot = 1.0

# --- Derived ----------------------------------------------------------------
tab_outer_x = rail_w + tab_t
cav_w = bar_w + 2.0 * slide_clear
cav_h = bar_h + 2.0 * slide_clear
sleeve_h = cav_h + 2.0 * sleeve_wall            # 13.5, under the console
mid_z = sleeve_h / 2.0                          # bar centre height
cav_y0 = bar_y - cav_w / 2.0                    # cavity edge nearest Y=0

# The sleeve must not touch the console underside.
assert sleeve_h < rail_h - 1.0

# Engagement at full extension has to stay generous, or the joint flops.
min_engagement = bar_len + sleeve_len - (gap_max - 2.0 * rail_w)
assert min_engagement >= 40.0, min_engagement
# And the bar must not bottom out in the sleeve when closed.
assert bar_len + sleeve_len - (gap_min - 2.0 * rail_w) <= sleeve_len


def _lock_tool():
    """Cutter for the insert hole. Built OUTSIDE any BuildPart: a primitive made
    inside one is added to the part immediately, at the origin, before the
    transform is applied."""
    hole_len = lock_wall + 2.0 * cut_overshoot
    wall_mid_y = cav_y0 - lock_wall / 2.0
    return Pos(-sleeve_len + lock_from_mouth, wall_mid_y, mid_z) * \
        Rot(90.0, 0.0, 0.0) * Cylinder(lock_hole_d / 2.0, hole_len)


def make_rail():
    lock_tool = _lock_tool()
    with BuildPart() as rail:
        # Rail bar: from the inner edge (x=0) out to the tab's outer face.
        with Locations((0.0, 0.0, 0.0)):
            Box(tab_outer_x, rail_len, rail_h,
                align=(Align.MIN, Align.CENTER, Align.MIN))

        # Retaining tabs at the two Y ends. Start 1 mm inside the bar so the
        # fuse is not a face-coincident one.
        for sign in (-1.0, 1.0):
            y0 = sign * (rail_len / 2.0 - tab_len / 2.0)
            with Locations((rail_w, y0, rail_h - 1.0)):
                Box(tab_t, tab_len, tab_h + 1.0,
                    align=(Align.MIN, Align.CENTER, Align.MIN))

        # Telescoping bar at -Y, reaching inward. Starts 1 mm inside the rail.
        with Locations((1.0, -bar_y, mid_z - bar_h / 2.0)):
            Box(bar_len + 1.0, bar_w, bar_h,
                align=(Align.MAX, Align.CENTER, Align.MIN))

        # Sleeve at +Y, with a thick wall on the side facing Y=0 for the lock.
        sleeve_y0 = cav_y0 - lock_wall
        sleeve_y1 = bar_y + cav_w / 2.0 + sleeve_wall
        with Locations((1.0, (sleeve_y0 + sleeve_y1) / 2.0, 0.0)):
            Box(sleeve_len + 1.0, sleeve_y1 - sleeve_y0, sleeve_h,
                align=(Align.MAX, Align.CENTER, Align.MIN))

        # Sleeve bore: open at the mouth, blind at the rail face (x=0).
        with Locations((0.0, bar_y, sleeve_wall)):
            Box(sleeve_len + cut_overshoot, cav_w, cav_h,
                align=(Align.MAX, Align.CENTER, Align.MIN),
                mode=Mode.SUBTRACT)

        # Lock insert hole, through the thick wall into the bore.
        add(lock_tool, mode=Mode.SUBTRACT)

        # Rubber-foot pockets in the underside of the rail.
        with BuildSketch(Plane.XY.offset(-cut_overshoot)):
            with Locations(*[(rail_w / 2.0, sy * foot_y) for sy in (-1.0, 1.0)]):
                Circle(foot_d / 2.0)
        extrude(amount=cut_overshoot + foot_depth, mode=Mode.SUBTRACT)

        # Soften the outside vertical corners.
        outer = rail.edges().filter_by_position(
            Axis.X, tab_outer_x - 0.01, tab_outer_x + 0.01)
        chamfer(outer.filter_by(Axis.Z), edge_chamfer)

    part = rail.part
    bb = part.bounding_box()
    assert abs(bb.min.Z) < 1e-6 and abs(bb.max.Z - (rail_h + tab_h)) < 1e-6, bb
    assert len(part.solids()) == 1
    return part


def gen_step():
    return label_shape(make_rail(), "ps5_adjustable_rail")


if __name__ == "__main__":
    gen_step()
