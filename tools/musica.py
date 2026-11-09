"""Música + efeitos do carrossel vivo, feitos por código (R$0, sem modelo).

Uso:  python -I musica.py <proj>          (lê <proj>/carrossel.json, escreve <proj>/audio/slide_N.wav + musica_inteira.wav)

carrossel.json (só o que este script usa):
{
  "bpm": 120,                      # 120 = 1 batida a cada 0,5 s · 1 compasso = 2 s
  "estilo": "tech",                # tech | calmo
  "slides": [
    {"compassos": 4, "energia": 2, "sfx": [[0, "hit"], [2, "pop"], [6.5, "whoosh"]]},
    ...
  ]
}
- sfx = [batida, tipo] — batida conta a partir do início DO SLIDE (0 = primeiro tempo; 0.5 = contratempo).
  tipos: hit pop whoosh click tick shutter ding riser type swoosh thump
- A música é UMA só: o slide 2 continua os compassos do slide 1 (a harmonia segue), então ao arrastar soa como a
  mesma canção. Cada slide tem número inteiro de compassos e o rabo do som que passa do fim volta para o começo
  (buffer circular) → o loop do Instagram não tem emenda.
"""
import json, sys, wave
from pathlib import Path
import numpy as np

SR = 48000
RNG = np.random.default_rng(7)

# ------------------------------------------------------------------ síntese básica
def env(n, a=0.005, d=0.2, s=0.0, r=0.05, hold=None):
    t = np.arange(n) / SR
    e = np.minimum(1, t / max(a, 1e-4))
    dec = np.exp(-np.maximum(0, t - a) / max(d, 1e-4))
    e = e * (s + (1 - s) * dec)
    if hold is not None:
        rel = np.clip(1 - (t - hold) / max(r, 1e-4), 0, 1)
        e = e * np.where(t > hold, rel, 1)
    return e

def lp(x, cut):
    """passa-baixa de 1 polo (rápido o bastante para poucos segundos)."""
    a = np.exp(-2 * np.pi * cut / SR)
    try:
        from scipy.signal import lfilter
        return lfilter([1 - a], [1, -a], x)
    except Exception:
        y = np.empty_like(x); acc = 0.0
        for i, v in enumerate(x):
            acc = (1 - a) * v + a * acc; y[i] = acc
        return y

def hp(x, cut):
    return x - lp(x, cut)

def saw(f, n, det=0.0):
    t = np.arange(n) / SR
    out = np.zeros(n)
    for d in (-det, 0, det) if det else (0,):
        ph = (t * f * (1 + d)) % 1.0
        out += 2 * ph - 1
    return out / (3 if det else 1)

def sine(f, n, ph=0):
    return np.sin(2 * np.pi * f * np.arange(n) / SR + ph)

def tri(f, n):
    ph = (np.arange(n) / SR * f) % 1.0
    return 4 * np.abs(ph - 0.5) - 1

def noise(n):
    return RNG.uniform(-1, 1, n)

def mtof(m):
    return 440.0 * 2 ** ((m - 69) / 12)

# ------------------------------------------------------------------ instrumentos
def kick(n=int(0.42 * SR)):
    t = np.arange(n) / SR
    f = 45 + 110 * np.exp(-t / 0.035)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-t / 0.16) * 0.95 + noise(n) * np.exp(-t / 0.004) * 0.15

def clap(n=int(0.3 * SR)):
    x = hp(noise(n), 900)
    t = np.arange(n) / SR
    e = sum(np.exp(-np.maximum(0, t - o) / 0.012) * (t >= o) for o in (0, 0.011, 0.022)) * 0.5
    return x * (e + np.exp(-t / 0.09) * 0.6) * 0.55

def hat(n=int(0.06 * SR), open_=False):
    if open_: n = int(0.22 * SR)
    t = np.arange(n) / SR
    return hp(noise(n), 7000) * np.exp(-t / (0.07 if open_ else 0.014)) * 0.32

def bass_note(m, dur):
    n = int(dur * SR)
    x = saw(mtof(m), n) * 0.6 + sine(mtof(m), n) * 0.7
    x = lp(x, 420)
    return x * env(n, 0.004, 0.25, 0.55, 0.05, hold=dur - 0.05) * 0.55

def pad_chord(ms, dur):
    n = int((dur + 0.6) * SR)
    x = sum(saw(mtof(m), n, det=0.006) for m in ms) / len(ms)
    x = lp(lp(x, 1500), 1500)
    t = np.arange(n) / SR
    e = np.minimum(1, t / 0.35) * np.clip(1 - (t - dur) / 0.6, 0, 1)
    return x * e * 0.22

def pluck(m, dur=0.35):
    n = int(dur * SR)
    x = tri(mtof(m), n) * 0.7 + sine(mtof(m) * 2, n) * 0.2
    return lp(x, 3500) * env(n, 0.002, 0.11) * 0.28

# ------------------------------------------------------------------ efeitos (sfx)
def sfx(kind):
    if kind == "hit":
        k = kick(); n = len(k); t = np.arange(n) / SR
        return k * 0.9 + lp(noise(n), 2500) * np.exp(-t / 0.06) * 0.35
    if kind == "thump":
        return kick() * 0.8
    if kind == "pop":
        n = int(0.09 * SR); t = np.arange(n) / SR
        f = 500 + 900 * (1 - np.exp(-t / 0.02))
        return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.03) * 0.55
    if kind == "click":
        n = int(0.025 * SR); t = np.arange(n) / SR
        return hp(noise(n), 2000) * np.exp(-t / 0.003) * 0.6
    if kind == "tick":
        n = int(0.04 * SR); t = np.arange(n) / SR
        return sine(2400, n) * np.exp(-t / 0.006) * 0.35
    if kind == "shutter":
        a = sfx("click"); gap = np.zeros(int(0.06 * SR))
        return np.concatenate([a, gap, a * 0.8])
    if kind == "ding":
        n = int(1.2 * SR); t = np.arange(n) / SR
        x = sine(1318, n) + 0.5 * sine(2637, n) + 0.25 * sine(3951, n)
        return x * np.exp(-t / 0.35) * 0.22
    if kind in ("whoosh", "swoosh"):
        n = int(0.45 * SR); t = np.arange(n) / SR
        x = noise(n); cut = 400 + 5000 * np.sin(np.pi * t / t[-1]) ** 2
        y = np.zeros(n); acc = 0.0
        a = np.exp(-2 * np.pi * cut / SR)
        try:
            from scipy.signal import lfilter  # aproximação: filtra em blocos
            out = []
            for i in range(0, n, 480):
                ai = a[i]
                out.append(lfilter([1 - ai], [1, -ai], x[i:i + 480]))
            y = np.concatenate(out)
        except Exception:
            for i in range(n):
                acc = (1 - a[i]) * x[i] + a[i] * acc; y[i] = acc
        return y * np.sin(np.pi * t / t[-1]) ** 1.5 * 0.7
    if kind == "riser":
        n = int(2.0 * SR); t = np.arange(n) / SR
        return hp(noise(n), 1500) * (t / t[-1]) ** 2.5 * 0.35
    if kind == "type":
        out = np.zeros(int(0.5 * SR))
        for i in range(6):
            c = sfx("click") * RNG.uniform(.4, .8); o = int(i * 0.075 * SR)
            out[o:o + len(c)] += c
        return out
    raise ValueError(f"sfx desconhecido: {kind}")

# ------------------------------------------------------------------ música
PROG = {  # acorde por compasso (MIDI), em lá menor: Am F C G
    "tech":  [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]],
    "calmo": [[57, 60, 64, 67], [53, 57, 60, 64], [48, 52, 55, 59], [55, 59, 62, 65]],
}
ARP = [0, 1, 2, 1, 2, 0, 1, 2]  # índice do acorde em colcheias... usado em semicolcheias alternadas


def put(buf, x, t):
    i = int(round(t * SR))
    if i >= len(buf): return
    j = min(len(buf), i + len(x))
    buf[i:j] += x[: j - i]


def render_slide(sl, bar0, bpm, estilo, tail=3.0):
    beat = 60.0 / bpm
    bar = 4 * beat
    L = sl["compassos"] * bar
    n = int(round((L + tail) * SR))
    drums, music, fx = np.zeros(n), np.zeros(n), np.zeros(n)
    en = sl.get("energia", 2)  # 1 = leve, 2 = normal, 3 = cheio
    prog = PROG[estilo]
    for b in range(sl["compassos"]):
        t0 = b * bar
        ch = prog[(bar0 + b) % len(prog)]
        # bateria
        for q in range(4):
            if en >= 2 or q in (0, 2): put(drums, kick(), t0 + q * beat)
            if q in (1, 3) and en >= 1: put(drums, clap(), t0 + q * beat)
            put(drums, hat(), t0 + q * beat + beat / 2)
            if en >= 3: put(drums, hat() * 0.6, t0 + q * beat + beat / 4); put(drums, hat() * 0.5, t0 + q * beat + 3 * beat / 4)
        if en >= 2: put(drums, hat(open_=True), t0 + 3.5 * beat)
        # baixo: fundamental em colcheias com oitava no contratempo
        root = ch[0] - 24
        for e in range(8):
            m = root + (12 if e % 4 == 3 else 0)
            put(music, bass_note(m, beat / 2 * 0.9), t0 + e * beat / 2)
        # pad
        put(music, pad_chord([m + 12 for m in ch], bar), t0)
        # arpejo em semicolcheias (energia ≥ 2)
        if en >= 2:
            for s in range(16):
                if s % 2 == 1 and en < 3: continue
                m = ch[ARP[s % 8] % len(ch)] + 24 + (12 if s % 8 >= 6 else 0)
                put(music, pluck(m), t0 + s * beat / 4)
    for bt, kind in sl.get("sfx", []):
        put(fx, sfx(kind), bt * beat)
    mix = drums * 0.9 + music * 1.0 + fx * 1.1
    # buffer circular: o que passa do fim volta para o começo (loop sem emenda)
    Ln = int(round(L * SR))
    out = mix[:Ln].copy()
    rest = mix[Ln:]
    while len(rest):
        k = min(len(rest), Ln)
        out[:k] += rest[:k]
        rest = rest[k:]
    return out


def write_wav(path, x):
    x = np.clip(x, -1, 1)
    st = np.stack([x, x], 1)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((st * 32767).astype("<i2").tobytes())


def main():
    proj = Path(sys.argv[1])
    cfg = json.loads((proj / "carrossel.json").read_text(encoding="utf-8"))
    bpm = cfg.get("bpm", 120); estilo = cfg.get("estilo", "tech")
    out = proj / "audio"; out.mkdir(exist_ok=True)
    parts, bar0 = [], 0
    for sl in cfg["slides"]:
        parts.append(render_slide(sl, bar0, bpm, estilo))
        bar0 += sl["compassos"]
    allx = np.concatenate(parts)
    rms = np.sqrt(np.mean(allx ** 2)) + 1e-9
    g = 10 ** (-15 / 20) / rms          # ~ -15 dBFS RMS (≈ -14/-16 LUFS)
    for i, p in enumerate(parts, 1):
        y = np.tanh(p * g * 1.1) / np.tanh(1.1)  # limitador suave
        write_wav(out / f"slide_{i}.wav", y * 0.95)
        print(f"slide {i}: {len(p) / SR:.2f} s")
    write_wav(out / "musica_inteira.wav", np.tanh(allx * g * 1.1) / np.tanh(1.1) * 0.95)


if __name__ == "__main__":
    main()
