"""Check the telescoping range and the click-stop.

Run with the CAD python:  python check_adjustment.py

1. Every click position (gap_min + k * pitch) must seat the bump in a notch with
   zero interference between the two rails.
2. Halfway between clicks the bump must ride on the bar's flat. That interference
   is the deliberate preload that makes the click and the hold.
3. Console envelope clears both rails at the default Slim setting.
4. Bar engagement stays generous across the whole range.
"""
from build123d import Align, Box, Pos

import ps5_slim_rail as R
import ps5_slim_stand as S


def overlap(a, b):
    """Volume of a & b. The boolean returns None when they do not touch, and a
    list when the overlap is in several pieces (one per bump)."""
    common = a & b
    if common is None:
        return 0.0
    if hasattr(common, "volume"):
        return common.volume
    return sum(piece.volume for piece in common)


rail = R.make_rail()
assert rail.is_valid

gaps = [R.gap_min + k * R.detent_pitch for k in range(R.n_clicks + 1)]
seated = []
for g in gaps:
    a, b = S.place_rails(rail, g)
    seated.append(overlap(a, b))
print("click positions: %d (gap %.0f..%.0f step %.0f)" % (len(gaps), gaps[0], gaps[-1], R.detent_pitch))
print("  max interference when seated: %.4f mm3 (want 0)" % max(seated))
assert max(seated) < 1e-6, list(zip(gaps, seated))

between = []
for g in (gaps[0] + 1.0, S.DEFAULT_GAP + 1.0, gaps[-1] - 1.0):
    a, b = S.place_rails(rail, g)
    between.append(overlap(a, b))
print("  between clicks (bump on the flat), mm3: %s (want > 0)" % [round(x, 2) for x in between])
assert all(x > 0.5 for x in between), between

a, b = S.place_rails(rail, S.DEFAULT_GAP)
console = Pos(0, 0, R.rail_h) * Box(R.console_w, R.console_d, R.console_h,
                                    align=(Align.CENTER, Align.CENTER, Align.MIN))
hit = overlap(console, a) + overlap(console, b)
print("console at gap %.0f: overlap %.4f mm3, end clearance %.2f mm each"
      % (S.DEFAULT_GAP, hit, (S.DEFAULT_GAP - R.console_w) / 2.0))
assert hit < 1e-6

for g in (R.gap_min, R.gap_max):
    d = g - 2.0 * R.rail_w
    print("gap %.0f: bar engagement %.0f mm" % (g, R.bar_len + R.sleeve_len - d))
print("OK")
