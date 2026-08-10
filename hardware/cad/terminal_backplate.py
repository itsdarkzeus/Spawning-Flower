"""Wall mounting backplate for the Hikvision DS-K1A8503MF-B fingerprint terminal.

Part of the classroom attendance capture point (see hardware/cad/README.md).

Coordinate convention
    Origin : centre of the wall-facing face of the plate
    XY     : the wall plane (X = horizontal, Y = vertical as mounted)
    +Z     : away from the wall, towards the room

Design intent
    The terminal envelope (140 x 155 x 30 mm) is published, but Hikvision does
    not publish the mounting-hole pattern for this SKU. The device fixings are
    therefore VERTICAL SLOTS rather than round holes, so an installer can
    absorb an error in the assumed pattern without re-drilling the plate.
    Confirm the real pattern against the physical rear cover, then either keep
    the slots or set `device_slot_len = device_slot_w` for plain round holes.
"""

from build123d import (
    Align,
    Axis,
    BuildPart,
    BuildSketch,
    Circle,
    Locations,
    Mode,
    Plane,
    RectangleRounded,
    SlotOverall,
    chamfer,
    extrude,
)

from cadpy.assembly import label_shape

# --- Terminal envelope (published) -----------------------------------------
device_w = 140.0
device_h = 155.0
device_d = 30.0

# --- Plate ------------------------------------------------------------------
plate_w = 170.0
plate_h = 190.0
plate_t = 5.0
plate_corner_r = 6.0

# --- Device fixings (ASSUMED pattern - verify against the physical unit) -----
device_hole_dx = 60.0
device_hole_dy = 110.0
device_slot_w = 5.5      # M5 clearance
device_slot_len = 16.0   # overall slot length => +/-5.25 mm of adjustment

# --- Wall fixings -----------------------------------------------------------
wall_hole_dx = 140.0
wall_hole_dy = 160.0
wall_hole_d = 6.5        # M6 masonry anchor clearance

# --- Cable pass-through (RJ45 + 5 VDC barrel) -------------------------------
cable_w = 50.0
cable_h = 40.0
cable_corner_r = 8.0

edge_chamfer = 1.0
cut_overshoot = 1.0


def _through_plane() -> Plane:
    """Sketch plane for through-cuts, dropped below the plate to overshoot."""
    return Plane.XY.offset(-cut_overshoot)


def _corner_points(dx: float, dy: float) -> list[tuple[float, float]]:
    return [(sx * dx / 2.0, sy * dy / 2.0) for sx in (-1, 1) for sy in (-1, 1)]


def gen_step():
    through = plate_t + 2.0 * cut_overshoot

    with BuildPart() as plate:
        # Base plate
        with BuildSketch(Plane.XY):
            RectangleRounded(plate_w, plate_h, plate_corner_r)
        extrude(amount=plate_t)

        # Cable pass-through
        with BuildSketch(_through_plane()):
            RectangleRounded(cable_w, cable_h, cable_corner_r)
        extrude(amount=through, mode=Mode.SUBTRACT)

        # Device fixing slots (vertical adjustment)
        with BuildSketch(_through_plane()):
            with Locations(*_corner_points(device_hole_dx, device_hole_dy)):
                SlotOverall(device_slot_len, device_slot_w, rotation=90)
        extrude(amount=through, mode=Mode.SUBTRACT)

        # Wall anchor holes
        with BuildSketch(_through_plane()):
            with Locations(*_corner_points(wall_hole_dx, wall_hole_dy)):
                Circle(wall_hole_d / 2.0)
        extrude(amount=through, mode=Mode.SUBTRACT)

        # Deburr the room-facing face
        chamfer(plate.edges().group_by(Axis.Z)[-1], edge_chamfer)

    return label_shape(plate.part, "terminal_backplate")


if __name__ == "__main__":
    gen_step()
