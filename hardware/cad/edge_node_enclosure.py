"""Building edge-node enclosure: Raspberry Pi sync agent + UPS/battery board.

Part of the attendance system hardware set (see hardware/cad/README.md).

One of these sits per building. It runs the ISAPI sync agent and the local
SQLite queue, so attendance keeps flowing while the campus link is down.

Coordinate convention
    Origin : centre of the outside face of the enclosure floor
    XY     : floor plane (X = long axis, Y = short axis)
    +Z     : up, out of the open face

    Wall-mounted with the floor against the wall and the lid facing the room,
    so the cable glands sit on the lower -Y wall and drain downwards.

Assembly
    base : floor, walls, lid bosses, board standoffs, wall-mount ears
    lid  : cover plate with a spigot lip and corner reliefs for the bosses

Board mounting
    Standoffs follow the Raspberry Pi mechanical pattern of 58 x 49 mm, which
    is common to the Pi 4B and Pi 5. A catalog Pi 5 STEP is downloaded to
    vendor/raspberry_pi_5.step if you want to run your own fit check; it is
    deliberately NOT fused into this assembly, so nothing here should be read
    as a verified board-level fit.
"""

from build123d import (
    Align,
    Box,
    BuildPart,
    BuildSketch,
    Circle,
    Cylinder,
    Location,
    Locations,
    Mode,
    Plane,
    Rectangle,
    extrude,
)

from cadpy.assembly import AssemblyHelper

# --- Cavity -----------------------------------------------------------------
inner_l = 120.0
inner_w = 90.0
inner_h = 55.0

wall_t = 2.5
floor_t = 3.0

outer_l = inner_l + 2.0 * wall_t   # 125
outer_w = inner_w + 2.0 * wall_t   # 95
outer_h = floor_t + inner_h        # 58

# --- Lid --------------------------------------------------------------------
lid_t = 3.0
lip_h = 2.0
lip_t = 2.0
lip_clear = 0.4                    # total, so 0.2 per side into the cavity

# --- Lid fixing bosses ------------------------------------------------------
boss_d = 8.0
boss_pilot_d = 2.5                 # M3 thread-forming into plastic
boss_pilot_depth = 14.0
lid_screw_d = 3.4                  # M3 clearance
boss_relief_d = boss_d + 0.6

# --- Board standoffs (Raspberry Pi 58 x 49 pattern) -------------------------
board_hole_dx = 58.0
board_hole_dy = 49.0
standoff_d = 6.0
standoff_h = 6.0
standoff_pilot_d = 2.1             # M2.5 thread-forming
standoff_pilot_depth = 5.5

# --- Wall-mount ears --------------------------------------------------------
ear_l = 26.0
ear_w = 40.0
ear_t = 4.0
ear_overlap = 2.0
ear_hole_d = 5.5

# --- Cable glands (M16) on the -Y wall --------------------------------------
gland_d = 16.5
gland_dx = 34.0
gland_z = 22.0

# --- Ventilation slots on the +Y wall ---------------------------------------
vent_l = 40.0
vent_h = 3.0
vent_levels = (28.0, 34.0, 40.0, 46.0, 52.0)

cut_overshoot = 1.0


def _boss_points() -> list[tuple[float, float]]:
    """Lid boss centres, tucked into the four inside corners."""
    x = inner_l / 2.0 - boss_d / 2.0
    y = inner_w / 2.0 - boss_d / 2.0
    return [(sx * x, sy * y) for sx in (-1.0, 1.0) for sy in (-1.0, 1.0)]


def _standoff_points() -> list[tuple[float, float]]:
    return [
        (sx * board_hole_dx / 2.0, sy * board_hole_dy / 2.0)
        for sx in (-1.0, 1.0)
        for sy in (-1.0, 1.0)
    ]


def make_base():
    with BuildPart() as base:
        # Shell
        Box(outer_l, outer_w, outer_h, align=(Align.CENTER, Align.CENTER, Align.MIN))
        with Locations((0.0, 0.0, floor_t)):
            Box(
                inner_l,
                inner_w,
                inner_h + cut_overshoot,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.SUBTRACT,
            )

        # Lid fixing bosses, full cavity height, fused into the corners
        with Locations(*[(x, y, floor_t) for x, y in _boss_points()]):
            Cylinder(
                boss_d / 2.0,
                inner_h,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )

        # Board standoffs
        with Locations(*[(x, y, floor_t) for x, y in _standoff_points()]):
            Cylinder(
                standoff_d / 2.0,
                standoff_h,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )

        # Wall-mount ears
        for sign in (-1.0, 1.0):
            x_inner = sign * (outer_l / 2.0 - ear_overlap)
            with Locations((x_inner, 0.0, 0.0)):
                Box(
                    ear_l,
                    ear_w,
                    ear_t,
                    align=(
                        Align.MIN if sign > 0 else Align.MAX,
                        Align.CENTER,
                        Align.MIN,
                    ),
                )

        # Ear fixing holes
        ear_hole_x = outer_l / 2.0 - ear_overlap + ear_l / 2.0
        with BuildSketch(Plane.XY.offset(-cut_overshoot)):
            with Locations(*[(sx * ear_hole_x, 0.0) for sx in (-1.0, 1.0)]):
                Circle(ear_hole_d / 2.0)
        extrude(amount=ear_t + 2.0 * cut_overshoot, mode=Mode.SUBTRACT)

        # Boss pilot holes, drilled down from the cavity rim
        with BuildSketch(Plane.XY.offset(outer_h + cut_overshoot)):
            with Locations(*_boss_points()):
                Circle(boss_pilot_d / 2.0)
        extrude(amount=-(boss_pilot_depth + cut_overshoot), mode=Mode.SUBTRACT)

        # Standoff pilot holes
        with BuildSketch(Plane.XY.offset(floor_t + standoff_h + cut_overshoot)):
            with Locations(*_standoff_points()):
                Circle(standoff_pilot_d / 2.0)
        extrude(amount=-(standoff_pilot_depth + cut_overshoot), mode=Mode.SUBTRACT)

        # Cable glands through the -Y wall
        with BuildSketch(Plane.XZ.offset(outer_w / 2.0 + cut_overshoot)):
            with Locations(*[(sx * gland_dx / 2.0, gland_z) for sx in (-1.0, 1.0)]):
                Circle(gland_d / 2.0)
        extrude(amount=-(wall_t + 2.0 * cut_overshoot), mode=Mode.SUBTRACT)

        # Ventilation slots through the +Y wall
        with BuildSketch(Plane.XZ.offset(-(outer_w / 2.0 + cut_overshoot))):
            with Locations(*[(0.0, z) for z in vent_levels]):
                Rectangle(vent_l, vent_h)
        extrude(amount=wall_t + 2.0 * cut_overshoot, mode=Mode.SUBTRACT)

    return base.part


def make_lid():
    with BuildPart() as lid:
        # Cover plate
        Box(outer_l, outer_w, lid_t, align=(Align.CENTER, Align.CENTER, Align.MIN))

        # Spigot lip, a ring hanging below the plate into the cavity
        lip_outer_l = inner_l - lip_clear
        lip_outer_w = inner_w - lip_clear
        with Locations((0.0, 0.0, -lip_h)):
            Box(
                lip_outer_l,
                lip_outer_w,
                lip_h,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
        with Locations((0.0, 0.0, -lip_h - cut_overshoot)):
            Box(
                lip_outer_l - 2.0 * lip_t,
                lip_outer_w - 2.0 * lip_t,
                lip_h + 2.0 * cut_overshoot,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.SUBTRACT,
            )

        # Corner reliefs so the lip clears the lid bosses.
        # Cut only through the lip depth, never through the cover plate.
        with BuildSketch(Plane.XY.offset(-lip_h - cut_overshoot)):
            with Locations(*_boss_points()):
                Circle(boss_relief_d / 2.0)
        extrude(amount=lip_h + cut_overshoot, mode=Mode.SUBTRACT)

        # Lid screws, through everything
        with BuildSketch(Plane.XY.offset(-lip_h - cut_overshoot)):
            with Locations(*_boss_points()):
                Circle(lid_screw_d / 2.0)
        extrude(
            amount=lip_h + lid_t + 2.0 * cut_overshoot,
            mode=Mode.SUBTRACT,
        )

    return lid.part


def gen_step():
    asm = AssemblyHelper("edge_node_enclosure")
    asm.add(make_base(), "base")
    asm.add(make_lid().locate(Location((0.0, 0.0, outer_h))), "lid")
    return asm.build()


if __name__ == "__main__":
    gen_step()
