# Attendance system — fabricated parts

Parametric CAD for the classroom attendance capture point built around the
Hikvision **DS-K1A8503MF-B** fingerprint terminal, and the per-building edge
node that runs the ISAPI sync agent.

Everything here is generated from build123d Python. **Edit the `.py`, never the
`.step`** — the STEP files are build outputs.

| Source | Output | What it is |
| --- | --- | --- |
| `terminal_backplate.py` | `terminal_backplate.step` + `.dxf` | Wall plate the terminal bolts to, and its cut profile |
| `terminal_shroud.py` | `terminal_shroud.step` | Anti-tamper / weather canopy over the terminal |
| `edge_node_enclosure.py` | `edge_node_enclosure.step` | Base + lid box for the Pi sync agent and UPS |

## Regenerating

Requires Python 3.12+ and the CAD skill runtime (`build123d`, `cadpy`):

```bash
python -m venv .venv && . .venv/bin/activate
pip install -e ../../.claude/skills/cad/scripts/packages/cadpy playwright==1.56.0

CAD=../../.claude/skills/cad
python $CAD/scripts/step terminal_backplate.py
python $CAD/scripts/step terminal_shroud.py
python $CAD/scripts/step edge_node_enclosure.py

python $CAD/scripts/inspect refs terminal_backplate.step --facts --planes --positioning

# Cut profile for the backplate
python ../../.claude/skills/dxf/scripts/dxf terminal_backplate.py
```

To review in the browser:

```bash
npm --prefix ../../.claude/skills/cad-viewer/scripts/viewer run serve -- \
  --host 127.0.0.1 --dir "$PWD" --json
```

## Parts

### 1. Terminal backplate — 170 × 190 × 5 mm

Screws to the wall first; the terminal then mounts to it. Keeping the terminal
off the masonry means a failed unit can be swapped without re-drilling, which
matters when you are maintaining dozens of these.

- 4 × Ø6.5 wall anchor holes on a 140 × 160 mm pattern (M6 masonry anchors)
- 4 × 5.5 mm slots, 16 mm overall, on a 60 × 110 mm pattern for the terminal
- 50 × 40 mm rounded cable pass-through for RJ45 + 5 VDC
- 1.0 mm chamfer on the room-facing face

> **The device fixing pattern is an assumption.** Hikvision does not publish the
> mounting-hole pattern for this SKU, and I could not retrieve it from the
> datasheet. That is exactly why the device fixings are **slots, not holes** —
> they give ±5.25 mm of vertical adjustment to absorb an error in the assumed
> 60 × 110 mm pattern. **Measure a real unit before cutting a production batch.**
> Once confirmed, set `device_hole_dx` / `device_hole_dy`, and set
> `device_slot_len = device_slot_w` if you want plain round holes.

Suggested material: 5 mm aluminium (laser + drill) for exposed locations, or
3D-printed PETG for indoor rooms.

#### Cut profile — `terminal_backplate.dxf`

Ready to send to a laser, waterjet or plasma cutter. `gen_dxf()` **projects the
wall-facing face of the same solid** that `gen_step()` exports, rather than
redrawing the outline from formulas, so the two cannot drift apart. The
wall-facing face is used deliberately: the room-facing face carries the 1 mm
deburr chamfer and is therefore slightly smaller.

- Millimetres (`doc.units = MM`), modelspace, 1:1, centred on the origin
- Every contour on a single `CUT` layer
- 6 closed `LWPOLYLINE` (outline, cable cutout, 4 slots) + 4 `CIRCLE` (anchors)
- Arcs are real arcs — polyline bulges and true circles, not faceted polygons

This is a flat plate, so there are no bend lines and no bend layer. If you move
to a folded sheet-metal version, put fold lines on a separate layer with "bend"
in the name so the shop's software classifies them correctly.

Before ordering, run the profile through `$sendcutsend` (or your vendor's own
preflight) to check material, thickness and minimum feature sizes. Note the
5.5 mm slots and 6.5 mm holes against your chosen thickness — some processes
impose a minimum hole diameter relative to material thickness.

### 2. Terminal shroud — 194 × 53 × 164 mm

A three-sided canopy: top slab plus two side cheeks, open at the front, bottom
and back so the screen, sensor and card field stay clear.

- 148 mm internal width → 4 mm clearance per side on the 140 mm device
- 161 mm internal height → 6 mm over the 155 mm device
- 53 mm projection = 5 mm backplate + 30 mm device + 18 mm overhang
- 3 mm walls, 0.8 mm chamfer on the front lip
- 4 × Ø5.5 fixings through back flanges

Worth fitting where terminals sit at building entrances (sun and rain) or where
a queue forms behind the person scanning.

### 3. Edge node enclosure — 173 × 95 × 61 mm (assembly)

One per building. Holds the Raspberry Pi running the sync agent and local SQLite
queue, plus a UPS/battery board.

- 120 × 90 × 55 mm cavity, 2.5 mm walls, 3 mm floor
- 4 × board standoffs, 6 mm tall, on the **58 × 49 mm Raspberry Pi pattern**
  (common to Pi 4B and Pi 5), Ø2.1 pilots for M2.5
- 4 × corner bosses full cavity height, Ø2.5 pilots for M3, with matching
  Ø3.4 clearance holes in the lid
- Lid spigot lip, 2 mm deep, with corner reliefs so it clears the bosses
- 2 × Ø16.5 M16 cable glands on the lower wall (fit downward so water drains)
- 5 × ventilation slots on the opposite wall
- 2 × wall-mount ears, Ø5.5

Suggested material: 3D-printed PETG or ABS. PLA is a poor choice — these boxes
sit in unconditioned rooms.

## Assumptions and limits

1. **Terminal hole pattern is assumed** (see above). Verify before batching.
2. **No board-level fit check was performed.** The standoff pattern comes from
   the published Raspberry Pi mechanical spec. Nothing here has been checked
   against a real board or a specific UPS HAT. Re-download the catalog Pi 5
   model and do your own fit check:
   ```bash
   python ../../.claude/skills/step-parts/scripts/download_step_part.py \
     --id raspberry_pi_5 --download --out-dir vendor
   ```
3. **No structural, thermal, tolerance or IP-rating analysis was done.** Wall
   thicknesses and clearances are first-pass modelling defaults. The vent slots
   mean the enclosure has **no meaningful ingress rating** — do not mount it
   outdoors or anywhere exposed without redesigning that face.
4. Print/cut clearances assume a well-tuned machine. The lid lip has 0.4 mm
   total clearance, which is tight for FDM; open it up if your printer runs wide.

## Validation performed

Deterministic checks against the exported STEP, not the source:

- Bounding boxes: backplate 170 × 190 × 5, shroud 194 × 53 × 164, enclosure
  173 × 95 × 61
- Enclosure planes confirm cavity ±60 × ±45, floor top z=3, rim z=58, lid top
  z=61, walls 2.5 mm
- Cylinder axes recovered from the STEP confirm every hole pattern:
  standoffs and their pilots at (±29, ±24.5); bosses, boss pilots, lid screws
  and lip reliefs all coaxial at (±56, ±41); glands at (±17); ears at (±73.5);
  backplate anchors at (±70, ±80); backplate slots at x=±30 spanning
  y=±49.75…±60.25 (16 mm overall, 60 × 110 pattern)
- Snapshot review: iso, opposed iso, front, and lid-hidden top views

DXF (`ezdxf`, against the written file):

- Units MM; 6 closed LWPOLYLINE + 4 CIRCLE, no other entities, all on `CUT`
- Extents exactly 170.000 × 190.000 mm, centred on (0, 0)
- Anchors Ø6.50 at (±70, ±80); slots 5.50 × 16.00 at (±30, ±55); cable cutout
  50.00 × 40.00 centred
- **Area cross-check**: net cut area 29865.22 mm² against the STEP wall-facing
  face area of 29865.80 mm² — 0.002%, i.e. polyline flattening tolerance. This
  is what confirms every arc bulge sign and sweep direction is right; bbox
  checks alone would not catch an inverted arc.
