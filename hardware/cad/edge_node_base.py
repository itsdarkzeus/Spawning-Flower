"""Printable body: edge node enclosure base.

The assembly lives in `edge_node_enclosure.py`; this exports the base on its
own so it can be sliced. Geometry comes from `make_base()` there, so the two
never diverge - edit the parameters in that file, not here.

The base and lid touch face-to-face at z=58 in the assembly, which merges them
into a single non-manifold mesh when the whole assembly is written to one STL.
Print from these per-body files instead.
"""

from cadpy.assembly import label_shape

from edge_node_enclosure import make_base


def gen_step():
    return label_shape(make_base(), "edge_node_base")


if __name__ == "__main__":
    gen_step()
