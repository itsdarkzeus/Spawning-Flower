"""Plated fish dish — full scene, STEP + GLB.

Follows the composition of the reference photo: a seared fillet laid diagonally
across a white coupe plate, a red pepper smear beneath it, a herb oil dollop to
the right, charred leek batons and a rolled leek curl to the left, two roasted
cherry tomatoes at the front, and micro herbs scattered through the middle.

Same two-stage pipeline as the meal box:

    CAD stage   plate, fillet mass, leeks, tomatoes, sauce bodies -> STEP
    mesh stage  sear, grain, slump and comb streaks -> GLB

The plate is the one part that gets NO displacement at either stage. Glazed
porcelain is genuinely that smooth, and noise only makes it look cheap.

Coordinate frame: plate centred on the origin, resting on Z=0, +Z up. In plan
view +Y is towards the top of the reference photo.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from build123d import Color, Pos, Rot

from cadpy.assembly import AssemblyHelper

import garnish as G
import shading
from fish import make_fillet, sear
from mesh_kit import roughen, subdivide, tessellate, weld, write_glb
from plate import WELL_DEPTH, make_plate

HERE = Path(__file__).resolve().parent

# --- palette, sRGB (the writer converts to linear) --------------------------
COL_PLATE = (0.80, 0.80, 0.79)
COL_FISH = (0.70, 0.47, 0.23)
COL_LEEK = (0.29, 0.41, 0.15)
COL_LEEK_PALE = (0.87, 0.88, 0.74)
COL_CURL = (0.33, 0.50, 0.18)
COL_TOMATO = (0.66, 0.14, 0.10)
COL_SAUCE_RED = (0.76, 0.22, 0.07)
COL_SAUCE_GREEN = (0.48, 0.63, 0.24)
COL_HERB = (0.32, 0.50, 0.20)

# The plate's upper surface, sampled from the same control points the revolve
# uses. Garnishes are seated on it rather than all dropped to a single height,
# so nothing floats over the rise towards the rim or sinks into it.
_PLATE_PROFILE = [
    (0.0, WELL_DEPTH),
    (46.0, WELL_DEPTH + 0.4),
    (86.0, WELL_DEPTH + 2.6),
    (114.0, WELL_DEPTH + 9.0),
]


def plate_height(x: float, y: float) -> float:
    r = float(np.hypot(x, y))
    xs = [p[0] for p in _PLATE_PROFILE]
    zs = [p[1] for p in _PLATE_PROFILE]
    return float(np.interp(r, xs, zs))


def seat(x: float, y: float, spin: float = 0.0, sink: float = 0.0):
    """Location that drops a part onto the plate surface at (x, y)."""
    return Pos(x, y, plate_height(x, y) - sink) * Rot(0.0, 0.0, spin)


# --- layout ------------------------------------------------------------------
LEEK_PLACEMENTS = [
    (-58.0, 22.0, 61.0),
    (-45.0, 2.0, 58.0),
    (-33.0, -20.0, 54.0),
]

# Micro herbs are lifted slightly (negative sink) so they rest on top of the
# sauce and the fillet instead of vanishing inside them.
# The fillet runs from about (-19, -78) to (47, 86) and is ~58 mm wide, so
# anything dropped inside that band disappears under it. These sit clear of it,
# except the last one, lifted to rest ON the fillet as in the reference.
HERB_PLACEMENTS = [
    (62.0, 12.0, -30.0, 1.4),
    (69.0, 2.0, 45.0, 1.4),
    (58.0, -26.0, 20.0, 4.4),
    (52.0, -34.0, -18.0, 4.0),
    (-48.0, -46.0, 26.0, 1.4),
    (-40.0, -54.0, -6.0, 1.4),
    (-58.0, 30.0, 66.0, 1.4),
    (22.0, 30.0, 52.0, 13.0),
    (30.0, 12.0, -24.0, 13.0),
]


def _bodies():
    """Every solid in the scene, already placed. [(label, solid, colour)]"""
    out = [("plate", make_plate(), COL_PLATE)]

    # Sauces first - they sit under everything and are partly hidden.
    out.append(("sauce_red", seat(2.0, 8.0, 26.0, sink=0.4) * G.make_smear(), COL_SAUCE_RED))
    out.append(("sauce_green", seat(58.0, -26.0, -14.0, sink=0.3) * G.make_dollop(42.0), COL_SAUCE_GREEN))

    for i, (x, y, spin) in enumerate(LEEK_PLACEMENTS, start=1):
        out.append((f"leek_{i}", seat(x, y, spin) * G.make_leek(118.0 + 9.0 * i), COL_LEEK))

    out.append(("leek_curl", seat(-27.0, -8.0, 0.0, sink=-1.0) * G.make_leek_curl(), COL_CURL))

    out.append(("tomato_1", seat(-44.0, -54.0) * G.make_tomato(), COL_TOMATO))
    out.append(("tomato_2", seat(-19.0, -63.0) * G.make_tomato(length=24.0), COL_TOMATO))

    # The fillet goes on last so it overlaps the sauce and the leek tips.
    out.append(("fish_fillet", seat(14.0, 4.0, 68.0, sink=1.0) * make_fillet(), COL_FISH))

    for i, (x, y, spin, lift) in enumerate(HERB_PLACEMENTS, start=1):
        out.append((f"herb_{i}", seat(x, y, spin, sink=-lift) * G.make_leaf(11.5), COL_HERB))

    return out


def gen_step():
    """CAD artifact: every body, smooth, before any surface texture."""
    asm = AssemblyHelper("plated_fish")
    for label, solid, col in _bodies():
        asm.add(solid, label, color=Color(*col))
    return asm.build()


def build_glb(path=None, preview=None):
    path = Path(path or HERE / "plated_fish.glb")
    prims = []

    for index, (label, solid, col) in enumerate(_bodies()):
        rough = 0.55

        if label == "plate":
            # No displacement at all: glazed porcelain is smooth, and noise here
            # reads as a cheap ceramic rather than a restaurant plate.
            v, f = weld(*tessellate(solid, 0.12, 0.12))
            rough = 0.14

        elif label == "fish_fillet":
            v, f = weld(*tessellate(solid, 0.16, 0.16))
            v, f = subdivide(v, f, 2)
            v = sear(v, f, seed=11)
            rough = 0.42

        elif label.startswith("leek"):
            v, f = weld(*tessellate(solid, 0.16, 0.16))
            v, f = subdivide(v, f, 1)
            v = roughen(v, f, amplitude=0.42, frequency=0.30, octaves=3,
                        seed=200 + index, bias=0.0, axis_scale=(0.16, 1.0, 1.0))
            rough = 0.46

        elif label.startswith("tomato"):
            v, f = weld(*tessellate(solid, 0.12, 0.14))
            v, f = subdivide(v, f, 1)
            # Roasted skin slumps in broad, soft folds - low frequency only.
            v = roughen(v, f, amplitude=1.15, frequency=0.075, octaves=2,
                        seed=300 + index, bias=0.0)
            rough = 0.26

        elif label.startswith("sauce"):
            v, f = weld(*tessellate(solid, 0.25, 0.25))
            v, f = subdivide(v, f, 2)
            v = G.comb(v, f, seed=500 + index,
                       amplitude=0.55 if label.endswith("green") else 0.95)
            rough = 0.30

        else:  # herbs
            v, f = weld(*tessellate(solid, 0.14, 0.16))
            rough = 0.44

        # Per-vertex colour. The plate is the one thing left flat: a glaze is
        # genuinely uniform, and variation on it reads as dirt.
        vcolors = None
        if label == "fish_fillet":
            vcolors = shading.fish(v, f, seed=11)
        elif label.startswith("leek_") and label != "leek_curl":
            vcolors = shading.leek(v, f, seed=31 + index)
        elif label == "leek_curl":
            vcolors = shading.leek(v, f, seed=37, length_axis=2)
        elif label.startswith("tomato"):
            vcolors = shading.tomato(v, f, seed=41 + index)
        elif label == "sauce_red":
            vcolors = shading.sauce(v, f, seed=51)
        elif label == "sauce_green":
            vcolors = shading.sauce(v, f, seed=57, base=(0.31, 0.43, 0.12),
                                    deep=(0.16, 0.25, 0.06), thin=(0.42, 0.54, 0.19))
        elif label.startswith("herb"):
            vcolors = shading.herb(v, f, seed=61 + index)

        prims.append({"name": label, "verts": v, "faces": f, "vcolors": vcolors,
                      "color": col, "roughness": rough, "metallic": 0.0})

    size = write_glb(path, prims)
    tris = sum(len(p["faces"]) for p in prims)
    print(f"GLB: {path}  {size / 1e6:.2f} MB  {len(prims)} meshes  {tris} triangles")

    if preview:
        from tools.preview import render
        render(prims, preview, width=1150, height=1150,
               direction=(0.02, -0.12, 1.0), background="#20242B")
        print("preview:", preview)

    return prims


if __name__ == "__main__":
    build_glb(preview=HERE / "render" / "plated_fish_top.png")
