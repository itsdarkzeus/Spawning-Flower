"""Render an actual .glb file the way a real viewer renders it.

Why this exists
    `tools/preview.py` renders the in-memory meshes. That is fast to iterate on
    but it is NOT the deliverable, and it has now disagreed with the shipped
    file twice: once because glTF wants linear colour and the preview was fed
    sRGB, and once because both glTF and three.js MULTIPLY the material colour
    into vertex colours, which the preview was not doing. Both times the
    preview looked right and the file did not.

    So this loads the written .glb through THREE.GLTFLoader - the same path any
    viewer takes - and renders it under lighting rigs that approximate what a
    phone GLB viewer actually does. If it looks wrong here, it looks wrong on
    the user's device.

Usage:
    python tools/verify_glb.py plated_fish.glb --out render/verify --preset studio
"""

from __future__ import annotations

import argparse
import http.server
import socketserver
import threading
from pathlib import Path

HERE = Path(__file__).resolve().parent
VENDOR = HERE / "vendor"
THREE = HERE.parent.parent / "hardware" / "cad" / "tools" / "vendor" / "three.min.js"
LOADER = VENDOR / "GLTFLoader.js"

# Rigs approximating what consumer GLB viewers ship. "studio" is deliberately
# bright and frontal, which is the setting that shows up washed-out albedo.
PRESETS = {
    "studio": dict(hemi=0.95, hemiGround=0x9aa2ad, key=1.35, fill=0.75, rim=0.55, exposure=1.15, tone=False),
    "soft":   dict(hemi=0.70, hemiGround=0x8a8f96, key=0.70, fill=0.45, rim=0.30, exposure=1.00, tone=True),
    "outdoor": dict(hemi=0.60, hemiGround=0x6d7a55, key=1.80, fill=0.35, rim=0.45, exposure=1.10, tone=True),
}

PAGE = """<!doctype html><html><head><meta charset="utf-8"><style>
html,body{margin:0;height:100%%;background:%(bg)s;overflow:hidden}canvas{display:block}
</style></head><body><script>%(three)s</script><script>%(loader)s</script><script>
const W=%(w)d, H=%(h)d, P=%(preset)s;
const renderer = new THREE.WebGLRenderer({antialias:true});
renderer.setSize(W,H);
renderer.outputEncoding = THREE.sRGBEncoding;      // every glTF viewer does this
if (P.tone) { renderer.toneMapping = THREE.ACESFilmicToneMapping; }
renderer.toneMappingExposure = P.exposure;
renderer.setClearColor(new THREE.Color("%(bg)s"), 1);
document.body.appendChild(renderer.domElement);

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(34, W/H, 0.001, 100);
camera.up.set(0,1,0);                               // glTF is Y-up

scene.add(new THREE.HemisphereLight(0xffffff, P.hemiGround, P.hemi));
const key = new THREE.DirectionalLight(0xffffff, P.key); key.position.set(-0.5,1.0,0.75); scene.add(key);
const fill= new THREE.DirectionalLight(0xffffff, P.fill); fill.position.set(0.8,0.5,-0.4); scene.add(fill);
const rim = new THREE.DirectionalLight(0xffffff, P.rim);  rim.position.set(0.0,-0.4,-1.0); scene.add(rim);

new THREE.GLTFLoader().load("%(glb)s", g => {
  scene.add(g.scene);
  const box = new THREE.Box3().setFromObject(g.scene);
  const c = box.getCenter(new THREE.Vector3());
  const s = box.getSize(new THREE.Vector3());
  const d = s.length()*0.5/Math.sin((34*Math.PI/180)/2) * %(zoom)f;
  const dir = new THREE.Vector3(%(dir)s).normalize();
  camera.position.copy(c.clone().addScaledVector(dir, d));
  camera.lookAt(c);
  camera.near = d/200; camera.far = d*10; camera.updateProjectionMatrix();
  renderer.render(scene,camera);
  window.__ready = true;
}, undefined, e => { window.__err = String(e && e.message || e); });
</script></body></html>"""


class _Server(socketserver.TCPServer):
    # Without this the port stays in TIME_WAIT after a run and the next call
    # dies with "Address already in use".
    allow_reuse_address = True


def _serve(directory, port):
    handler = lambda *a, **k: http.server.SimpleHTTPRequestHandler(*a, directory=str(directory), **k)
    httpd = _Server(("127.0.0.1", port), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


def verify(glb_path, out_png, preset="studio", direction=(0.0, 1.0, 0.30),
           width=1000, height=1000, background="#12161C", zoom=0.92, port=8791):
    """Render `glb_path` through GLTFLoader and save a PNG. Returns the path."""
    from playwright.sync_api import sync_playwright

    glb_path = Path(glb_path).resolve()
    work = glb_path.parent
    cfg = PRESETS.get(preset, PRESETS["studio"])

    import json
    page = PAGE % {
        "three": THREE.read_text(), "loader": LOADER.read_text(),
        "glb": glb_path.name, "w": width, "h": height,
        "dir": ",".join(str(v) for v in direction),
        "bg": background, "preset": json.dumps(cfg), "zoom": zoom,
    }
    tmp_html = work / "_verify_tmp.html"
    tmp_html.write_text(page)

    # GLTFLoader fetches the .glb, and fetch() is blocked on file:// - so the
    # model directory has to be served over HTTP for this to work at all.
    httpd = _serve(work, port)
    port = httpd.server_address[1]    # port=0 lets the OS pick a free one
    try:
        out = Path(out_png)
        out.parent.mkdir(parents=True, exist_ok=True)
        with sync_playwright() as p:
            browser = p.chromium.launch(args=["--use-gl=swiftshader", "--enable-unsafe-swiftshader"])
            pg = browser.new_page(viewport={"width": width, "height": height})
            errors = []
            pg.on("pageerror", lambda e: errors.append(str(e)))
            pg.goto(f"http://127.0.0.1:{port}/{tmp_html.name}")
            pg.wait_for_function("window.__ready === true || window.__err", timeout=120000)
            err = pg.evaluate("window.__err || null")
            if err:
                raise RuntimeError(f"GLTFLoader failed: {err}")
            pg.wait_for_timeout(500)
            pg.screenshot(path=str(out))
            browser.close()
            if errors:
                print("page errors:", errors)
    finally:
        httpd.shutdown()
        httpd.server_close()          # actually release the socket
        tmp_html.unlink(missing_ok=True)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("glb")
    ap.add_argument("--out", default="render/verify.png")
    ap.add_argument("--preset", default="studio", choices=sorted(PRESETS))
    ap.add_argument("--dir", default="0.0,1.0,0.30")
    ap.add_argument("--zoom", type=float, default=0.92)
    args = ap.parse_args()
    d = tuple(float(v) for v in args.dir.split(","))
    print(verify(args.glb, args.out, preset=args.preset, direction=d, zoom=args.zoom))
