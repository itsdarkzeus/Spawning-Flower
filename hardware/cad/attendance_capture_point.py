"""Complete attendance hardware: the classroom capture point + the edge node.

Brings every part into one wall-referenced frame so the whole install can be
viewed, exploded and assembled as a unit.

Coordinate convention (the wall frame)
    Origin : on the wall surface, on the vertical centreline of the capture
             point, at the bottom edge of the shroud
    X      : horizontal, along the wall
    +Y     : away from the wall, into the room
    +Z     : up

Bodies
    backplate     wall plate, y = 0..5
    terminal      DS-K1A8503MF-B envelope, mounted on the plate, y = 5..35
    shroud        canopy over the terminal, y = 0..53
    node_base     edge node enclosure base, mounted further along the wall
    node_lid      its lid

The terminal is a documented envelope, not a vendor model - see
terminal_device_envelope.py.
"""

from build123d import Color, Location

from cadpy.assembly import AssemblyHelper

from edge_node_enclosure import make_base, make_lid, outer_h
from terminal_backplate import _build_plate
from terminal_device_envelope import make_device
from terminal_shroud import make_shroud

# --- Placement --------------------------------------------------------------
backplate_t = 5.0
device_h = 155.0

# Rotate a part authored with +Z up into the wall frame, where +Y leaves the
# wall: (x, y, z) -> (x, z, -y).
WALL_ROTATION = (-90.0, 0.0, 0.0)

# The backplate is authored flat in XY with +Z out of the wall, so it needs the
# same rotation, then lifting to sit centred on the terminal.
backplate_loc = Location((0.0, 0.0, device_h / 2.0), WALL_ROTATION)

# The terminal sits on the face of the backplate.
terminal_loc = Location((0.0, backplate_t, 0.0))

# The edge node lives further along the same wall. The extra 180 degrees about
# the box's own Z puts the gland wall at the BOTTOM once it is stood up, so the
# glands face down and water runs off them rather than into them.
node_origin = (320.0, 0.0, 60.0)
node_loc = Location(node_origin, WALL_ROTATION) * Location((0.0, 0.0, 0.0), (0.0, 0.0, 180.0))
node_lid_loc = node_loc * Location((0.0, 0.0, outer_h))

COLORS = {
    "backplate": Color(0.62, 0.66, 0.70),
    "terminal": Color(0.20, 0.22, 0.26),
    "shroud": Color(0.78, 0.80, 0.83),
    "node_base": Color(0.30, 0.46, 0.50),
    "node_lid": Color(0.40, 0.57, 0.61),
}


def gen_step():
    asm = AssemblyHelper("attendance_capture_point")

    asm.add(
        _build_plate().locate(backplate_loc),
        "backplate",
        color=COLORS["backplate"],
    )
    asm.add(
        make_device().locate(terminal_loc),
        "terminal",
        color=COLORS["terminal"],
    )
    asm.add(
        make_shroud(),
        "shroud",
        color=COLORS["shroud"],
    )
    asm.add(
        make_base().locate(node_loc),
        "node_base",
        color=COLORS["node_base"],
    )
    asm.add(
        make_lid().locate(node_lid_loc),
        "node_lid",
        color=COLORS["node_lid"],
    )

    return asm.build()


if __name__ == "__main__":
    gen_step()
