"""Generic fast-food packaging: clamshell box, fries carton, fries.

Deliberately unbranded. This is plain packaging geometry - no logos, no
wordmarks, no trade dress. Apply your own artwork as a texture downstream if
you have the rights to it.

Unlike the chicken, all of this is genuinely CAD-shaped: tapered lofts, a
constant-thickness shell, a slanted trim cut and a chamfered prism. build123d
handles it exactly, and the STEP output is the real artifact.

Units are millimetres, Z up. Each part is returned resting on Z=0 and centred
in XY unless noted.
"""

from __future__ import annotations

import math
import random

from build123d import (
    Align,
    Box,
    BuildPart,
    BuildSketch,
    Location,
    Mode,
    Plane,
    Pos,
    RectangleRounded,
    Rot,
    chamfer,
    loft,
)

# --- clamshell ---------------------------------------------------------------
BOX_BOTTOM = (230.0, 168.0, 11.0)   # length, width, corner radius
BOX_TOP = (256.0, 194.0, 19.0)
BASE_HEIGHT = 62.0
LID_HEIGHT = 54.0
CARD_T = 1.6

# --- fries carton ------------------------------------------------------------
CARTON_BOTTOM = (56.0, 30.0, 5.0)
CARTON_TOP = (94.0, 48.0, 9.0)
CARTON_HEIGHT = 108.0
CARTON_T = 1.3
CARTON_SLANT = 26.0                 # degrees off horizontal at the mouth


def _tapered_shell(bottom, top, height, thickness, floor=True):
    """A lofted tapered tub with constant-ish wall thickness, open at the top."""
    bl, bw, br = bottom
    tl, tw, tr = top

    with BuildPart() as part:
        with BuildSketch(Plane.XY):
            RectangleRounded(bl, bw, br)
        with BuildSketch(Plane.XY.offset(height)):
            RectangleRounded(tl, tw, tr)
        loft()

        z0 = thickness if floor else -1.0
        with BuildSketch(Plane.XY.offset(z0)):
            RectangleRounded(bl - 2 * thickness, bw - 2 * thickness, max(br - thickness, 0.5))
        with BuildSketch(Plane.XY.offset(height + 1.0)):
            RectangleRounded(tl - 2 * thickness, tw - 2 * thickness, max(tr - thickness, 0.5))
        loft(mode=Mode.SUBTRACT)

    return part.part


def make_box_base():
    return _tapered_shell(BOX_BOTTOM, BOX_TOP, BASE_HEIGHT, CARD_T)


def make_box_lid():
    return _tapered_shell(BOX_BOTTOM, BOX_TOP, LID_HEIGHT, CARD_T)


def make_carton():
    """Fries scoop: tapered tub with the mouth trimmed on a slant."""
    tub = _tapered_shell(CARTON_BOTTOM, CARTON_TOP, CARTON_HEIGHT, CARTON_T)

    # Trim the mouth: a large block, tilted about X, subtracted from the top.
    knife = Box(400.0, 400.0, 300.0, align=(Align.CENTER, Align.CENTER, Align.MIN))
    knife = Pos(0, 0, CARTON_HEIGHT - 16.0) * (Rot(CARTON_SLANT, 0, 0) * knife)
    return (tub - knife).clean()


def make_fry(length=78.0, thickness=9.0, taper=0.82, chamfer_size=1.4):
    """One chip: a slightly tapered rectangular prism with eased edges."""
    with BuildPart() as fry:
        with BuildSketch(Plane.XY):
            RectangleRounded(thickness, thickness, 1.2)
        with BuildSketch(Plane.XY.offset(length)):
            RectangleRounded(thickness * taper, thickness * taper, 1.0)
        loft()
        try:
            chamfer(fry.edges().group_by()[0], chamfer_size)
            chamfer(fry.edges().group_by()[-1], chamfer_size)
        except Exception:
            pass
    return fry.part


def fry_cluster(count=14, seed=5, spread_x=30.0, spread_y=14.0, base_z=44.0):
    """A handful of chips standing in the carton, leaning at varied angles.

    Returns [(solid, label)] already positioned in the carton's own frame.
    """
    rng = random.Random(seed)
    out = []
    for i in range(count):
        length = rng.uniform(62.0, 92.0)
        thickness = rng.uniform(7.6, 10.4)
        fry = make_fry(length, thickness)

        lean_x = rng.uniform(-16.0, 16.0)
        lean_y = rng.uniform(-13.0, 13.0)
        spin = rng.uniform(0.0, 90.0)
        fry = Rot(lean_y, lean_x, spin) * fry

        x = rng.uniform(-spread_x, spread_x)
        y = rng.uniform(-spread_y, spread_y)
        z = base_z - rng.uniform(0.0, 16.0)
        out.append((Pos(x, y, z) * fry, f"fry_{i + 1:02d}"))
    return out
