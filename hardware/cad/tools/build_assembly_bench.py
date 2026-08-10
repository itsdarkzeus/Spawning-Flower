#!/usr/bin/env python3
"""Build the self-contained assembly bench page from the CAD assembly.

Tessellates every body in attendance_capture_point.step, packs the meshes into
one binary blob, and inlines that blob plus three.js into
`assembly_bench_template.html` to produce `assembly_bench.html`.

The output has to run with no network access at all (artifact pages are served
under a strict CSP that blocks every external host), so nothing may be left as
a <script src> or a fetch - it all gets inlined.

Usage, from hardware/cad:

    python tools/build_assembly_bench.py

Third-party: three.js r128 and its OrbitControls example, MIT licensed,
downloaded on first run and cached in tools/vendor/.
"""

from __future__ import annotations

import base64
import json
import struct
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
CAD = HERE.parent
VENDOR = HERE / "vendor"

STEP = CAD / "attendance_capture_point.step"
TEMPLATE = HERE / "assembly_bench_template.html"
OUTPUT = CAD / "assembly_bench.html"

THREE_VERSION = "0.128.0"
DEPS = {
    "three.min.js": f"https://unpkg.com/three@{THREE_VERSION}/build/three.min.js",
    "OrbitControls.js": f"https://unpkg.com/three@{THREE_VERSION}/examples/js/controls/OrbitControls.js",
}

# Mesh density. Looser than the CAD default because this is a web viewer, not a
# manufacturing artifact - the STEP remains the source of truth.
TOLERANCE = 0.15
ANGULAR_TOLERANCE = 0.4


def fetch_deps() -> dict[str, str]:
    VENDOR.mkdir(parents=True, exist_ok=True)
    out = {}
    for name, url in DEPS.items():
        path = VENDOR / name
        if not path.exists():
            print(f"  downloading {name} ...")
            with urllib.request.urlopen(url, timeout=60) as response:
                path.write_bytes(response.read())
        out[name] = path.read_text()
    return out


def leaves_of(shape):
    found = []

    def walk(node):
        for child in node.children:
            if child.children:
                walk(child)
            else:
                found.append(child)

    walk(shape)
    return found


def pack(shape):
    """Return (blob, metadata) with each body's positions and indices."""
    blob = bytearray()
    meta = []

    for leaf in leaves_of(shape):
        verts, tris = leaf.tessellate(TOLERANCE, ANGULAR_TOLERANCE)

        positions = bytearray()
        for v in verts:
            positions += struct.pack("<fff", v.X, v.Y, v.Z)
        indices = bytearray()
        for t in tris:
            indices += struct.pack("<III", *t)

        box = leaf.bounding_box()
        meta.append(
            {
                "name": leaf.label,
                "posOffset": len(blob),
                "posCount": len(verts),
                "idxOffset": len(blob) + len(positions),
                "idxCount": len(tris) * 3,
                "center": [round(box.center().X, 2), round(box.center().Y, 2), round(box.center().Z, 2)],
                "size": [round(box.size.X, 2), round(box.size.Y, 2), round(box.size.Z, 2)],
            }
        )
        blob += positions + indices
        print(f"  {leaf.label:<12} verts={len(verts):6d} tris={len(tris):6d}")

    return bytes(blob), meta


def main() -> int:
    if not STEP.exists():
        print(f"missing {STEP}; run scripts/step on attendance_capture_point.py first")
        return 1

    from build123d import import_step

    print("tessellating ...")
    blob, meta = pack(import_step(str(STEP)))
    print(f"  blob {len(blob) / 1024:.0f} KiB")

    print("resolving three.js ...")
    deps = fetch_deps()

    html = TEMPLATE.read_text()
    replacements = {
        "/*__THREE__*/": deps["three.min.js"],
        "/*__ORBIT__*/": deps["OrbitControls.js"],
        "/*__PARTS__*/": json.dumps(meta),
        "/*__MESH__*/": base64.b64encode(blob).decode(),
    }
    for token, value in replacements.items():
        if token not in html:
            print(f"template is missing placeholder {token}")
            return 1
        html = html.replace(token, value)

    OUTPUT.write_text(html)
    print(f"wrote {OUTPUT} ({len(html) / 1e6:.2f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
