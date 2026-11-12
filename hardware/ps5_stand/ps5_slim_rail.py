"""Sculpted, adjustable end rail for a horizontal PS5 stand - print two, identical.

Each rail carries one telescoping bar and one sleeve. Turn one rail 180 deg
about Z and each bar slides into the other rail's sleeve, so one part serves as
both sides and the pair expands like a curtain rod.

Coordinate convention (rail local frame)
    Origin : centre of the rail's INNER edge, on the desk surface
    +X     : outward, towards the console end (wall side)
    -X     : inward, bar and sleeve extend this way
    Y      : console depth axis
    +Z     : up

Form
    A low seat carries the console end. A single retaining wall sweeps along the
    outer edge: it rises to a high crest at the front and back and dips low in
    the middle, so it reads as one flowing curve rather than two tabs, and the
    middle of the end face stays open for the vents. The wall's inner face leans
    outward by 5 deg (the console drops straight in, nothing undercuts), its top edge
    is fully rounded, the plan corners are generously radiused and the underside
    is softened so the rail looks lifted off the desk.

Dimensions
    Console (Sony published, both Slim editions): 358 W x 216 D x 96 / 80 H.
    Adjustment range, wall face to wall face: 340 - 400 mm, covering the PS5
    Slim (358) and the original PS5 (390).
"""

from math import radians, tan

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
    Polygon,
    Pos,
    Rot,
    extrude,
    fillet,
)

from cadpy.assembly import label_shape

# --- Console envelope (published) -------------------------------------------
console_w = 358.0
console_d = 216.0
console_h = 96.0

# --- Fit --------------------------------------------------------------------
fit_clear = 1.5     # per end, console to wall inner face at the seat
gap_min = 340.0     # wall face to wall face, fully closed
gap_max = 400.0     # fully extended

# --- Seat and wall ----------------------------------------------------------
rail_len = 236.0    # Y; under a 256 mm print bed
rail_w = 40.0       # X, support under the console end (inner edge to wall face)
rail_h = 15.0       # seat height: lifts the console off the desk
base_t = 5.0        # wall thickness at the seat
wall_lean_in = 5.0  # deg, inner face leans outward as it rises
crest_h = 36.0      # wall top at the front and back ends
dip_h = 19.0        # wall top at the middle
plan_r_outer = 20.0 # plan corner radius, wall side
plan_r_inner = 8.0  # plan corner radius, bar side
top_round = 1.3     # fillet on the wall's top edges
under_round = 3.0   # fillet on the underside perimeter

# --- Telescoping bar / sleeve ----------------------------------------------
bar_y = 60.0
bar_w = 12.0
bar_h = 7.0
slide_clear = 0.35  # per side, printed fit - snug but free
sleeve_wall = 2.0
lock_wall = 6.5     # thick side wall that holds the lock insert
bar_len = 200.0
sleeve_len = 170.0
bar_round = 1.5
sleeve_round = 2.0

# M4 heat-set insert (5.6 mm x 5.7 mm) in the lock wall + M4 thumbscrew
lock_hole_d = 5.6
lock_from_mouth = 14.0

# --- Underside feet pockets (stick-on rubber pads) --------------------------
foot_d = 12.0
foot_depth = 1.5
foot_y = 85.0

cut_overshoot = 1.0

# --- Derived ----------------------------------------------------------------
cav_w = bar_w + 2.0 * slide_clear
cav_h = bar_h + 2.0 * slide_clear
sleeve_h = cav_h + 2.0 * sleeve_wall
mid_z = sleeve_h / 2.0
cav_y0 = bar_y - cav_w / 2.0

crest_y = rail_len / 2.0 - 10.0              # where the swoop reaches crest_h; the
                                             # rounded plan corner leaves no wall
                                             # beyond about this
# The extrusion is taller than the crest so the swoop alone shapes the wall top.
profile_h = crest_h + 8.0
x_in_top = rail_w + (profile_h - rail_h) * tan(radians(wall_lean_in))
# The outer face is vertical and the plan prism ends exactly on it, so the plan
# corner arcs meet it tangentially. A leaning outer face leaves a kink there that
# the underside fillet cannot run through.
x_out = rail_w + base_t
x_max = x_out

# The sleeve must stay clear of the console underside.
assert sleeve_h < rail_h - 2.0
min_engagement = bar_len + sleeve_len - (gap_max - 2.0 * rail_w)
assert min_engagement >= 40.0, min_engagement
assert bar_len + sleeve_len - (gap_min - 2.0 * rail_w) <= sleeve_len


def _wall_extrusion():
    """Seat + leaning wall as one XZ profile, extruded along Y."""
    pts = [
        (0.0, 0.0),
        (x_out, 0.0),
        (x_out, profile_h),
        (x_in_top, profile_h),
        (rail_w, rail_h),
        (0.0, rail_h),
    ]
    with BuildPart() as p:
        with BuildSketch(Plane.XZ):
            Polygon(*pts, align=None)
        extrude(amount=rail_len / 2.0, both=True)
    return p.part


def _plan_prism():
    """Rounded-rectangle prism that gives the rail its plan-view outline."""
    with BuildPart() as p:
        Box(x_max, rail_len, 3.0 * profile_h,
            align=(Align.MIN, Align.CENTER, Align.CENTER))
        verticals = p.edges().filter_by(Axis.Z)
        fillet(verticals.filter_by_position(Axis.X, x_max - 0.01, x_max + 0.01),
               plan_r_outer)
        fillet(verticals.filter_by_position(Axis.X, -0.01, 0.01), plan_r_inner)
    return p.part


def _swoop_tool():
    """Big cylinder, axis along X, whose underside carves the wall's dip."""
    h = crest_h - dip_h
    radius = (crest_y ** 2 + h ** 2) / (2.0 * h)
    centre_z = dip_h + radius
    return Pos(x_max / 2.0, 0.0, centre_z) * Rot(0.0, 90.0, 0.0) * \
        Cylinder(radius, x_max + 20.0)


def _bar():
    with BuildPart() as p:
        with Locations((1.0, -bar_y, mid_z)):
            Box(bar_len + 1.0, bar_w, bar_h,
                align=(Align.MAX, Align.CENTER, Align.CENTER))
        fillet(p.edges().filter_by(Axis.X), bar_round)
    return p.part


def _sleeve():
    y0 = cav_y0 - lock_wall
    y1 = bar_y + cav_w / 2.0 + sleeve_wall
    with BuildPart() as p:
        with Locations((1.0, (y0 + y1) / 2.0, 0.0)):
            Box(sleeve_len + 1.0, y1 - y0, sleeve_h,
                align=(Align.MAX, Align.CENTER, Align.MIN))
        fillet(p.edges().filter_by(Axis.X), sleeve_round)
        # Bore: open at the mouth, blind at the rail face (x=0).
        with Locations((0.0, bar_y, sleeve_wall)):
            Box(sleeve_len + cut_overshoot, cav_w, cav_h,
                align=(Align.MAX, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
    return p.part


def _lock_tool():
    hole_len = lock_wall + 2.0 * cut_overshoot
    wall_mid_y = cav_y0 - lock_wall / 2.0
    return Pos(-sleeve_len + lock_from_mouth, wall_mid_y, mid_z) * \
        Rot(90.0, 0.0, 0.0) * Cylinder(lock_hole_d / 2.0, hole_len)


def _foot_tool():
    with BuildPart() as p:
        with BuildSketch(Plane.XY.offset(-cut_overshoot)):
            with Locations(*[(rail_w / 2.0, sy * foot_y) for sy in (-1.0, 1.0)]):
                Circle(foot_d / 2.0)
        extrude(amount=cut_overshoot + foot_depth)
    return p.part


def make_rail():
    body = _wall_extrusion() & _plan_prism()
    body = body - _swoop_tool()

    # Round the wall's top edges: the swoop face is the long cylindrical face.
    swoop = [f for f in body.faces()
             if f.geom_type.name == "CYLINDER" and f.bounding_box().size.Y > 0.9 * rail_len]
    assert len(swoop) == 1, len(swoop)
    body = body.fillet(top_round, list(swoop[0].edges()))

    # Soften the underside so the rail looks lifted.
    bottom = body.edges().filter_by_position(Axis.Z, -0.01, 0.01)
    body = body.fillet(under_round, list(bottom))

    body = body + _bar() + _sleeve()
    body = body - _lock_tool() - _foot_tool()

    bb = body.bounding_box()
    assert abs(bb.min.Z) < 1e-6 and abs(bb.max.Z - crest_h) < 2.0, bb
    assert len(body.solids()) == 1
    return body


def gen_step():
    return label_shape(make_rail(), "ps5_adjustable_rail")


if __name__ == "__main__":
    gen_step()
