"""Mesh-side helpers: tessellate CAD solids, roughen them, write a GLB.

Why this exists
    A B-rep kernel is the right tool for the *form* of these models - the
    clamshell box, the fries carton and the chicken's underlying mass are all
    lofts, shells and tapers, and they come out of build123d exactly. It is the
    wrong tool for *surface detail*: OCCT has no displacement and no noise, and
    faking breading by fusing hundreds of spheres either takes minutes or
    returns a null shape once the arguments pile up.

    So the split is: CAD owns the shape, the mesh stage owns the texture. The
    STEP files remain the honest CAD artifact; the crust exists only in the
    exported mesh, and that is stated in the README rather than glossed over.

Everything here is numpy plus the standard library - no extra dependencies.
"""

from __future__ import annotations

import base64
import json
import struct
from pathlib import Path

import numpy as np


# --------------------------------------------------------------------------
# tessellation
# --------------------------------------------------------------------------

def tessellate(shape, tolerance: float = 0.25, angular: float = 0.3):
    """Return (vertices Nx3, faces Mx3) for a build123d shape, in millimetres."""
    verts, tris = shape.tessellate(tolerance, angular)
    v = np.array([[p.X, p.Y, p.Z] for p in verts], dtype=np.float64)
    f = np.array(tris, dtype=np.int32)
    return v, f


def weld(verts, faces, decimals: int = 4):
    """Merge coincident vertices so normals average smoothly across facets."""
    keys = np.round(verts, decimals)
    _, index, inverse = np.unique(keys, axis=0, return_index=True, return_inverse=True)
    return verts[index], inverse[faces]


def subdivide(verts, faces, levels: int = 1):
    """Midpoint 1-to-4 split, repeated.

    Displacement can only move existing vertices, so the mesh has to carry
    enough of them to resolve the detail before any noise is applied. A CAD
    tessellation of a smooth loft is far too sparse for millimetre-scale crust.
    """
    for _ in range(max(0, levels)):
        edge_mid = {}
        new_verts = list(verts)

        def mid(a, b):
            key = (a, b) if a < b else (b, a)
            hit = edge_mid.get(key)
            if hit is None:
                hit = len(new_verts)
                new_verts.append((verts[a] + verts[b]) * 0.5)
                edge_mid[key] = hit
            return hit

        new_faces = []
        for a, b, c in faces:
            ab, bc, ca = mid(a, b), mid(b, c), mid(c, a)
            new_faces += [[a, ab, ca], [b, bc, ab], [c, ca, bc], [ab, bc, ca]]

        verts = np.array(new_verts, dtype=np.float64)
        faces = np.array(new_faces, dtype=np.int32)
    return verts, faces


def vertex_normals(verts, faces):
    """Area-weighted vertex normals."""
    a, b, c = verts[faces[:, 0]], verts[faces[:, 1]], verts[faces[:, 2]]
    face_n = np.cross(b - a, c - a)          # length is 2 * area, so this weights
    out = np.zeros_like(verts)
    for col in range(3):
        np.add.at(out, faces[:, col], face_n)
    length = np.linalg.norm(out, axis=1, keepdims=True)
    length[length == 0] = 1.0
    return out / length


# --------------------------------------------------------------------------
# value noise
# --------------------------------------------------------------------------

def _hash01(ix, iy, iz, seed):
    """Deterministic pseudo-random scalar in [0,1) per integer lattice point."""
    h = (ix * 374761393 + iy * 668265263 + iz * 2147483647 + seed * 1274126177)
    h = (h ^ (h >> 13)) * 1274126177
    h = h ^ (h >> 16)
    return (h & 0xFFFFFF) / float(0x1000000)


def value_noise(points, frequency, seed):
    """Trilinearly interpolated value noise sampled at `points` (Nx3)."""
    p = points * frequency
    i = np.floor(p).astype(np.int64)
    f = p - i
    # smoothstep for continuous first derivative
    w = f * f * (3.0 - 2.0 * f)

    out = np.zeros(len(points))
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                corner = _hash01(i[:, 0] + dx, i[:, 1] + dy, i[:, 2] + dz, seed)
                weight = (
                    (w[:, 0] if dx else 1 - w[:, 0])
                    * (w[:, 1] if dy else 1 - w[:, 1])
                    * (w[:, 2] if dz else 1 - w[:, 2])
                )
                out += corner * weight
    return out


def fbm(points, octaves=4, frequency=0.06, lacunarity=2.1, gain=0.52, seed=1):
    """Fractal sum of value noise, returned roughly in [-1, 1]."""
    total = np.zeros(len(points))
    amp, freq, norm = 1.0, frequency, 0.0
    for o in range(octaves):
        total += amp * (value_noise(points, freq, seed + o * 101) - 0.5) * 2.0
        norm += amp
        amp *= gain
        freq *= lacunarity
    return total / max(norm, 1e-9)


def roughen(verts, faces, amplitude=2.4, frequency=0.075, octaves=4, seed=1, bias=0.0):
    """Push vertices along their normals by fractal noise.

    `bias` shifts the noise so the surface swells outward on average, which is
    what a batter coating actually does to the silhouette.
    """
    normals = vertex_normals(verts, faces)
    n = fbm(verts, octaves=octaves, frequency=frequency, seed=seed) + bias
    return verts + normals * (n * amplitude)[:, None]


def crust(verts, faces, seed=1, mass=3.0, mass_freq=0.030, grain=1.5, grain_freq=0.16):
    """Two-scale breading: coarse lumps of batter, then a fine crumb on top.

    A single noise scale reads as either a dented balloon or as sandpaper.
    Fried chicken needs both - an irregular overall mass and a crisp small
    crumb sitting on it.
    """
    v = roughen(verts, faces, amplitude=mass, frequency=mass_freq,
                octaves=3, seed=seed, bias=0.25)
    v = roughen(v, faces, amplitude=grain, frequency=grain_freq,
                octaves=4, seed=seed + 977, bias=0.15)
    return v


# --------------------------------------------------------------------------
# GLB writer
# --------------------------------------------------------------------------

def srgb_to_linear(c):
    """Convert one sRGB channel (0-1) to linear.

    glTF defines baseColorFactor in LINEAR space, but palettes are almost
    always picked in sRGB - the value you would type into a colour picker.
    Writing sRGB values straight into baseColorFactor makes every material
    render washed out, because the viewer then applies its own linear->sRGB
    transfer on top: a 0.78 red displays at 0.90, so a deep red arrives pink.
    """
    c = float(c)
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _pad(buf: bytearray, alignment: int = 4, fill: bytes = b"\x00"):
    while len(buf) % alignment:
        buf += fill


def write_glb(path, primitives, y_up: bool = True, scale: float = 0.001):
    """Write a binary glTF 2.0 file.

    `primitives` is a list of dicts: name, verts (Nx3 mm), faces (Mx3),
    color (r,g,b) 0-1 **in sRGB**, and optional roughness / metallic.
    Colours are converted to linear on the way out, per the glTF spec.

    glTF convention is metres and Y-up, so millimetre Z-up CAD coordinates are
    converted here: scale by 0.001 and map (x, y, z) -> (x, z, -y).
    """
    bin_buf = bytearray()
    accessors, buffer_views, meshes, nodes, materials = [], [], [], [], []

    for prim in primitives:
        verts = np.asarray(prim["verts"], dtype=np.float64) * scale
        faces = np.asarray(prim["faces"], dtype=np.uint32)

        if y_up:
            verts = np.column_stack([verts[:, 0], verts[:, 2], -verts[:, 1]])

        normals = vertex_normals(verts, faces).astype(np.float32)
        pos = verts.astype(np.float32)
        idx = faces.reshape(-1).astype(np.uint32)

        # --- position accessor
        _pad(bin_buf)
        off = len(bin_buf)
        bin_buf += pos.tobytes()
        buffer_views.append({"buffer": 0, "byteOffset": off, "byteLength": pos.nbytes, "target": 34962})
        accessors.append({
            "bufferView": len(buffer_views) - 1, "componentType": 5126, "count": len(pos),
            "type": "VEC3",
            "min": pos.min(axis=0).tolist(), "max": pos.max(axis=0).tolist(),
        })
        pos_acc = len(accessors) - 1

        # --- normal accessor
        _pad(bin_buf)
        off = len(bin_buf)
        bin_buf += normals.tobytes()
        buffer_views.append({"buffer": 0, "byteOffset": off, "byteLength": normals.nbytes, "target": 34962})
        accessors.append({
            "bufferView": len(buffer_views) - 1, "componentType": 5126,
            "count": len(normals), "type": "VEC3",
        })
        nrm_acc = len(accessors) - 1

        # --- index accessor
        _pad(bin_buf)
        off = len(bin_buf)
        bin_buf += idx.tobytes()
        buffer_views.append({"buffer": 0, "byteOffset": off, "byteLength": idx.nbytes, "target": 34963})
        accessors.append({
            "bufferView": len(buffer_views) - 1, "componentType": 5125,
            "count": len(idx), "type": "SCALAR",
        })
        idx_acc = len(accessors) - 1

        # Palette entries are authored in sRGB; glTF wants linear.
        r, g, b = (srgb_to_linear(c) for c in prim["color"])
        materials.append({
            "name": prim["name"] + "_mat",
            "pbrMetallicRoughness": {
                "baseColorFactor": [r, g, b, 1.0],
                "metallicFactor": prim.get("metallic", 0.0),
                "roughnessFactor": prim.get("roughness", 0.75),
            },
            "doubleSided": prim.get("double_sided", True),
        })
        meshes.append({
            "name": prim["name"],
            "primitives": [{
                "attributes": {"POSITION": pos_acc, "NORMAL": nrm_acc},
                "indices": idx_acc,
                "material": len(materials) - 1,
            }],
        })
        nodes.append({"name": prim["name"], "mesh": len(meshes) - 1})

    gltf = {
        "asset": {"version": "2.0", "generator": "text-to-cad food kit"},
        "scene": 0,
        "scenes": [{"nodes": list(range(len(nodes)))}],
        "nodes": nodes,
        "meshes": meshes,
        "materials": materials,
        "accessors": accessors,
        "bufferViews": buffer_views,
        "buffers": [{"byteLength": len(bin_buf)}],
    }

    json_chunk = json.dumps(gltf, separators=(",", ":")).encode("utf8")
    while len(json_chunk) % 4:
        json_chunk += b" "
    _pad(bin_buf)

    total = 12 + 8 + len(json_chunk) + 8 + len(bin_buf)
    out = bytearray()
    out += struct.pack("<III", 0x46546C67, 2, total)
    out += struct.pack("<II", len(json_chunk), 0x4E4F534A) + json_chunk
    out += struct.pack("<II", len(bin_buf), 0x004E4942) + bytes(bin_buf)

    Path(path).write_bytes(bytes(out))
    return len(out)
