"""Render a set of meshes to a PNG, for judging food models while iterating.

The CAD snapshot tool only accepts STEP, and the interesting part of these
models (the roughened crust) exists only after tessellation - so it cannot be
reviewed that way. This inlines the meshes into a throwaway three.js page and
screenshots it with the Chromium that is already installed for Playwright.

    from tools.preview import render
    render([{ "name": "thigh", "verts": v, "faces": f, "color": (0.72,0.42,0.13) }],
           "render/thigh.png")
"""

from __future__ import annotations

import base64
import json
import struct
import tempfile
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
THREE = HERE.parent.parent / "hardware" / "cad" / "tools" / "vendor" / "three.min.js"

PAGE = """<!doctype html><html><head><meta charset="utf-8"><style>
html,body{margin:0;height:100%%;background:%(bg)s;overflow:hidden}canvas{display:block}
</style></head><body><script>%(three)s</script><script>
const PRIMS = %(prims)s;
const BUF = Uint8Array.from(atob("%(blob)s"), c => c.charCodeAt(0)).buffer;
const W = %(w)d, H = %(h)d;

const renderer = new THREE.WebGLRenderer({antialias:true});
renderer.setSize(W,H); document.body.appendChild(renderer.domElement);
renderer.setClearColor(new THREE.Color("%(bg)s"), 1);

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(38, W/H, 1, 20000);
camera.up.set(0,0,1);

scene.add(new THREE.HemisphereLight(0xffffff, 0x604430, 0.72));
const key = new THREE.DirectionalLight(0xfff3e0, 0.95); key.position.set(-300,-500,700); scene.add(key);
const rim = new THREE.DirectionalLight(0xffffff, 0.35); rim.position.set(500,400,200); scene.add(rim);

const box = new THREE.Box3();
for (const p of PRIMS) {
  const pos = new Float32Array(BUF, p.posOffset, p.posCount*3);
  const idx = new Uint32Array(BUF, p.idxOffset, p.idxCount);
  const g = new THREE.BufferGeometry();
  g.setAttribute("position", new THREE.BufferAttribute(pos,3));
  g.setIndex(new THREE.BufferAttribute(idx,1));
  if (p.colOffset !== null && p.colOffset !== undefined) {
    const col = new Float32Array(BUF, p.colOffset, p.colCount*3);
    g.setAttribute("color", new THREE.BufferAttribute(col,3));
  }
  g.computeVertexNormals();
  // When vertex colours are present they carry the whole colour. three.js
  // MULTIPLIES the material colour into them, so it has to be white here or
  // the preview shows something darker and more saturated than the GLB, whose
  // baseColorFactor is set to white for exactly the same reason.
  const hasVC = (p.colOffset !== null && p.colOffset !== undefined);
  const m = new THREE.MeshStandardMaterial({
    color: hasVC ? new THREE.Color(1,1,1)
                 : new THREE.Color(p.color[0],p.color[1],p.color[2]),
    roughness:p.roughness!==undefined?p.roughness:0.78, metalness:0.02,
    side:THREE.DoubleSide, flatShading:!!p.flat,
    vertexColors: hasVC
  });
  const mesh = new THREE.Mesh(g,m); scene.add(mesh);
  box.expandByObject(mesh);
}

const size = box.getSize(new THREE.Vector3());
const c = box.getCenter(new THREE.Vector3());
const radius = Math.max(size.length()*0.5, 10);
const dist = radius / Math.sin((38*Math.PI/180)/2) * 0.92;
const dir = new THREE.Vector3(%(dir)s).normalize();
camera.position.copy(c.clone().addScaledVector(dir, dist));
camera.lookAt(c);
camera.near = dist/200; camera.far = dist*10; camera.updateProjectionMatrix();

renderer.render(scene,camera);
window.__ready = true;
</script></body></html>"""


def _pack(primitives):
    blob = bytearray()
    meta = []
    for p in primitives:
        verts = np.asarray(p["verts"], dtype=np.float32)
        faces = np.asarray(p["faces"], dtype=np.uint32).reshape(-1)
        pos_bytes = verts.tobytes()
        idx_bytes = faces.tobytes()
        vcol = p.get("vcolors")
        vcol_bytes = b""
        if vcol is not None:
            vcol_bytes = np.asarray(vcol, dtype=np.float32).tobytes()
        meta.append({
            "colOffset": (len(blob) + len(pos_bytes) + len(idx_bytes)) if vcol is not None else None,
            "colCount": len(verts) if vcol is not None else 0,
            "name": p.get("name", "part"),
            "color": list(p.get("color", (0.7, 0.7, 0.7))),
            "roughness": p.get("roughness", 0.78),
            "flat": bool(p.get("flat", False)),
            "posOffset": len(blob), "posCount": len(verts),
            "idxOffset": len(blob) + len(pos_bytes), "idxCount": len(faces),
        })
        blob += pos_bytes + idx_bytes + vcol_bytes
        while len(blob) % 4:
            blob += b"\x00"
    return bytes(blob), meta


def render(primitives, out_png, width=1200, height=900, direction=(0.7, -1.0, 0.55),
           background="#EFE7DC"):
    from playwright.sync_api import sync_playwright

    blob, meta = _pack(primitives)
    html = PAGE % {
        "three": THREE.read_text(),
        "prims": json.dumps(meta),
        "blob": base64.b64encode(blob).decode(),
        "w": width, "h": height,
        "dir": ",".join(str(v) for v in direction),
        "bg": background,
    }
    tmp = Path(tempfile.mkdtemp()) / "preview.html"
    tmp.write_text(html)

    out = Path(out_png)
    out.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--use-gl=swiftshader", "--enable-unsafe-swiftshader"])
        page = browser.new_page(viewport={"width": width, "height": height})
        page.goto(tmp.as_uri())
        page.wait_for_function("window.__ready === true", timeout=60000)
        page.wait_for_timeout(400)
        page.screenshot(path=str(out))
        browser.close()
    return out
