"""Fast-food meal box — full scene, STEP + GLB.

Reproduces the arrangement of the reference photo: an open clamshell box with a
large piece of fried chicken and two smaller pieces in the tray, and a fries
carton leaning into the right-hand side.

Deliberately unbranded: no logos, no wordmarks, no trade dress anywhere in the
geometry or the materials.

Two-stage pipeline, for the reasons set out in mesh_kit.py:

    CAD stage   packaging and the chicken's underlying mass, exported to STEP
    mesh stage  breading and paper texture applied by displacement, exported
                to GLB

So the STEP holds smooth chicken cores and the GLB holds the crust. They are
not interchangeable, and that is intentional rather than an oversight.

Coordinate frame: origin at the centre of the box base, resting on Z=0, +Z up,
+Y towards the back of the box (the hinge side).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from build123d import Color, Location, Pos, Rot

from cadpy.assembly import AssemblyHelper

from chicken_piece import make_thigh, make_tender, make_wing
from mesh_kit import subdivide, tessellate, weld, roughen, write_glb
from packaging import (
    BASE_HEIGHT,
    LID_HEIGHT,
    CARD_T,
    fry_cluster,
    make_box_base,
    make_box_lid,
    make_carton,
)

HERE = Path(__file__).resolve().parent

# --- palette (linear-ish sRGB, no branding) ---------------------------------
COL_CARD = (0.94, 0.93, 0.905)
COL_CARTON = (0.78, 0.16, 0.14)
COL_CHICKEN = (0.76, 0.45, 0.16)
COL_CHICKEN_DARK = (0.70, 0.39, 0.13)
COL_FRY = (0.91, 0.78, 0.41)

# --- placement ---------------------------------------------------------------
HINGE_Y = 97.0
# Negative: a positive rotation about X swings the lid down through the table
# instead of up and back.
LID_OPEN_DEG = -104.0
FLOOR_Z = CARD_T

# Closed position first: the lid is flipped, so its rim lands on the base rim
# at BASE_HEIGHT and its body rises to BASE_HEIGHT + LID_HEIGHT. Then the whole
# thing swings about the hinge line running along X at (y=HINGE_Y, z=BASE_HEIGHT).
LID_CLOSED = Pos(0.0, 0.0, BASE_HEIGHT + LID_HEIGHT) * Rot(180.0, 0.0, 0.0)
LID_LOC = (
    Pos(0.0, HINGE_Y, BASE_HEIGHT)
    * Rot(LID_OPEN_DEG, 0.0, 0.0)
    * Pos(0.0, -HINGE_Y, -BASE_HEIGHT)
    * LID_CLOSED
)

# The tray tapers, so the usable footprint at floor level is a good deal
# smaller than the rim. Contents are placed against the FLOOR limits, with
# headroom left for the crust displacement pushing outward at export time.
THIGH_LOC = Pos(-40.0, 10.0, FLOOR_Z) * Rot(0.0, 0.0, 24.0)
WING_LOC = Pos(-46.0, -50.0, FLOOR_Z) * Rot(0.0, 0.0, 20.0)
TENDER_LOC = Pos(34.0, -50.0, FLOOR_Z) * Rot(0.0, 0.0, -14.0)
# Leaning further back would push the carton's mouth through the open lid.
CARTON_LOC = Pos(64.0, 2.0, FLOOR_Z) * Rot(-34.0, 0.0, -22.0)

# --- crust / texture settings ------------------------------------------------
CRUST = dict(mass=13.0, mass_freq=0.015, mid=6.0, mid_freq=0.050, grain=3.0, grain_freq=0.30)


def _crust(verts, faces, seed):
    v = roughen(verts, faces, amplitude=CRUST["mass"], frequency=CRUST["mass_freq"],
                octaves=3, seed=seed, bias=0.20)
    v = roughen(v, faces, amplitude=CRUST["mid"], frequency=CRUST["mid_freq"],
                octaves=3, seed=seed + 311, bias=0.10)
    v = roughen(v, faces, amplitude=CRUST["grain"], frequency=CRUST["grain_freq"],
                octaves=4, seed=seed + 977, bias=0.10)
    return v


def _bodies():
    """Every solid in the scene, already placed. [(label, solid, colour)]"""
    out = [
        ("box_base", make_box_base(), COL_CARD),
        ("box_lid", LID_LOC * make_box_lid(), COL_CARD),
        ("chicken_thigh", THIGH_LOC * make_thigh(), COL_CHICKEN),
        ("chicken_tender", TENDER_LOC * make_tender(), COL_CHICKEN_DARK),
        ("chicken_wing", WING_LOC * make_wing(), COL_CHICKEN),
        ("fries_carton", CARTON_LOC * make_carton(), COL_CARTON),
    ]
    for fry, label in fry_cluster():
        out.append((label, CARTON_LOC * fry, COL_FRY))
    return out


def gen_step():
    """CAD artifact: packaging plus the SMOOTH chicken cores."""
    asm = AssemblyHelper("meal_box")
    for label, solid, col in _bodies():
        asm.add(solid, label, color=Color(*col))
    return asm.build()


def build_glb(path=None, preview=None):
    """Mesh artifact: the same scene with crust and paper texture applied."""
    path = Path(path or HERE / "meal_box.glb")
    prims = []

    for index, (label, solid, col) in enumerate(_bodies()):
        if label.startswith("chicken"):
            v, f = weld(*tessellate(solid, 0.06, 0.10))
            v, f = subdivide(v, f, 2)
            v = _crust(v, f, seed=17 + index * 53)
            roughness = 0.52
        elif label.startswith(("box_", "fries_carton")):
            v, f = weld(*tessellate(solid, 0.2, 0.2))
            v, f = subdivide(v, f, 2)
            # Just enough wobble that the card does not read as injection-moulded.
            v = roughen(v, f, amplitude=0.45, frequency=0.05, octaves=2,
                        seed=400 + index, bias=0.0)
            roughness = 0.86
        else:
            v, f = weld(*tessellate(solid, 0.25, 0.3))
            v, f = subdivide(v, f, 1)
            v = roughen(v, f, amplitude=0.5, frequency=0.22, octaves=3,
                        seed=900 + index, bias=0.05)
            roughness = 0.68

        prims.append({
            "name": label, "verts": v, "faces": f,
            "color": col, "roughness": roughness, "metallic": 0.0,
        })

    size = write_glb(path, prims)
    tris = sum(len(p["faces"]) for p in prims)
    print(f"GLB: {path}  {size / 1e6:.2f} MB  {len(prims)} meshes  {tris} triangles")

    if preview:
        from tools.preview import render
        render(prims, preview, width=1400, height=1050, direction=(0.42, -1.0, 0.62))
        print("preview:", preview)

    return prims


if __name__ == "__main__":
    build_glb(preview=HERE / "render" / "meal_preview.png")
