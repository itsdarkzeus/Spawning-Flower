# Adjustable horizontal PS5 stand

Two identical rails that telescope like a curtain rod. Each rail has one bar and
one sleeve; turn one rail 180 deg about Z and each bar slides into the other
rail's sleeve. **Print the rail twice - there is no left/right.**

Range, tab face to tab face: **340 - 400 mm**. Covers the PS5 Slim (358 mm,
Disc and Digital) and the original PS5 (390 mm).

| Part | File | Size (mm) |
|---|---|---|
| Rail (print x2) | `ps5_slim_rail.py` -> `.step`, `meshes/ps5_slim_rail.stl` | 245 x 236 x 35.4 |
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

## Personalisation

Shallow engraving (0.7 mm) on each rail's outer face, so the sweep of the wall
is untouched:

- **The name** `itsdarkzeus` in an original angular lettering, drawn as stroke
  geometry in `ps5_slim_rail.py` (no font needed). Reads correctly from outside
  on both rails.
- **Two Zeus bolts**, one each side of the name.
- **A signature line** above the name. Its shape comes from a SHA-256 hash of
  the text: amplitude, frequency and phase of three sine waves are taken from
  the hash bytes, so the same text always draws the same line and different
  text draws a different one.

Change `personal_text` (letters in the alphabet below only) or set
`personalise = False` for a plain rail. Letters available: `i t s d a r k z e u`.
Any other letter needs a glyph added to `GLYPHS`.

The engraving cutter is checked against the wall: the build asserts the name
clears the signature line, the line clears the wall top, and the bolts stay
inside the wall and off the rounded corners.

## Design choices

**Form**
- One sweeping wall per rail instead of two tabs: a high crest at the front
  and back, dipping to 22 mm in the middle. The middle of each end face stays
  open for the vents.
- The wall's inner face leans outward 5 deg, so the console drops straight in
  with nothing undercut. Top edge fully rounded (1.3 mm).
- Generous plan corners (20 mm wall side, 8 mm bar side) and a 3 mm rounded
  underside, so the rail reads as lifted off the desk.
- The console sits 15 mm up, floating over the rails.

**Mechanism**
- Bar 12 x 7 mm in a 12.7 x 7.7 mm sleeve (0.35 mm per side printed clearance).
- Bar and sleeve sit below the console underside (3.3 mm gap) and carry no
  weight - the rails do.
- Engagement stays 110 mm closed down to 50 mm fully open.
- 1.5 mm end clearance at the default Slim setting.

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
- **Engraving is untested in print.** Strokes are 1.0 mm wide and 0.7 mm deep,
  which wants a 0.4 mm nozzle and 0.12-0.2 mm layers to stay crisp. Rendered
  shading is too flat to judge depth, so the cut was checked by volume
  (229 mm3 removed per rail) and by rendering the cutter alone.

## Rebuild

    python $CAD/scripts/step ps5_slim_rail.py --stl meshes/ps5_slim_rail.stl
    python $CAD/scripts/step ps5_slim_stand.py
    python check_adjustment.py
