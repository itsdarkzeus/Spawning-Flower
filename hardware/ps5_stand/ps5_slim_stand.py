"""Adjustable horizontal PS5 stand: two identical rails plus a fit-check envelope.

`gap` is the distance between the two tab inner faces. The default fits a PS5
Slim with 1.5 mm each end; the mechanism spans R.gap_min to R.gap_max.

The envelope is a box from Sony's published 358 x 216 x 96 mm - not a vendor
model. The real shell is curved and slightly smaller than this box.
"""

from build123d import Align, Box, Color, Pos, Rot

from cadpy.assembly import AssemblyHelper

import ps5_slim_rail as R

DEFAULT_GAP = R.console_w + 2.0 * R.fit_clear


def place_rails(rail, gap):
    """Right rail as modelled; left is the same part turned 180 deg about Z."""
    x = gap / 2.0 - R.rail_w
    return Pos(x, 0.0, 0.0) * rail, Pos(-x, 0.0, 0.0) * Rot(0.0, 0.0, 180.0) * rail


def build(gap=DEFAULT_GAP):
    asm = AssemblyHelper("ps5_adjustable_stand")
    right, left = place_rails(R.make_rail(), gap)
    asm.add(right, "rail_a", color=Color(0.2, 0.2, 0.22))
    asm.add(left, "rail_b", color=Color(0.2, 0.2, 0.22))

    console = Pos(0.0, 0.0, R.rail_h) * Box(
        R.console_w, R.console_d, R.console_h,
        align=(Align.CENTER, Align.CENTER, Align.MIN))
    asm.add(console, "ps5_envelope", color=Color(0.92, 0.92, 0.94))
    return asm.build()


def gen_step():
    return build()


if __name__ == "__main__":
    gen_step()
