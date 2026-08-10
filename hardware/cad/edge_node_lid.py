"""Printable body: edge node enclosure lid.

The assembly lives in `edge_node_enclosure.py`; this exports the lid on its own
so it can be sliced. Geometry comes from `make_lid()` there, so the two never
diverge - edit the parameters in that file, not here.

Exported in its part-local frame with the cover plate spanning z = 0..3 and the
spigot lip hanging below it, rather than in its assembled position.
"""

from cadpy.assembly import label_shape

from edge_node_enclosure import make_lid


def gen_step():
    return label_shape(make_lid(), "edge_node_lid")


if __name__ == "__main__":
    gen_step()
