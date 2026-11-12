"""Check the telescoping range: interference, engagement and console fit.

Run with the CAD python:  python check_adjustment.py
"""
from build123d import Align, Box, Pos, Rot

import ps5_slim_rail as R
import ps5_slim_stand as S


def overlap(a, b):
    """Volume of a & b. The boolean returns None when they do not touch."""
    common = a & b
    return 0.0 if common is None else common.volume


def check(gap, with_console):
    rail = R.make_rail()
    a, b = S.place_rails(rail, gap)
    rails_overlap = overlap(a, b)
    out = {"gap": gap, "valid": a.is_valid and b.is_valid,
           "rail_vs_rail_overlap_mm3": round(rails_overlap, 4)}
    d = gap - 2.0 * R.rail_w
    out["engagement_mm"] = round(R.bar_len + R.sleeve_len - d, 1)
    if with_console:
        c = Pos(0, 0, R.rail_h) * Box(R.console_w, R.console_d, R.console_h,
                                      align=(Align.CENTER, Align.CENTER, Align.MIN))
        out["console_overlap_mm3"] = round(overlap(c, a) + overlap(c, b), 4)
        out["end_gap_each_mm"] = round((gap - R.console_w) / 2.0, 2)
    return out


for g, con in [(R.gap_min, False), (S.DEFAULT_GAP, True), (390.0 + 3.0, False), (R.gap_max, False)]:
    print(check(g, con))
