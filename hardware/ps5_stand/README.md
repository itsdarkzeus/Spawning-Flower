# Adjustable horizontal PS5 stand

Two identical rails that telescope like a curtain rod. Each rail has one bar and
one sleeve; turn one rail 180 deg about Z and each bar slides into the other
rail's sleeve. **Print the rail twice - there is no left/right.**

Range, tab face to tab face: **340 - 400 mm**. Covers the PS5 Slim (358 mm,
Disc and Digital) and the original PS5 (390 mm).

| Part | File | Size (mm) |
|---|---|---|
| Rail (print x2) | `ps5_slim_rail.py` -> `.step`, `meshes/ps5_slim_rail.stl` | 243.5 x 236 x 32 |
| Assembly + fit-check envelope | `ps5_slim_stand.py` -> `.step` | gap-dependent |
| Range / interference check | `check_adjustment.py` | |

Hardware (per stand): 2x M4 heat-set insert (5.6 x 5.7 mm hole), 2x M4x12
thumbscrew, 4x 12 mm stick-on rubber feet.

## Source dimensions

Sony's published outer size: 358 x 96 x 216 mm (W x H x D) Disc, 358 x 80 x 216
Digital. The rails only touch the console ends, so height does not matter.

## Using it

1. Slide the rails apart until the tab faces are ~3 mm wider than the console.
2. Tighten both thumbscrews (they are under where the console sits).
3. Lower the console on, ends inside the tabs.

Set the width with the console off: the lock is not reachable once it is on.

## Design choices

- Bar 12 x 8 mm in a 12.7 x 8.7 mm sleeve (0.35 mm per side printed clearance).
- Bar and sleeve sit below the console underside (2.5 mm gap) and carry no
  weight - the rails do.
- Engagement stays 110 mm closed down to 50 mm fully open.
- 1.5 mm end clearance at the default Slim setting.
- Tabs sit at the front/back of each rail only, keeping the middle of each end
  face open for vents.
- Rail lifts the console 16 mm; tabs rise a further 16 mm.

## Checked (`check_adjustment.py`)

At gap 340 / 361 / 393 / 400: valid solids, zero rail-to-rail interference,
and zero console overlap at 361.

## Not verified - check before relying on it

- **Print fit is untested.** 0.35 mm slide clearance is a typical FDM value;
  tune `slide_clear` for your printer.
- Console envelope is a box from published dimensions, not a vendor model. The
  real shell is curved - measure the 358 mm end to end with calipers.
- Underside contact area and foot positions are not published; rails are 40 mm
  wide for generous support.
- Nothing stops the console sliding front to back except friction.
- Lock is a screw pressing on the bar, not a ratchet; it can slip under a knock.

## Rebuild

    python $CAD/scripts/step ps5_slim_rail.py --stl meshes/ps5_slim_rail.stl
    python $CAD/scripts/step ps5_slim_stand.py
    python check_adjustment.py
