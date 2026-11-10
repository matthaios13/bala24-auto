"""Outro Bala24 (1080x1920, 4.5 s, πρωτότυπος ήχος). python make_outro.py logo.png out.mp4"""
import math, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import imageio_ffmpeg

W, H, FPS, DUR, SR = 1080, 1920, 30, 4.5, 44100
NAVY = (4, 18, 31); NAVY2 = (13, 39, 68); GREEN = (36, 242, 126); WHITE = (255, 255, 255)
F_BOLD = "/System/Library/Fonts/Supplemental/Arial Black.ttf"


def ease_out(x): x = min(max(x, 0), 1); return 1 - (1 - x) ** 3
def ease_back(x, s=1.6):
    x = min(max(x, 0), 1) - 1; return x * x * ((s + 1) * x + s) + 1
def prog(t, a, b): return min(max((t - a) / (b - a), 0), 1)


def text_img(txt, size, col):
    f = ImageFont.truetype(F_BOLD, size); bb = f.getbbox(txt)
    im = Image.new("RGBA", (bb[2] - bb[0] + 20, bb[3] - bb[1] + 20), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((10 - bb[0], 10 - bb[1]), txt, font=f, fill=col + (255,))
    return im


def paste(base, im, cx, cy, a=1.0):
    if a < 1:
        im = im.copy(); im.putalpha(im.getchannel("A").point(lambda v: int(v * a)))
    base.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))


def background():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt(((xx - W / 2) / W) ** 2 + ((yy - H * 0.45) / H) ** 2)
    k = np.clip(1 - d * 1.5, 0, 1)[..., None] ** 1.3
    img = np.array(NAVY, np.float32) * (1 - k) + np.array(NAVY2, np.float32) * k
    return Image.fromarray(img.astype(np.uint8)).convert("RGBA")


def build_frames(logo_path):
    logo = Image.open(logo_path).convert("RGBA"); logo = logo.crop(logo.getbbox())
    logo = logo.resize((860, int(logo.height * 860 / logo.width)), Image.LANCZOS)
    glow = Image.new("RGBA", (logo.width + 120, logo.height + 120), GREEN + (0,))
    a = Image.new("L", glow.size, 0); a.paste(logo.getchannel("A"), (60, 60))
    glow.putalpha(a.filter(ImageFilter.GaussianBlur(28)).point(lambda v: int(v * 0.55)))
    base = background()
    l1 = text_img("ΠΕΡΙΣΣΟΤΕΡΑ ΣΤΟ", 46, WHITE)
    l2 = text_img("BALA24.GR", 92, GREEN)
    ig = text_img("IG  @bala24gr", 40, WHITE); yt = text_img("YT  @Bala24_gr", 40, WHITE)
    for fi in range(int(DUR * FPS)):
        t = fi / FPS
        im = base.copy(); L = Image.new("RGBA", (W, H), (0, 0, 0, 0)); g = ImageDraw.Draw(L)
        # διαγώνιες λωρίδες ταχύτητας
        for k in range(-3, 9):
            x = k * 220 + (t * 420) % 220 - 300
            g.polygon([(x, 0), (x + 70, 0), (x - 630, H), (x - 700, H)], fill=GREEN + (14 if k % 2 else 7,))
        # γραμμές γηπέδου
        r = 260 + 40 * ease_out(prog(t, 0, 1.2))
        g.ellipse((W / 2 - r, H * 0.42 - r, W / 2 + r, H * 0.42 + r), outline=GREEN + (40,), width=4)
        g.line((0, H * 0.42, W, H * 0.42), fill=GREEN + (30,), width=4)
        im.alpha_composite(L)
        # logo: σπρώχνεται από αριστερά με «ίχνος»
        p = ease_back(prog(t, 0.15, 0.75))
        cx = -500 + (W / 2 + 500) * p; cy = H * 0.42
        if p < 1:
            for tr in range(1, 5):
                paste(im, logo, cx - tr * 70 * (1 - p), cy, 0.12 * (5 - tr) * (1 - p))
        paste(im, glow, cx, cy, ease_out(prog(t, 0.6, 1.0)))
        paste(im, logo, cx, cy)
        # φωτεινή δέσμη πάνω στο logo
        sw = prog(t, 0.9, 1.6)
        if 0 < sw < 1:
            S = Image.new("RGBA", (W, H), (0, 0, 0, 0)); gs = ImageDraw.Draw(S)
            x = W * 0.05 + sw * W * 0.9
            gs.polygon([(x, cy - 90), (x + 60, cy - 90), (x - 20, cy + 90), (x - 80, cy + 90)], fill=(255, 255, 255, 120))
            S = S.filter(ImageFilter.GaussianBlur(10))
            m = Image.new("L", (W, H), 0); m.paste(logo.getchannel("A"), (int(cx - logo.width / 2), int(cy - logo.height / 2)))
            S.putalpha(Image.fromarray(np.minimum(np.asarray(S.getchannel("A")), np.asarray(m))))
            im.alpha_composite(S)
        # κείμενα
        a1 = ease_out(prog(t, 1.2, 1.6)); a2 = ease_out(prog(t, 1.45, 1.85)); a3 = ease_out(prog(t, 1.9, 2.4))
        paste(im, l1, W / 2, H * 0.55 + 30 * (1 - a1), a1)
        paste(im, l2, W / 2, H * 0.61 + 30 * (1 - a2), a2)
        g2 = ImageDraw.Draw(im)
        bw = 760 * a3
        if bw > 4:
            g2.rounded_rectangle((W / 2 - bw / 2, H * 0.70, W / 2 + bw / 2, H * 0.70 + 6), 3, fill=GREEN + (255,))
        paste(im, ig, W / 2, H * 0.745, a3); paste(im, yt, W / 2, H * 0.785, a3)
        # λευκό flash στην πρόσκρουση + fade out
        arr = np.asarray(im.convert("RGB")).astype(np.float32)
        dt = t - 0.72
        if 0 <= dt < 0.35:
            fl = 0.5 * math.exp(-dt * 12); arr = arr * (1 - fl) + 255 * fl
        arr *= min(prog(t, 0, 0.15), 1 - prog(t, DUR - 0.4, DUR))
        yield np.clip(arr, 0, 255).astype(np.uint8).tobytes()


def audio(path):
    n = int(DUR * SR); t = np.arange(n) / SR; out = np.zeros(n)
    rng = np.random.default_rng(24)
    def lp(x, hi):
        X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR); return np.fft.irfft(X / (1 + (f / hi) ** 4), len(x))
    # whoosh 0.1-0.75
    i0, i1 = int(0.1 * SR), int(0.75 * SR); x = rng.standard_normal(i1 - i0)
    out[i0:i1] += lp(x, 4000) * np.linspace(0, 1, i1 - i0) ** 2 * 0.35
    # impact 0.72
    i = int(0.72 * SR); tt = t[: n - i]
    f = 45 + 110 * np.exp(-tt * 25)
    out[i:] += np.tanh(2 * np.sin(2 * np.pi * np.cumsum(f) / SR)) * np.exp(-tt * 4) * 0.8
    out[i:] += lp(rng.standard_normal(n - i), 9000) * np.exp(-tt * 6) * 0.2
    # χορδή (F#m add9) με σβήσιμο
    for k, m in enumerate((54, 61, 66, 68, 73)):
        fr = 440 * 2 ** ((m - 69) / 12)
        s = sum(np.sin(2 * np.pi * fr * h * tt + k) / h for h in (1, 2, 3)) * np.exp(-tt * 0.9)
        out[i:] += lp(s, 3000) * 0.07
    # δύο «tick» στα κείμενα
    for t0 in (1.2, 1.9):
        j = int(t0 * SR); m = min(n - j, 2500); out[j:j + m] += np.sin(2 * np.pi * 1600 * t[:m]) * np.exp(-t[:m] * 60) * 0.15
    out = np.tanh(out * 1.3); out /= np.max(np.abs(out)) + 1e-9; out *= 0.9
    fo = int(0.4 * SR); out[-fo:] *= np.linspace(1, 0, fo)
    st = (np.stack([out, out], 1) * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(st.tobytes())


if __name__ == "__main__":
    logo, out = sys.argv[1], sys.argv[2]
    wav = out + ".wav"; audio(wav)
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    p = subprocess.Popen([ff, "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-i", wav, "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                          "-shortest", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    for fr in build_frames(logo): p.stdin.write(fr)
    p.stdin.close(); p.wait()
    import os; os.remove(wav); print("done", out)
