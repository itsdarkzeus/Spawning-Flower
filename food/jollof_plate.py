"""Grilled chicken and jollof rice — full scene, STEP + GLB.

Follows the reference: charred thighs front-left, a mound of jollof rice right,
grilled corn rounds arcing across the back, a dipping pot of chilli sauce top
right, all on a wide-rimmed matte black plate.

Three construction routes are used, chosen per element rather than uniformly:

    revolve      the plate - a surface of revolution, exactly what CAD is for
    displacement the chicken - one continuous but very irregular surface
    instancing   rice grains and corn kernels - genuinely separate bodies,
                 which displacement can never produce

Lighting is baked into the vertex colours (curvature AO plus contact shadows),
because a GLB carries none.

Coordinate frame: plate centred on the origin, resting on Z=0, +Z up.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from build123d import Color, Pos, Rot

from cadpy.assembly import AssemblyHelper

import grill
import rice as R
import shading
from mesh_kit import (contact_shadow, curvature_ao, instance, roughen,
                      split_faces, subdivide, tessellate, weld, write_glb)
from plate import make_rimmed_plate

HERE = Path(__file__).resolve().parent

# --- palette, sRGB ----------------------------------------------------------
COL_PLATE = (0.115, 0.115, 0.122)
COL_CHICKEN = (0.42, 0.16, 0.05)
COL_CORN = (0.72, 0.50, 0.10)
COL_COB = (0.74, 0.70, 0.52)
COL_RICE = (0.66, 0.30, 0.07)
COL_RICE_CORE = (0.24, 0.10, 0.03)
COL_ONION = (0.30, 0.50, 0.15)
COL_POT = (0.055, 0.055, 0.060)
COL_SAUCE = (0.44, 0.07, 0.03)

# Plate surface, sampled from the same control points the revolve uses.
_PLATE_PROFILE = [(0.0, 10.0), (70.0, 10.4), (105.0, 11.6), (120.0, 20.0),
                  (132.0, 25.4), (155.0, 26.0)]


def plate_height(x, y):
    r = np.hypot(np.asarray(x, dtype=float), np.asarray(y, dtype=float))
    return np.interp(r, [p[0] for p in _PLATE_PROFILE], [p[1] for p in _PLATE_PROFILE])


def seat(x, y, spin=0.0, lift=0.0):
    return Pos(float(x), float(y), float(plate_height(x, y)) + lift) * Rot(0.0, 0.0, spin)


# --- layout ------------------------------------------------------------------
RICE_AT = (54.0, -4.0)
RICE_SCALE = 0.88

# Spread further apart than instinct suggests: at 40 mm centres three 108 mm
# thighs merge into a single brown mass and read as one piece.
THIGHS = [                      # x, y, spin, extra lift
    (-92.0, -18.0, 38.0, 0.0),
    (-46.0, -56.0, 4.0, 1.5),
    (10.0, -80.0, -26.0, 3.0),
]

# Roll about each cob's own axis matters as much as the spin: four rounds at
# the same roll read as a machined row rather than four pieces of corn.
CORN = [                        # x, y, spin about Z, roll about cob axis, tilt
    (-96.0, 34.0, 24.0, 12.0, -4.0),
    (-64.0, 62.0, 38.0, 74.0, 3.0),
    (-24.0, 80.0, 54.0, 138.0, -6.0),
    (16.0, 86.0, 70.0, 201.0, 5.0),
]

POT_AT = (86.0, 68.0)


def _rot_z(deg):
    a = np.radians(deg)
    return np.array([[np.cos(a), -np.sin(a), 0.0], [np.sin(a), np.cos(a), 0.0], [0.0, 0.0, 1.0]])


def _rot_y(deg):
    a = np.radians(deg)
    return np.array([[np.cos(a), 0.0, np.sin(a)], [0.0, 1.0, 0.0], [-np.sin(a), 0.0, np.cos(a)]])


def _rot_x(deg):
    a = np.radians(deg)
    return np.array([[1.0, 0.0, 0.0], [0.0, np.cos(a), -np.sin(a)], [0.0, np.sin(a), np.cos(a)]])


def _corn_round(x, y, spin, roll=0.0, tilt=0.0):
    """Core + kernel meshes for one cob round, placed on the plate."""
    core = grill.make_cob_core()
    cv, cf = weld(*tessellate(core, 0.20, 0.20))
    kv, kf = grill.kernel_shell()

    # Lying on its side, so it rests at its outer radius.
    z = float(plate_height(x, y)) + grill.COB_RADIUS + 1.2
    rot = _rot_z(spin) @ _rot_y(tilt) @ _rot_x(roll)
    place = [(rot, np.array([x, y, z]), 1.0)]
    return instance(cv, cf, place), instance(kv, kf, place), rot


def _pot():
    """Small dipping pot with a disc of chilli sauce in it."""
    from build123d import BuildPart, BuildSketch, Circle, Plane, loft

    with BuildPart() as pot:
        for u, r in [(0.0, 26.0), (0.35, 31.0), (0.8, 35.5), (1.0, 37.0)]:
            with BuildSketch(Plane.XY.offset(u * 34.0)):
                Circle(r)
        loft(ruled=True)
        for u, r in [(0.12, 22.0), (0.4, 27.5), (0.85, 32.0), (1.02, 33.5)]:
            with BuildSketch(Plane.XY.offset(u * 34.0)):
                Circle(r)
        from build123d import Mode
        loft(ruled=True, mode=Mode.SUBTRACT)

    with BuildPart() as sauce:
        for u, r in [(0.0, 30.0), (1.0, 31.5)]:
            with BuildSketch(Plane.XY.offset(19.0 + u * 4.0)):
                Circle(r)
        loft(ruled=True)

    return pot.part, sauce.part


def _bodies():
    """CAD solids only - the instanced elements are mesh-stage and not here."""
    out = [("plate", make_rimmed_plate(), COL_PLATE)]

    scaled = R.make_core()
    out.append(("rice_core", seat(*RICE_AT) * scaled, COL_RICE_CORE))

    for i, (x, y, spin, lift) in enumerate(THIGHS, start=1):
        out.append((f"chicken_{i}", seat(x, y, spin, lift) * grill.make_thigh(), COL_CHICKEN))

    pot, sauce = _pot()
    out.append(("pot", seat(*POT_AT) * pot, COL_POT))
    out.append(("pot_sauce", seat(*POT_AT) * sauce, COL_SAUCE))
    return out


def gen_step():
    asm = AssemblyHelper("jollof_plate")
    for label, solid, col in _bodies():
        asm.add(solid, label, color=Color(*col))
    return asm.build()


def build_glb(path=None):
    path = Path(path or HERE / "jollof_plate.glb")
    built = []

    for index, (label, solid, col) in enumerate(_bodies()):
        rough, vcolors = 0.55, None

        if label == "plate":
            v, f = weld(*tessellate(solid, 0.12, 0.12))
            rough = 0.72                      # matte black ceramic
            vcolors = np.tile(np.asarray(COL_PLATE, dtype=float), (len(v), 1))

        elif label.startswith("chicken"):
            seed = 21 + index * 7
            v, f = weld(*tessellate(solid, 0.12, 0.14))
            v, f = subdivide(v, f, 3)
            v = grill.char_skin(v, f, seed=seed)
            colours = shading.chicken(v, f, seed=seed)

            # One glTF material carries one roughness, so a surface that is wet
            # where it is glazed and dry where it is burnt cannot be a single
            # primitive. Split it on the same char field that drives the colour.
            mask = shading.chicken_char(v, f, seed=seed)
            (bv, bf, bi), (gv, gf, gi) = split_faces(v, f, mask, 0.42)
            if len(bf):
                built.append([f"{label}_char", bv, bf, col, 0.68, colours[bi]])
            built.append([f"{label}_glaze", gv, gf, col, 0.22, colours[gi]])
            continue

        elif label == "rice_core":
            v, f = weld(*tessellate(solid, 0.4, 0.4))
            vcolors = np.tile(np.asarray(COL_RICE_CORE, dtype=float), (len(v), 1))
            rough = 0.85

        elif label == "pot":
            v, f = weld(*tessellate(solid, 0.15, 0.15))
            vcolors = np.tile(np.asarray(COL_POT, dtype=float), (len(v), 1))
            rough = 0.66

        else:                                  # pot sauce
            v, f = weld(*tessellate(solid, 0.2, 0.2))
            v, f = subdivide(v, f, 1)
            v = roughen(v, f, amplitude=0.5, frequency=0.28, octaves=3, seed=770)
            vcolors = shading.sauce(v, f, seed=79, base=(0.46, 0.08, 0.03),
                                    deep=(0.24, 0.035, 0.015), thin=(0.60, 0.18, 0.05))
            rough = 0.16

        built.append([label, v, f, col, rough, vcolors])

    # --- instanced elements ---------------------------------------------
    rx, ry = RICE_AT
    rz = float(plate_height(rx, ry))
    shift = np.array([rx, ry, rz])

    gv, gf = R.grain_shell()
    gv = gv + shift
    built.append(["rice_grains", gv, gf, COL_RICE, 0.66, shading.jollof(gv, gf)])

    cv, cf = R.crown_bits()
    cv = cv + shift
    built.append(["rice_crown", cv, cf, COL_ONION, 0.55,
                  np.tile(np.asarray(COL_ONION, dtype=float), (len(cv), 1))])

    for i, (x, y, spin, roll, tilt) in enumerate(CORN, start=1):
        (cob_v, cob_f), (ker_v, ker_f), rot = _corn_round(x, y, spin, roll, tilt)
        built.append([f"cob_{i}", cob_v, cob_f, COL_COB, 0.70,
                      np.tile(np.asarray(COL_COB, dtype=float), (len(cob_v), 1))])
        # Char is gated on distance from the cob AXIS, so the shading field has
        # to be evaluated in the cob's own frame, not the plate's.
        origin = np.array([x, y, float(plate_height(x, y)) + grill.COB_RADIUS + 1.2])
        local = (ker_v - origin) @ rot
        built.append([f"kernels_{i}", ker_v, ker_f, COL_CORN, 0.42,
                      shading.corn(local, ker_f, seed=71 + i * 5)])

    _bake_lighting(built)

    prims = [{"name": lb, "verts": v, "faces": f, "vcolors": vc,
              "color": col, "roughness": r, "metallic": 0.0}
             for lb, v, f, col, r, vc in built]

    size = write_glb(path, prims)
    tris = sum(len(p["faces"]) for p in prims)
    print(f"GLB: {path}  {size / 1e6:.2f} MB  {len(prims)} meshes  {tris} triangles")
    return prims


def _bake_lighting(built):
    food = [v for label, v, *_ in built if label != "plate"]
    occluders = np.concatenate(food, axis=0) if food else None

    for entry in built:
        label, v, f, col, rough, vcolors = entry
        if vcolors is None:
            vcolors = np.tile(np.asarray(col, dtype=float), (len(v), 1))

        shade = curvature_ao(v, f, strength=0.26)
        if label == "plate" and occluders is not None:
            shade = shade * contact_shadow(v, occluders, radius=13.0, strength=0.45)
        entry[5] = np.clip(vcolors * shade[:, None], 0.0, 1.0)


if __name__ == "__main__":
    build_glb()
