"""Monta e renderiza o carrossel vivo.

Uso:
  python -I montar.py <proj>                 # monta build/sN/ (HTML + kit + áudio) para cada slide
  python -I montar.py <proj> --render        # monta e renderiza renders/slide_N.mp4 (1080x1350, 30 fps) + previa.html
  python -I montar.py <proj> --render --so 2 # só o slide 2
  python -I montar.py <proj> --snap          # fotos de cada slide (4 momentos) em work/snaps/ para conferir

<proj>/carrossel.json:
{ "titulo": "...", "topo": "CLAUDE CODE GRÁTIS", "bpm": 120, "estilo": "tech",
  "slides": [ {"arquivo": "slides/s1.html", "compassos": 4, "energia": 2, "sfx": [[0, "hit"]]}, ... ] }
<proj>/slides/sN.html = só o miolo do slide (markup + <script> com as animações usando CV.*).
<proj>/assets/ (fotos, recortes, clipes) é copiado para cada build e fica em "assets/...".
"""
import json, shutil, subprocess, sys
from pathlib import Path

KIT = Path(__file__).resolve().parent.parent / "kit"

PAGE = """<!doctype html>
<html lang="pt-BR"><head><meta charset="UTF-8" />
<meta name="viewport" content="width=1080, height=1350" />
<title>{titulo} — slide {i}</title>
<link rel="stylesheet" href="kit/cv.css" />
<script src="kit/vendor/gsap.min.js"></script>
<script>window.CV_SLIDE = {cvs};</script>
<script src="kit/cv.js"></script>
</head><body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{dur}" data-width="1080" data-height="1350">
  <audio id="trilha" class="clip" src="audio.wav" data-start="0" data-duration="{dur}" data-track-index="10" data-volume="1"></audio>
  <div class="bg"><div class="grid"></div><div class="glow" style="left:-250px;top:-300px"></div>
    <div class="glow g2" style="right:-260px;bottom:-200px"></div><div class="sheen"></div><div class="vig"></div></div>
  <div class="top"><span><span class="dot"></span>{topo}</span><span class="count">{i}/{n}</span></div>
  <div class="ruler"><div class="line"></div></div>
  <div class="cont abs" style="inset:0">
{miolo_html}
  </div>
  <div class="ball" id="bola" style="{bola_css}"></div>
</div>
<script>
const {{ tl, b, $, $$ }} = CV; CV.fundo(); CV.regua();
{miolo_js}
CV.fim();
</script>
</body></html>
"""


def split_miolo(txt):
    if "<script>" in txt:
        a, rest = txt.split("<script>", 1)
        js = rest.rsplit("</script>", 1)[0]
        return a, js
    return txt, ""


def montar(proj, so=None):
    cfg = json.loads((proj / "carrossel.json").read_text(encoding="utf-8"))
    bpm = cfg.get("bpm", 120); n = len(cfg["slides"]); inicio = 0.0; out = []
    for i, sl in enumerate(cfg["slides"], 1):
        dur = sl["compassos"] * 4 * 60 / bpm
        if so is None or i == so:
            d = proj / "build" / f"s{i}"
            if d.exists(): shutil.rmtree(d)
            shutil.copytree(KIT, d / "kit")
            if (proj / "assets").exists(): shutil.copytree(proj / "assets", d / "assets")
            shutil.copy(proj / "audio" / f"slide_{i}.wav", d / "audio.wav")
            html, js = split_miolo((proj / sl["arquivo"]).read_text(encoding="utf-8"))
            cvs = json.dumps({"i": i, "total": n, "compassos": sl["compassos"], "bpm": bpm, "inicio": inicio})
            page = PAGE.format(titulo=cfg.get("titulo", "carrossel"), i=i, n=n, cvs=cvs, dur=f"{dur:.3f}",
                               topo=cfg.get("topo", ""), miolo_html=html, miolo_js=js,
                               bola_css="" if sl.get("bola", True) else "display:none")
            (d / "index.html").write_text(page, encoding="utf-8")
            (d / "hyperframes.json").write_text('{ "paths": { "assets": "assets" } }', encoding="utf-8")
            (d / "package.json").write_text('{ "name": "cv-slide", "private": true, "type": "module" }', encoding="utf-8")
            out.append((i, d, dur))
        inicio += dur
    return cfg, out


def sh(cmd, cwd):
    print("$", " ".join(cmd)); r = subprocess.run(cmd, cwd=cwd, shell=True)
    if r.returncode: sys.exit(f"falhou: {' '.join(cmd)}")


def previa(proj, cfg):
    n = len(cfg["slides"])
    vids = "\n".join(f'<video src="renders/slide_{i}.mp4" playsinline loop preload="auto"></video>' for i in range(1, n + 1))
    (proj / "previa.html").write_text(PREVIA.replace("{{VIDS}}", vids).replace("{{T}}", cfg.get("titulo", "")), encoding="utf-8")


PREVIA = """<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><title>{{T}} — prévia</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
:root{--bg:#f3f3f1;--fg:#111;--card:#fff;--mut:#666}
@media (prefers-color-scheme:dark){:root{--bg:#0d0f14;--fg:#eee;--card:#181b22;--mut:#999}}
body{margin:0;background:var(--bg);color:var(--fg);font:15px system-ui;display:flex;flex-direction:column;align-items:center;padding:24px 16px}
.phone{width:min(420px,100%);background:var(--card);border-radius:18px;overflow:hidden;box-shadow:0 10px 40px rgba(0,0,0,.18)}
.hd{display:flex;align-items:center;gap:10px;padding:10px 12px;font-weight:600}.hd i{width:30px;height:30px;border-radius:50%;background:linear-gradient(45deg,#f58529,#dd2a7b,#515bd4)}
.vp{position:relative;aspect-ratio:4/5;overflow:hidden}.strip{display:flex;height:100%;transition:transform .35s ease}
.strip video{width:100%;height:100%;flex:0 0 100%;object-fit:cover;background:#000}
.nav{position:absolute;top:50%;transform:translateY(-50%);border:0;width:34px;height:34px;border-radius:50%;background:rgba(255,255,255,.85);font-size:18px;cursor:pointer}
.l{left:8px}.r{right:8px}.dots{display:flex;gap:5px;justify-content:center;padding:10px}.dots b{width:6px;height:6px;border-radius:50%;background:#bbb}.dots b.on{background:#3897f0}
p{color:var(--mut);max-width:420px;text-align:center}
</style></head><body>
<div class="phone"><div class="hd"><i></i>{{T}}</div><div class="vp"><div class="strip" id="s">{{VIDS}}</div>
<button class="nav l" onclick="go(-1)">‹</button><button class="nav r" onclick="go(1)">›</button></div><div class="dots" id="d"></div></div>
<p>Clique no vídeo para tocar com som. Setas (ou ← →) trocam o slide, como arrastar no Instagram.</p>
<script>
const V=[...document.querySelectorAll('video')],D=document.getElementById('d');let k=0,on=false;
V.forEach(()=>D.appendChild(document.createElement('b')));
function show(){document.getElementById('s').style.transform=`translateX(${-100*k}%)`;[...D.children].forEach((b,i)=>b.className=i==k?'on':'');
V.forEach((v,i)=>{if(i==k&&on){v.currentTime=0;v.play()}else v.pause()})}
function go(s){k=Math.max(0,Math.min(V.length-1,k+s));show()}
document.querySelector('.vp').addEventListener('click',e=>{if(e.target.tagName=='VIDEO'){on=true;show()}});
addEventListener('keydown',e=>{if(e.key=='ArrowRight')go(1);if(e.key=='ArrowLeft')go(-1)});show();
</script></body></html>"""


def main():
    proj = Path(sys.argv[1]).resolve()
    so = int(sys.argv[sys.argv.index("--so") + 1]) if "--so" in sys.argv else None
    cfg, built = montar(proj, so)
    if "--snap" in sys.argv:
        for i, d, dur in built:
            ats = ",".join(f"{dur * f:.2f}" for f in (0.12, 0.35, 0.6, 0.85))
            sh(["npx", "hyperframes", "snapshot", ".", "--no-end", "-o", str(proj / "work" / "snaps" / f"s{i}"), "--at", ats], d)
    if "--render" in sys.argv:
        (proj / "renders").mkdir(exist_ok=True)
        for i, d, dur in built:
            sh(["npx", "hyperframes", "render", ".", "-o", str(proj / "renders" / f"slide_{i}.mp4"), "--fps", "30", "-q", "looks"], d)
        previa(proj, cfg)
        # pasta pronta para postar: partes numeradas na ordem do carrossel + legenda + todas juntas para conferir
        post = proj / "postar"; post.mkdir(exist_ok=True)
        n = len(cfg["slides"])
        for i in range(1, n + 1):
            if (proj / "renders" / f"slide_{i}.mp4").exists():
                shutil.copy(proj / "renders" / f"slide_{i}.mp4", post / f"parte_{i:02d}_de_{n:02d}.mp4")
        if (proj / "legenda.md").exists(): shutil.copy(proj / "legenda.md", post / "legenda.md")
        lista = proj / "renders" / "lista.txt"
        lista.write_text("".join(f"file 'slide_{i}.mp4'\n" for i in range(1, n + 1)), encoding="utf-8")
        subprocess.run(["ffmpeg", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lista), "-c", "copy", "-y",
                        str(proj / "carrossel_inteiro.mp4")])
        lista.unlink()
        print("previa:", proj / "previa.html", "| postar:", post)
    for i, d, dur in built:
        print(f"slide {i}: {dur:.1f} s -> {d}")


if __name__ == "__main__":
    main()
