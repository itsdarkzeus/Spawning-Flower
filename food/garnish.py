"""Garnishes and sauces for the plated fish: leeks, tomatoes, herbs, smears.

Everything here is a lofted CAD core, built from the same section-stack pattern
as the fillet. What varies is how each one is finished in the mesh stage:

  leeks     grain along the stalk, like the fillet but tighter
  tomatoes  soft low-frequency slump, no fine detail - roasted skin is smooth
  sauces    streaks running ALONG the smear, from the drag of a spoon

That last one is why `mesh_kit.roughen` grew an `axis_scale`. A sauce smear's
comb lines are the single most recognisable thing about it, and isotropic noise
renders them as generic lumpiness.

Units are millimetres, Z up. Parts rest on Z=0 and are centred in XY unless
noted, so the assembly only has to place them.
"""

from __future__ import annotations

import math

from build123d import (
    Align,
    Box,
    BuildPart,
    BuildSketch,
    Circle,
    Ellipse,
    Locations,
    Plane,
    Pos,
    Rot,
    Vector,
    loft,
)


# --------------------------------------------------------------------------
# shared helper
# --------------------------------------------------------------------------

def lofted_lobe(sections, length, flatten=None):
    """Loft a section stack along Z, then lay it down along X.

    `sections` are (length fraction, half-width, half-height, lateral lean).
    `flatten` slices that much off the underside so the part sits flat.
    """
    with BuildPart() as core:
        for frac, half_w, half_h, lean in sections:
            with BuildSketch(Plane.XY.offset(frac * length)):
                with Locations((lean, 0.0)):
                    Ellipse(half_w, half_h)
        loft()

    piece = Rot(90.0, 0.0, 0.0) * (Rot(0.0, 90.0, 0.0) * core.part)

    if flatten:
        box = piece.bounding_box()
        knife = Box(4000.0, 2000.0, 900.0, align=(Align.CENTER, Align.CENTER, Align.MAX))
        piece = piece - Pos(0.0, 0.0, box.min.Z + flatten) * knife

    box = piece.bounding_box()
    return Pos(-box.center().X, -box.center().Y, -box.min.Z) * piece


# --------------------------------------------------------------------------
# charred leek / spring onion batons
# --------------------------------------------------------------------------

LEEK_SECTIONS = [
    (0.00, 5.4, 5.0, 0.0),
    (0.14, 7.6, 7.0, 0.6),
    (0.40, 8.4, 7.8, 1.2),
    (0.68, 8.0, 7.4, 0.8),
    (0.88, 6.8, 6.2, -0.4),
    (1.00, 4.6, 4.2, -1.2),
]


def make_leek(length=126.0, split_at=0.78):
    """A halved leek baton, flat side down.

    Returns (green_part, pale_part). Real leeks go pale towards the root, and
    with one flat colour per mesh the only way to show that is to cut the solid
    in two and give each half its own material.
    """
    baton = lofted_lobe(LEEK_SECTIONS, length, flatten=3.0)
    box = baton.bounding_box()
    cut_x = box.min.X + (box.max.X - box.min.X) * split_at

    knife = Box(2000.0, 400.0, 400.0, align=(Align.MIN, Align.CENTER, Align.CENTER))
    beyond = Pos(cut_x, 0.0, 0.0) * knife
    return (baton - beyond), (baton & beyond)


# --------------------------------------------------------------------------
# rolled leek curl
# --------------------------------------------------------------------------

def make_leek_curl(turns=1.5, r_start=18.0, r_end=7.0, rise=10.0,
                   ribbon_w=4.2, ribbon_t=1.0, steps=40):
    """A thin ribbon rolled into a spiral.

    Built as a loft through sections placed along a computed spiral rather than
    a sweep: each section sits on its own plane, normal to the local tangent,
    which keeps the ribbon's flat face oriented correctly all the way round.

    Two things have to hold or the loft self-intersects and the curl turns into
    a knot: the radial pitch ((r_start - r_end) / turns) must exceed the ribbon
    THICKNESS, and the section plane needs an explicit vertical x_dir so the
    ribbon stands on edge instead of lying flat and colliding with its own
    neighbouring coil.
    """
    pitch = abs(r_start - r_end) / max(turns, 1e-6)
    if pitch <= 2.0 * ribbon_t:
        raise ValueError(
            f"spiral pitch {pitch:.1f} mm is too tight for a {2 * ribbon_t:.1f} mm "
            "ribbon; raise r_start, lower r_end, or use fewer turns"
        )

    sections = []
    for i in range(steps + 1):
        t = i / steps
        theta = t * turns * math.tau
        radius = r_start + (r_end - r_start) * t
        centre = Vector(radius * math.cos(theta), radius * math.sin(theta), rise * t)

        # Tangent of the spiral at this station.
        d_theta = turns * math.tau
        dr = r_end - r_start
        tangent = Vector(
            dr * math.cos(theta) - radius * math.sin(theta) * d_theta,
            dr * math.sin(theta) + radius * math.cos(theta) * d_theta,
            rise,
        )
        sections.append((centre, tangent))

    with BuildPart() as curl:
        for centre, tangent in sections:
            with BuildSketch(Plane(origin=centre, z_dir=tangent, x_dir=(0.0, 0.0, 1.0))):
                Ellipse(ribbon_w, ribbon_t)
        loft()

    box = curl.part.bounding_box()
    return Pos(-box.center().X, -box.center().Y, -box.min.Z) * curl.part


# --------------------------------------------------------------------------
# blistered cherry tomatoes
# --------------------------------------------------------------------------

TOMATO_SECTIONS = [
    (0.00,  4.0,  3.4, 0.0),
    (0.16, 10.0,  8.6, 0.0),
    (0.40, 13.2, 11.4, 0.0),
    (0.62, 13.4, 11.6, 0.0),
    (0.84,  9.8,  8.4, 0.0),
    (1.00,  4.2,  3.6, 0.0),
]


def make_tomato(length=26.0):
    """A roasted cherry tomato: near-spherical, slightly slumped, flat-based."""
    return lofted_lobe(TOMATO_SECTIONS, length, flatten=2.2)


# --------------------------------------------------------------------------
# micro herb leaves
# --------------------------------------------------------------------------

LEAF_SECTIONS = [
    (0.00, 0.9, 0.30, 0.0),
    (0.22, 3.6, 0.72, 0.3),
    (0.50, 4.6, 0.86, 0.0),
    (0.78, 3.4, 0.68, -0.3),
    (1.00, 0.8, 0.26, -0.6),
]


def make_leaf(length=15.0):
    return lofted_lobe(LEAF_SECTIONS, length)


# --------------------------------------------------------------------------
# sauces
# --------------------------------------------------------------------------

SMEAR_SECTIONS = [
    (0.00,  4.0, 0.55, 0.0),
    (0.18, 14.0, 1.60, 1.5),
    (0.42, 22.0, 2.70, 1.0),
    (0.66, 26.0, 3.30, -1.0),
    (0.86, 21.0, 2.40, -2.5),
    (1.00, 11.0, 1.10, -3.5),
]

DOLLOP_SECTIONS = [
    (0.00,  6.0, 0.7, 0.0),
    (0.22, 21.0, 2.6, 0.0),
    (0.50, 26.0, 3.6, 0.0),
    (0.78, 22.0, 2.8, 0.0),
    (1.00, 10.0, 1.0, 0.0),
]


def make_smear(length=152.0):
    """Red pepper smear: a tapered lens, flat on the plate."""
    return lofted_lobe(SMEAR_SECTIONS, length, flatten=0.01)


def make_dollop(length=66.0):
    """Herb oil puddle: rounder and shallower than the smear."""
    return lofted_lobe(DOLLOP_SECTIONS, length, flatten=0.01)


def comb(verts, faces, seed=5, amplitude=0.55, frequency=0.30):
    """Streaks running along the smear, as if dragged with the back of a spoon."""
    from mesh_kit import roughen

    return roughen(verts, faces, amplitude=amplitude, frequency=frequency,
                   octaves=3, seed=seed, bias=0.0, axis_scale=(0.10, 1.0, 1.0))
