"""Anti-tamper / weather canopy for the Hikvision DS-K1A8503MF-B terminal.

Part of the classroom attendance capture point (see hardware/cad/README.md).

Coordinate convention
    Origin : centre of the wall line at the base of the shroud
    X      : horizontal, across the wall
    +Y     : away from the wall, towards the room
    +Z     : up

Design intent
    A three-sided canopy - top slab plus two side cheeks - that overhangs the
    terminal. Open at the front, bottom and back so the screen, the fingerprint
    sensor and the card field stay clear while the unit is shaded from sun and
    rain and shielded from casual shoulder-surfing at the queue.

    Sized around the published 140 x 155 x 30 mm envelope plus the 5 mm
    backplate it sits on, so the canopy clears the terminal in every axis.
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

# --- Terminal envelope (published) + backplate ------------------------------
device_w = 140.0
device_h = 155.0
device_d = 30.0
backplate_t = 5.0

# --- Clearances -------------------------------------------------------------
side_clear = 4.0      # per side, terminal to inner cheek face
top_clear = 6.0       # terminal top to underside of canopy
front_overhang = 18.0  # canopy projection beyond the terminal front face

wall_t = 3.0

# --- Derived cavity / outer shell ------------------------------------------
inner_w = device_w + 2.0 * side_clear                  # 148
inner_h = device_h + top_clear                         # 161
inner_d = backplate_t + device_d + front_overhang      # 53

outer_w = inner_w + 2.0 * wall_t                       # 154
outer_h = inner_h + wall_t                             # 164
outer_d = inner_d                                      # 53

# --- Back mounting flanges --------------------------------------------------
flange_w = 22.0
flange_t = 4.0        # thickness in Y, sits flat against the wall
flange_overlap = 2.0  # into the side cheek, so the fuse is not face-coincident
flange_hole_d = 5.5   # M5 clearance
flange_hole_z = (28.0, 136.0)

# Applied to both the inner and outer front lip edges, so it must stay well
# under wall_t / 2 or the chamfer consumes the whole wall and OCCT fails.
edge_chamfer = 0.8
cut_overshoot = 1.0


def gen_step():
    with BuildPart() as shroud:
        # Outer block
        Box(
            outer_w,
            outer_d,
            outer_h,
            align=(Align.CENTER, Align.MIN, Align.MIN),
        )

        # Hollow it out, opening the front (+Y), back (-Y) and bottom (-Z).
        # Overshoot in Y and Z so no cutting face is coincident with a wall.
        with Locations((0.0, -cut_overshoot, -cut_overshoot)):
            Box(
                inner_w,
                outer_d + 2.0 * cut_overshoot,
                inner_h + cut_overshoot,
                align=(Align.CENTER, Align.MIN, Align.MIN),
                mode=Mode.SUBTRACT,
            )

        # Back mounting flanges, one per side, overlapping the cheek slightly
        for sign in (-1.0, 1.0):
            x_inner = sign * (outer_w / 2.0 - flange_overlap)
            with Locations((x_inner, 0.0, 0.0)):
                Box(
                    flange_w,
                    flange_t,
                    outer_h,
                    align=(
                        Align.MIN if sign > 0 else Align.MAX,
                        Align.MIN,
                        Align.MIN,
                    ),
                )

        # Flange fixing holes, drilled through Y
        hole_x = outer_w / 2.0 - flange_overlap + flange_w / 2.0
        # Plane.XZ normal is -Y, so offset backwards to start in front of the
        # flange and extrude through it.
        with BuildSketch(Plane.XZ.offset(-cut_overshoot)):
            with Locations(
                *[
                    (sx * hole_x, z)
                    for sx in (-1.0, 1.0)
                    for z in flange_hole_z
                ]
            ):
                Circle(flange_hole_d / 2.0)
        extrude(amount=flange_t + 2.0 * cut_overshoot, mode=Mode.SUBTRACT)

        # Soften the exposed front lip
        front_edges = shroud.edges().filter_by_position(
            Axis.Y, outer_d - 0.01, outer_d + 0.01
        )
        chamfer(front_edges, edge_chamfer)

    return label_shape(shroud.part, "terminal_shroud")


if __name__ == "__main__":
    gen_step()
