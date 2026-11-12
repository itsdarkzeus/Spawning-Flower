"""Horizontal PS5 Slim stand: two mirrored end rails plus a fit-check envelope.

The envelope is a 358 x 216 x 96 box standing in for the console - Sony's
published outer dimensions, not a vendor CAD model. It exists to prove the rails
fit; the real console shell is curved and slightly smaller than this box.
"""

from build123d import Color, Plane, Pos

from cadpy.assembly import AssemblyHelper

import ps5_slim_rail as R


def gen_step():
    asm = AssemblyHelper("ps5_slim_stand")

    right = R.make_rail()
    left = right.mirror(Plane.YZ)
    asm.add(right, "rail_right", color=Color(0.2, 0.2, 0.22))
    asm.add(left, "rail_left", color=Color(0.2, 0.2, 0.22))

    from build123d import Align, Box
    console = Pos(0.0, 0.0, R.rail_h) * Box(
        R.console_w, R.console_d, R.console_h,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    asm.add(console, "ps5_slim_envelope", color=Color(0.92, 0.92, 0.94))
    return asm.build()


if __name__ == "__main__":
    gen_step()
