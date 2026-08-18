# Prompts to adapt the text-to-cad skill for food

Derived from building three dishes with it: a fast-food meal box, a plated fish
course, and grilled chicken with jollof rice.

## Before you run any of these

The skill is third-party (`earthtojake/text-to-cad`). Editing it in place means
`npx skills install` overwrites your work on the next update, and
`skills-lock.json` pins content hashes so the change will show as drift.

Two clean options:

1. **Fork it** — install from your fork, apply these prompts there.
2. **Write a companion skill** (`food-modeling`) that depends on the CAD skill
   for STEP generation and owns everything below. This is the better choice if
   you want CAD updates to keep flowing.

Prompts 2–4 and 7 are self-contained enough to become the companion skill on
their own.

---

## The finding these prompts encode

The CAD skill is B-rep and STEP-first, which is exactly right for a plate, a
clamshell box or a cob core — surfaces of revolution and lofts, built exactly.
It is the wrong tool for everything that makes food look like food.

Three construction routes are needed, and **the choice between them is the
single most important decision in a food model**:

| Route | Use when | Examples |
| --- | --- | --- |
| **CAD** (loft / revolve) | The form is regular | plate, box, cob core, mound core, sauce body |
| **Displacement** (mesh) | One continuous but irregular surface | seared crust, chicken skin, tomato wrinkles, sauce comb |
| **Instancing** (mesh) | Genuinely separate bodies | rice grains, corn kernels, seeds, herb scatter |

The rule: **ask whether the thing is one surface or many bodies.** Displacement
moves an existing surface — it can never separate one body into many. A
noise-roughened dome is lumpy porridge, never rice, no matter how it is tuned.

---

## Prompt 1 — Route selection in SKILL.md

> Edit `SKILL.md`. Add a section called "Choosing a construction route" after
> "Default assumptions".
>
> State that organic and food subjects need three routes, and that picking the
> wrong one wastes the most time: CAD loft/revolve for regular form,
> mesh displacement for one continuous irregular surface, and mesh instancing
> for genuinely separate bodies.
>
> Give the decision rule explicitly: *is this one surface, or many bodies?*
> Displacement can only move an existing surface; it can never separate one
> body into many. Note that attempting rice or corn kernels by displacement
> always fails, and that attempting them with CAD booleans (fusing hundreds of
> primitives) either takes minutes per piece or returns a null shape from OCCT
> once the argument count climbs.
>
> Add to the "Use this skill when" triggers: food, produce, baked goods,
> plated dishes, organic surfaces, crust, char, grain, kernel.
>
> Amend the line that says STL/3MF/GLB are "secondary" workflows: for food the
> GLB is usually the primary deliverable and the STEP is the intermediate. Do
> not delete the STEP-first discipline, but say when it inverts.

---

## Prompt 2 — New reference: `references/organic-surfaces.md`

> Create `references/organic-surfaces.md`, loaded when the subject is food,
> produce, or any organic surface. Cover, with concrete numbers:
>
> **Displacement basics.** Displacement can only move vertices that already
> exist, so tessellate finely then midpoint-subdivide before applying noise —
> typically 4k triangles to 110k for a 200 mm part. A CAD tessellation alone is
> far too sparse and the noise smears along the loft's iso-lines.
>
> **Amplitude floor.** Sub-millimetre displacement is invisible at plate scale.
> On a 100–200 mm object, surface detail needs roughly 2 mm minimum to read;
> 0.95 mm rendered as perfectly smooth in testing. State this as a rule.
>
> **Anisotropy decides what a pattern IS.** Provide an `axis_scale` parameter
> that stretches the noise field per axis before sampling. Fish flakes run
> ACROSS the fillet, grill marks run ACROSS the stalk, sauce comb lines run
> ALONG the smear. Sampled isotropically, char reads as mould and flakes read
> as generic bumpiness. Give the axis relationship for each.
>
> **Ridged vs smooth noise.** `1 - |fbm|`, sharpened, creases where the field
> crosses zero and reads as a flake edge or crust ridge. Plain fbm gives
> rounded lumps and suits slump and swelling. Say which to reach for.
>
> **Multi-scale is mandatory.** One scale reads as either a dented balloon or
> sandpaper. Give the fried-chicken example: mass 13 mm at frequency 0.015,
> batter folds 6 mm at 0.050, crumb 3 mm at 0.30.
>
> **Masking.** Fade displacement to near zero at loft tips, where the section
> converges and full-amplitude noise on tightly packed vertices throws visible
> spikes. Mask to upward-facing normals for anything that only happens on the
> cooked side.
>
> **Colour must share the field.** A crust that is geometrically present still
> reads flat unless the crevices darken. Re-evaluate the same ridge field in
> the shading function and darken its valleys.
>
> **Edges from geometry, not noise.** A browned border computed from the
> surface normal only darkens the silhouette, which is nearly invisible
> top-down — and top-down is how plated food is photographed. Use a 2D
> elliptical falloff from the part's centreline for the visible band, and keep
> the normal-based term for angled views.

---

## Prompt 3 — New runtime module in `cadpy`

> Add a module to `scripts/packages/cadpy` — call it `cadpy.mesh` — exposing
> the mesh stage as a first-class part of the runtime, since STEP export alone
> cannot produce these results. Pure numpy, no new dependencies.
>
> Required functions:
>
> - `tessellate(shape, tol, angular)` → vertices, faces
> - `weld(verts, faces)` — merge coincident vertices so normals average
>   smoothly across facets
> - `subdivide(verts, faces, levels)` — midpoint 1-to-4 split
> - `vertex_normals`, `neighbour_mean`
> - `value_noise`, `fbm`, `ridged(points, sharpness)`
> - `roughen(verts, faces, amplitude, frequency, octaves, seed, bias,
>   axis_scale, mask)` — displacement along vertex normals
> - `instance(verts, faces, placements)` — replicate one mesh at many
>   (rotation, translation, scale) triples and merge into a single primitive
> - `frame_from_normal(normal, tangent_hint, rng)` — orthonormal basis for
>   laying an instanced piece flat against a surface
> - `curvature_ao(verts, faces, strength, spread)` — occlusion from local
>   concavity
> - `contact_shadow(target, occluders, radius, strength)` — darkening where
>   other geometry sits close to a surface
> - `split_faces(verts, faces, vertex_mask, threshold)` — divide a mesh by a
>   per-vertex field, returning vertex index arrays so colours computed once
>   can be sliced
> - `write_glb(path, primitives)` — see prompt 4
>
> Document that an instanced base mesh's triangle count IS the whole budget,
> because it is drawn thousands of times. Build it directly at a chosen
> resolution (a UV ellipsoid at 64 triangles) rather than inheriting whatever
> the mesher produces.
>
> Document that any instanced shell needs a core solid inside it or you see
> through the gaps, and that the core must be both **clearly inset** and
> **darker than the shell** — at a small inset its smooth silhouette pokes
> through and reads as a solid flange around the object.

---

## Prompt 4 — Colour space and vertex colours

> Document and enforce the glTF colour contract in the GLB writer and in a
> reference file. Three rules, each of which produced a shipped bug:
>
> 1. **`baseColorFactor` is LINEAR, not sRGB.** Palettes get authored in sRGB
>    because that is what a colour picker gives you. Writing them straight
>    through makes every material render washed out, because the viewer applies
>    its own linear→sRGB transfer on top: a 0.78 red arrives pink. The writer
>    must convert.
>
> 2. **`COLOR_0` vertex colours are also linear, and the material factor must
>    be WHITE when they are present** — glTF multiplies the two. This is the
>    capability that makes char marks, browning gradients and sauce density
>    variation possible with no textures and no UVs at all. It should be
>    prominent, not a footnote.
>
> 3. **Author albedo dark.** Under a bright studio rig anything above roughly
>    0.7 blows to white. Cooked-food albedo peaks nearer 0.4–0.55. Palettes
>    should look too dark in isolation and correct once lit.
>
> Add a warning that three.js applies the same material×vertex-colour multiply,
> so any preview harness must white out its material colour too — otherwise the
> preview shows something darker and more saturated than the file.

---

## Prompt 5 — Verification: check the file, not the preview

> Amend the mandatory validation workflow. The skill currently requires a
> `scripts/snapshot` render of the primary STEP. For food that is necessary but
> not sufficient: the STEP holds the smooth core, and everything that makes the
> model work — crust, char, grain, baked lighting — exists only in the exported
> mesh. A STEP snapshot cannot show any of it.
>
> Add a `scripts/verify-glb` tool that loads the **written .glb** through a real
> glTF loader and renders it under lighting rigs approximating consumer
> viewers: a bright, frontal, untone-mapped "studio" preset, plus softer and
> outdoor variants. Require its output for any food deliverable.
>
> State plainly why: an in-memory preview disagreed with the shipped file twice
> during development — once over sRGB vs linear, once over the vertex-colour
> multiply — and both times the preview looked right while the file did not.
> Colour and lighting decisions must be made against the loaded file.
>
> Require a close-up view for any claim about surface detail. A full-plate
> render at 1000 px cannot show whether a crust is actually crisp; the first
> "textured" fillet looked convincingly detailed at plate scale and was
> perfectly smooth close up.

---

## Prompt 6 — Food defaults and a material table

> Add a "Food defaults" section to `SKILL.md`, parallel to the existing
> mechanical defaults:
>
> - Units millimetres, plate diameters 280–310, dinner portions scaled to them
> - Displacement amplitude minimum ~2 mm on a 100–200 mm element
> - Curvature AO strength 0.20–0.30. **Not higher** — at 0.75 every micro-crease
>   on a ridged crust saturates and the piece renders as black camouflage
> - Contact shadow radius ~9–13 mm, strength ~0.4
>
> And a starting roughness table, noting that glTF allows one roughness per
> material so a surface needing two must be split:
>
> | Surface | Roughness |
> | --- | --- |
> | glazed ceramic | 0.14–0.20 |
> | matte ceramic | 0.58–0.72 |
> | sauce, glossy | 0.14–0.16 |
> | caramelised glaze | 0.22 |
> | charred/burnt | 0.68 |
> | seared crust | 0.40–0.62 |
> | rice, dry grain | 0.66 |
> | paper packaging | 0.86 |

---

## Prompt 7 — Guard the CAD traps

> Add a "Known failure modes" section to `references/build123d-modeling.md`.
> Each of these silently produced wrong geometry rather than raising:
>
> **`loft()` overshoots.** The default fits a spline through the sections and
> bulges when they are closely spaced. A mound with four profile stations in
> its top 12% produced a core 151 mm across instead of 118. Use
> `loft(ruled=True)` for profile stacks, and suspect it whenever a lofted part
> exceeds its own control points.
>
> **Revolve profiles split silently.** If the underside curve crosses the top
> surface, the wire becomes two loops and the revolve produces a stunted part
> without error — a 280 mm plate came out 193 mm. Always assert the profile
> made exactly one closed wire before revolving.
>
> **Laying a section stack down takes two rotations.** A loft built along Z
> needs Ry to bring the length onto X and then Rx to swap the section's axes
> back; Ry alone stands the part on its side with width and height exchanged.
>
> **Swept spirals self-intersect.** The radial pitch must exceed the ribbon
> thickness, and the section plane needs an explicit `x_dir` or the ribbon
> lies flat and collides with its neighbouring coil. Assert the pitch.
>
> **Dense boolean fusion fails.** A single multi-argument fuse of ~440 spheres
> returns a null shape from OCCT; batching leaves loose solids where arguments
> did not reach the target. Do not fake surface texture with booleans.

---

## Prompt 8 — Composition rules

> Add a short "Plating" section to the food reference:
>
> - **Tapered vessels have two footprints.** A box or bowl narrows towards its
>   floor; contents sit against the FLOOR limit, not the rim. Three items poked
>   through the walls of a clamshell before this was accounted for.
> - **Seat items on the actual surface.** Sample the vessel's profile and drop
>   each item onto its local height. Dropping everything to one flat height
>   leaves outer items floating or sunk.
> - **Sauces are draped, not placed.** Offset each vertex by the plate's local
>   height so a film follows the well's curve rather than sitting flat on a
>   tangent plane.
> - **Things merge.** Three 108 mm chicken thighs at 40 mm centres read as a
>   single brown mass. Spread repeated elements much further than instinct
>   suggests.
> - **Vary roll, not just spin.** Repeated elements need rotation about their
>   own axis as well as about the vertical, or their surface features line up
>   and the group reads as machined.
> - **Leave headroom for displacement.** Crust and blistering push outward by
>   their amplitude; layout clearances must absorb it.
