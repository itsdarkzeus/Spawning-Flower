# Fast-food meal box — 3D model

A generic fried-chicken meal box: open clamshell, three pieces of chicken, a
fries carton and chips. Built from a reference photo.

**Deliverable:** `meal_box.glb` — glTF 2.0 binary, 20 named meshes, PBR
materials, 434k triangles, 10.4 MB.

![preview](render/meal_photo_angle.png)

## No branding

The packaging here is **deliberately generic**. No logos, no wordmarks, no
Colonel, no trade dress — those are trademarks and they are not reproduced in
the geometry or the materials. The red carton is a plain red carton.

If you hold the rights to particular branding, the carton and box are clean
single-material meshes and take a texture in Blender without any preparation.

## The two-stage pipeline, and why

A B-rep CAD kernel and a mesh are good at opposite halves of this job, so the
model uses both:

| Stage | Owns | Output |
| --- | --- | --- |
| **CAD** (build123d / OCCT) | Form — the tapered clamshell, the shelled carton, the slanted mouth trim, the chicken's underlying mass | `meal_assembly.step` |
| **Mesh** (`mesh_kit.py`) | Surface — breading, paper wobble | `meal_box.glb` |

**So the STEP contains smooth chicken cores and the GLB contains the crust.**
They are not interchangeable. That is a deliberate split, not an oversight.

### Why the crust is not CAD

The obvious solid-modelling trick for breading is to fuse a scatter of spheres
onto the core. That was built and abandoned:

- **74 large spheres** — fused fine, but read as a lumpy blob, closer to
  cauliflower than chicken.
- **438 small spheres** — a single multi-argument fuse returned a *null shape*.
  Batched into groups of 60 it survived, but left ~20 loose solids where bumps
  had been placed relative to the nominal section radius and never reached the
  shrunken core.
- Even when it worked it cost ~60 s per piece, against ~1.5 s for the loft.

OCCT has no displacement and no noise, and this is what faking it costs.
Displacement along vertex normals is the right tool for surface detail, so the
crust moved to the mesh stage: 4 s for all three pieces, and it actually looks
like fried chicken.

### How the crust is made

`mesh_kit.crust()` applies fractal value noise along vertex normals at three
scales, because one scale reads as either a dented balloon or as sandpaper:

| Scale | Amplitude | Frequency | Reads as |
| --- | --- | --- | --- |
| mass | 13.0 mm | 0.015 | irregular overall lump |
| mid | 6.0 mm | 0.050 | batter drips and folds |
| grain | 3.0 mm | 0.30 | crisp crumb |

Displacement can only move vertices that exist, so each piece is tessellated
finely and then midpoint-subdivided twice — roughly 4.4k triangles becomes
110k — before any noise is applied. A CAD tessellation on its own is far too
sparse and the noise just smears along the loft's iso-lines.

The noise is seeded, so every rebuild produces exactly the same model.

## Files

| File | What |
| --- | --- |
| `chicken_piece.py` | Lofted chicken cores — thigh, tender, wing |
| `packaging.py` | Clamshell base and lid, fries carton, chips |
| `meal_assembly.py` | Scene layout, `gen_step()` and `build_glb()` |
| `mesh_kit.py` | Tessellate, subdivide, noise, displace, GLB writer |
| `tools/preview.py` | Offscreen three.js render, for judging the model |

## Rebuilding

```bash
python meal_assembly.py                                   # GLB + preview
python ../.claude/skills/cad/scripts/step meal_assembly.py  # STEP
```

Needs `build123d`, `cadpy`, `numpy`, and `playwright` for previews only.

## Notes and limits

1. **Flat colours, no textures.** The GLB carries one PBR base colour per mesh —
   no albedo maps, no roughness maps, no UVs, no normal maps. Good enough for a
   diagram, a game prop or a print; for a photoreal render, take it into
   Blender and add materials. Food lives or dies on subsurface scattering and
   texture, and none of that exists here.
2. **Colours are converted sRGB -> linear on export.** glTF defines
   `baseColorFactor` in *linear* space, but palettes get picked in sRGB. Writing
   sRGB values straight through makes every material render washed out, because
   the viewer applies its own linear->sRGB transfer on top - a 0.78 red arrives
   pink and golden chicken arrives cream. `mesh_kit.srgb_to_linear()` handles
   it, so author `color` in sRGB and let the writer convert. Note this is
   invisible in `tools/preview.py`, which renders the sRGB values directly;
   verify colour against the GLB itself through a real glTF loader.
3. **Y-up, metres.** Per the glTF convention the writer converts from
   millimetre Z-up CAD coordinates, so the 256 mm box arrives as 0.256 units.
4. **The layout is constrained by the tray taper.** The box narrows towards its
   floor, so contents sit against a footprint of ±113 × ±82 mm, not the ±126 ×
   ±95 mm of the rim. Three pieces poked through the walls before this was
   accounted for; there is now headroom for the crust pushing outward too.
5. **The carton leans less than in the reference photo.** Past about 40° its
   mouth intersects the open lid.
6. **Not watertight, not printable as-is.** Displacement is applied per body
   with no collision handling, and pieces are allowed to touch. This is a
   visual asset. The STEP is the clean geometry.
