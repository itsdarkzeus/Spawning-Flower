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

Outputs
    gen_step() : the 5 mm plate as a solid
    gen_dxf()  : the laser/waterjet cut profile, projected from the wall-facing
                 face of that same solid rather than redrawn from formulas, so
                 the DXF cannot drift out of step with the 3D part.
"""

import math

from build123d import (
    Axis,
    BuildPart,
    BuildSketch,
    Circle,
    GeomType,
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

# --- DXF --------------------------------------------------------------------
CUT_LAYER = "CUT"
CHAIN_TOL = 1.0e-4


def _through_plane() -> Plane:
    """Sketch plane for through-cuts, dropped below the plate to overshoot."""
    return Plane.XY.offset(-cut_overshoot)


def _corner_points(dx: float, dy: float) -> list[tuple[float, float]]:
    return [(sx * dx / 2.0, sy * dy / 2.0) for sx in (-1, 1) for sy in (-1, 1)]


def _build_plate():
    """The plate solid. Shared by the STEP export and the DXF projection."""
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

    return plate.part


def gen_step():
    return label_shape(_build_plate(), "terminal_backplate")


# --- DXF projection ---------------------------------------------------------


def _is_full_circle(edge) -> bool:
    return (edge @ 0 - edge @ 1).length < CHAIN_TOL


def _order_edges(edges):
    """Walk a wire's edges end-to-end, flipping any that run backwards.

    Returns [(edge, start_point, end_point), ...] in contour order.
    """
    remaining = list(edges)
    first = remaining.pop(0)
    chain = [(first, first @ 0, first @ 1)]

    while remaining:
        cursor = chain[-1][2]
        for index, edge in enumerate(remaining):
            start, end = edge @ 0, edge @ 1
            if (start - cursor).length < CHAIN_TOL:
                chain.append((edge, start, end))
            elif (end - cursor).length < CHAIN_TOL:
                chain.append((edge, end, start))
            else:
                continue
            remaining.pop(index)
            break
        else:
            raise ValueError("contour does not close; cannot emit a cut profile")

    if (chain[-1][2] - chain[0][1]).length > CHAIN_TOL:
        raise ValueError("contour does not close; cannot emit a cut profile")
    return chain


def _bulge(edge, start, end) -> float:
    """DXF bulge for an arc segment: tan(included angle / 4), signed CCW."""
    if edge.geom_type != GeomType.CIRCLE:
        return 0.0

    centre = edge.arc_center
    angle = lambda p: math.degrees(math.atan2(p.Y - centre.Y, p.X - centre.X))

    a_start = angle(start)
    span = (angle(end) - a_start) % 360.0
    mid_span = (angle(edge @ 0.5) - a_start) % 360.0

    # If the geometric midpoint falls inside the CCW sweep the arc runs CCW,
    # otherwise it is the complementary CW arc.
    included = span if mid_span <= span else span - 360.0
    return math.tan(math.radians(included) / 4.0)


def _emit_wire(msp, wire) -> str:
    edges = wire.edges()

    if len(edges) == 1 and edges[0].geom_type == GeomType.CIRCLE and _is_full_circle(edges[0]):
        centre = edges[0].arc_center
        msp.add_circle(
            (centre.X, centre.Y),
            edges[0].radius,
            dxfattribs={"layer": CUT_LAYER},
        )
        return "CIRCLE"

    points = [
        (start.X, start.Y, 0.0, 0.0, _bulge(edge, start, end))
        for edge, start, end in _order_edges(edges)
    ]
    msp.add_lwpolyline(
        points,
        format="xyseb",
        close=True,
        dxfattribs={"layer": CUT_LAYER},
    )
    return "LWPOLYLINE"


def gen_dxf():
    import ezdxf

    part = _build_plate()

    # The wall-facing face carries the true cut profile; the room-facing face
    # is chamfered and therefore smaller.
    face = part.faces().filter_by(Axis.Z).sort_by(Axis.Z)[0]

    doc = ezdxf.new(setup=True)
    doc.units = ezdxf.units.MM
    doc.layers.add(CUT_LAYER, color=1)
    msp = doc.modelspace()

    _emit_wire(msp, face.outer_wire())
    for inner in face.inner_wires():
        _emit_wire(msp, inner)

    return doc


if __name__ == "__main__":
    gen_step()
    gen_dxf()
