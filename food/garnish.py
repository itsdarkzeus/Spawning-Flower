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

# Halved leek stalks are thin and flattened, roughly 11 mm across and 7 mm
# tall once the underside is sliced. An earlier version at 17 mm diameter read
# as cucumber.
LEEK_SECTIONS = [
    (0.00, 3.2, 2.6, 0.0),
    (0.14, 5.0, 3.9, 0.4),
    (0.40, 5.6, 4.3, 0.8),
    (0.68, 5.4, 4.1, 0.5),
    (0.88, 4.6, 3.5, -0.3),
    (1.00, 3.0, 2.4, -0.8),
]


def make_leek(length=126.0):
    """A halved leek baton, flat side down.

    One solid. An earlier version cut the baton in two so the pale root could
    have its own material, which was a workaround for having a single flat
    colour per mesh. With per-vertex colour the root gradient and the char
    bands both live in `shading.leek`, and the extra geometry is unnecessary.
    """
    return lofted_lobe(LEEK_SECTIONS, length, flatten=1.6)


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
    (0.00,  3.4,  3.0, 0.0),
    (0.16,  8.6,  7.6, 0.0),
    (0.40, 11.2, 10.0, 0.0),
    (0.62, 11.4, 10.2, 0.0),
    (0.84,  8.4,  7.4, 0.0),
    (1.00,  3.6,  3.2, 0.0),
]


def make_tomato(length=22.0):
    """A roasted cherry tomato: near-spherical, slightly slumped, flat-based."""
    return lofted_lobe(TOMATO_SECTIONS, length, flatten=2.2)


# --------------------------------------------------------------------------
# micro herb leaves
# --------------------------------------------------------------------------

# Purslane-style micro leaves: rounded, not pointed ovals.
# Flat and delicate. Earlier versions were thick enough to read as discs.
LEAF_SECTIONS = [
    (0.00, 1.2, 0.10, 0.0),
    (0.25, 4.4, 0.24, 0.2),
    (0.55, 5.0, 0.28, 0.0),
    (0.82, 3.8, 0.22, -0.2),
    (1.00, 1.0, 0.09, -0.4),
]


def make_leaf(length=13.0):
    return lofted_lobe(LEAF_SECTIONS, length)


# --------------------------------------------------------------------------
# sauces
# --------------------------------------------------------------------------

# Plated sauce is a thin film, 2-3 mm at most. Earlier versions stood 6.6 mm
# proud and read as a slab of jelly rather than something spooned on.
# A spooned smear is a film, not a pat. Under 1 mm at the tail, ~1.6 mm at the
# thickest, and it is draped onto the plate's curve in the assembly rather than
# sitting flat on a tangent plane.
SMEAR_SECTIONS = [
    (0.00,  6.0, 0.16, 0.0),
    (0.18, 17.0, 0.52, 1.5),
    (0.42, 26.0, 0.92, 1.0),
    (0.66, 29.0, 1.10, -1.0),
    (0.86, 23.0, 0.72, -2.5),
    (1.00, 11.0, 0.26, -3.5),
]

DOLLOP_SECTIONS = [
    (0.00,  5.0, 0.28, 0.0),
    (0.22, 17.0, 0.95, 0.0),
    (0.50, 21.0, 1.30, 0.0),
    (0.78, 17.0, 0.95, 0.0),
    (1.00,  8.0, 0.34, 0.0),
]


def make_smear(length=158.0):
    """Red pepper smear: a tapered lens, flat on the plate."""
    return lofted_lobe(SMEAR_SECTIONS, length, flatten=0.01)


def make_dollop(length=52.0):
    """Herb oil puddle: rounder and shallower than the smear."""
    return lofted_lobe(DOLLOP_SECTIONS, length, flatten=0.01)


def comb(verts, faces, seed=5, amplitude=0.16, frequency=0.40):
    """Streaks running along the smear, as if dragged with the back of a spoon."""
    from mesh_kit import roughen

    return roughen(verts, faces, amplitude=amplitude, frequency=frequency,
                   octaves=3, seed=seed, bias=0.0, axis_scale=(0.10, 1.0, 1.0))
