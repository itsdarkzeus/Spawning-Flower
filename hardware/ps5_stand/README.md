# Adjustable horizontal PS5 stand

Two identical rails that expand and contract like an expanding hanger. Pull them
apart or push them together and the joint **clicks from step to step and holds,
with no tool and no screw**. Each rail has one bar and one sleeve; turn one rail
180 deg about Z and each bar slides into the other rail's sleeve.
**Print the rail twice - there is no left/right.**

Range, wall face to wall face: **340 - 400 mm in 2 mm clicks** (31 positions).
Covers the PS5 Slim (358 mm, Disc and Digital) and the original PS5 (390 mm).

| Console | Click to | Clearance each end |
|---|---|---|
| PS5 Slim (358) | **360** | 1.0 mm |
| Original PS5 (390) | **392** | 1.0 mm |

| Part | File | Size (mm) |
|---|---|---|
| Rail (print x2) | `ps5_slim_rail.py` -> `.step`, `meshes/ps5_slim_rail.stl` | 245 x 236 x 35.4 |
| Assembly + fit-check envelope | `ps5_slim_stand.py` -> `.step` | gap-dependent |
| Range / interference check | `check_adjustment.py` | |

Hardware (per stand): 4x 12 mm stick-on rubber feet. Optional, only if you want
a rigid locked width: 2x M4 heat-set insert (5.6 x 5.7 mm hole) + 2x M4x12
thumbscrew. The stand holds its width without them.

## Which file do I use?

| For | File |
|---|---|
| **Send to the 3D printer** (print **2 copies**, same file) | `meshes/ps5_slim_rail.stl` (or `.3mf`, same geometry) |
| **View / share in 3D** (rails + console envelope, adjustable gap shown at the Slim setting) | `meshes/ps5_slim_stand.glb` |
| View one rail | `meshes/ps5_slim_rail.glb` |
| Edit / CAD | `ps5_slim_rail.step`, `ps5_slim_stand.step` |

The STL and 3MF are in millimetres. The GLBs are glTF 2.0 standard: metres and
Y-up. Print orientation: as supplied (flat on its underside, wall pointing up).
Both exports are checked watertight with 0 non-manifold edges, volume within
0.07% of the CAD.

## Source dimensions

Sony's published outer size: 358 x 96 x 216 mm (W x H x D) Disc, 358 x 80 x 216
Digital. The rails only touch the console ends, so height does not matter.

## Using it

1. Take the console off. Pull or push the two rails until the gap suits it; the
   joint clicks every 2 mm. Slim: click to 360.
2. Lower the console on, ends inside the walls.

To change width later, lift the console off first, then pull or push. It holds
by itself between clicks of use; no tools, no screws.

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

**Mechanism (the hanger action)**
- Each bar has 31 V-notches, 2 mm apart. Each sleeve has a U-slotted tongue in
  its roof (8 x 20 mm, 2 mm thick) with a 45 deg bump. The bump snaps into a
  notch and the tongue flexes it out again either way, so it clicks both
  directions and holds at every step.
- At rest in a notch the tongue is relaxed; it only flexes while moving between
  clicks, which keeps creep low.
- Estimated hold about 3-5 N per sleeve (calculated, not measured): plenty to keep
  an unloaded frame from drifting, not a rigid lock. The optional thumbscrew
  gives that.
- Bar 12 x 7 mm in a 12.7 x 7.7 mm sleeve (0.35 mm per side printed clearance).
- Bar and sleeve sit below the console underside (3.3 mm gap) and carry no
  weight - the rails do.
- Engagement stays 110 mm closed down to 50 mm fully open.
- 1.0 mm end clearance each end at the default Slim click (360).

## Checked (`check_adjustment.py`)

- All 31 click positions: valid solids and zero rail-to-rail interference, i.e.
  the bump seats exactly in a notch at every step.
- Halfway between clicks: 3.9 mm3 of interference per rail pair, the deliberate
  preload that makes the click and the hold.
- Console envelope clears both rails at 360 (zero overlap, 1.0 mm each end).
- STL / 3MF / GLB: watertight, 0 non-manifold edges, volume within 0.07% of CAD.

## Not verified - check before relying on it

- **Print fit is untested.** 0.35 mm slide clearance is a typical FDM value;
  tune `slide_clear` for your printer.
- Console envelope is a box from published dimensions, not a vendor model. The
  real shell is curved - measure the 358 mm end to end with calipers.
- Underside contact area and foot positions are not published; rails are 40 mm
  wide for generous support.
- Nothing stops the console sliding front to back except friction.
- **The click action is untested in print.** The geometry seats and preloads
  correctly in CAD, but the real hold force depends on your filament and
  printer. Print in PETG: the tongue is a spring and PLA can creep or snap.
  If it feels loose, raise `bump_h`; if too stiff, lower it (both in the rail
  source), or fit the optional thumbscrew.
- The 1.0 mm tongue slot needs a clean 0.4 mm nozzle print to open fully; clear
  any strings with a blade.
- **Engraving is untested in print.** Strokes are 1.0 mm wide and 0.7 mm deep,
  which wants a 0.4 mm nozzle and 0.12-0.2 mm layers to stay crisp. Rendered
  shading is too flat to judge depth, so the cut was checked by volume
  (229 mm3 removed per rail) and by rendering the cutter alone.

## Rebuild

Pass the mesh tolerances explicitly. The default export tolerance produced a
non-manifold STL (a 0.2 mm tip at the wall crest), which these settings avoid.

    T="--mesh-tolerance 0.02 --mesh-angular-tolerance 0.2"
    python $CAD/scripts/step ps5_slim_rail.py --stl meshes/ps5_slim_rail.stl \
        --3mf meshes/ps5_slim_rail.3mf --glb meshes/ps5_slim_rail.glb $T
    python $CAD/scripts/step ps5_slim_stand.py --glb meshes/ps5_slim_stand.glb $T
    python check_adjustment.py
