# Horizontal PS5 Slim stand

Two identical end rails (one mirrored) that cradle the console by its 358 mm
length, lifting it off the desk. Works for both Disc and Digital editions.

| Part | File | Size (mm) |
|---|---|---|
| End rail (print x2, one mirrored) | `ps5_slim_rail.py` -> `.step`, `meshes/ps5_slim_rail.stl` | 43.5 x 236 x 30 |
| Assembly with fit-check envelope | `ps5_slim_stand.py` -> `.step` | 358 x 216 x 110 overall |

## Source dimensions

Sony's published outer size: **358 x 96 x 216 mm** (W x H x D) for the Disc
model, **358 x 80 x 216 mm** for the Digital Edition. Width and depth are the
same on both, and the rails only touch the ends, so one design fits both.

## Design choices

- 1.5 mm clearance at each end between the console and the retaining tabs.
- Rails are 236 mm long so they print on a 256 mm bed.
- Rail raises the console 14 mm; tabs rise a further 16 mm.
- Tabs are short and sit at the front/back of each rail only, so the middle of
  each end face is not covered.
- Two 12 mm x 1.5 mm pockets underneath each rail for stick-on rubber feet.

## Assumptions to check

- The console envelope is a box from published dimensions, not a vendor model.
  The real shell is curved, so check the 358 mm end-to-end with calipers.
- The underside contact area near each end and the console's foot positions are
  not published; the rails are 40 mm wide to give generous support.
- Nothing stops the console sliding front-to-back except friction and the
  rubber feet.

## Rebuild

    python $CAD/scripts/step ps5_slim_rail.py --stl meshes/ps5_slim_rail.stl
    python $CAD/scripts/step ps5_slim_stand.py
