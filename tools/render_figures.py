"""Renders the README figures in assets/: cover.png, demo.gif, phone.png.

usage:
  python tools/capture_ui.py shots       # the real index.html / uzak_arayuz pages in Chromium
  python tools/render_figures.py shots
Needs Pillow. Fonts (OFL) in tools/fonts/: Young Serif and Manrope. Colours are the app's own CSS variables
(stiller.css for the desktop widget, uzak_arayuz/mobil.css for the phone page).
"""
import os, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = os.path.join(ROOT, "tools", "fonts")
OUT = os.path.join(ROOT, "assets")

# stiller.css: --arka-plan-bej, --ana-renk, --ikincil-renk, --metin-koyu
BEIGE, BROWN, LATTE, DARK = "#EDE0D4", "#8D6E63", "#D7CCC8", "#3E2723"
CRUST, PAPER, SUB = "#C08552", "#F8F2EB", "#7A5E54"
DESK = "#CDB8A6"  # a plain wallpaper tone for the desktop the widget floats on
PHONE_BG, PHONE_ACCENT = "#0F0F17", "#7C5CFC"  # mobil.css

def font(name, size, weight=None):
    f = ImageFont.truetype(os.path.join(FONTS, name), size)
    if weight:
        f.set_variation_by_axes([weight])
    return f

SERIF = lambda s: font("YoungSerif-Regular.ttf", s)
SANS = lambda s: font("Manrope.ttf", s, 500)
SANS_B = lambda s: font("Manrope.ttf", s, 750)

def wrap(d, text, f, width):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=f) <= width:
            cur = t
        else:
            lines.append(cur); cur = w
    return lines + [cur]

def glow(im, xy, r, rgb, alpha):
    layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).ellipse([xy[0] - r, xy[1] - r, xy[0] + r, xy[1] + r], fill=rgb + (alpha,))
    im.alpha_composite(layer.filter(ImageFilter.GaussianBlur(r // 2)))

def shadow(im, box, r, offset=16, blur=26, alpha=90):
    layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
    x0, y0, x1, y1 = box
    ImageDraw.Draw(layer).rounded_rectangle([x0, y0 + offset, x1, y1 + offset], r, fill=(62, 39, 35, alpha))
    im.alpha_composite(layer.filter(ImageFilter.GaussianBlur(blur)))

def chip(d, xy, text, f, fill, color, pad=(16, 8)):
    x, y = xy
    w = d.textlength(text, font=f)
    h = f.size + 2 * pad[1]
    d.rounded_rectangle([x, y, x + w + 2 * pad[0], y + h], h // 2, fill=fill)
    d.text((x + pad[0], y + pad[1] - 2), text, font=f, fill=color)
    return x + w + 2 * pad[0]

def desktop(im, box, taskbar=True):
    """A plain desktop corner: wallpaper, and a Windows-style taskbar along the bottom."""
    x0, y0, x1, y1 = box
    shadow(im, box, 18, alpha=70)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle(box, 18, fill=DESK)
    if taskbar:
        d.rounded_rectangle([x0, y1 - 52, x1, y1], 18, fill="#F3EEE8")
        d.rectangle([x0, y1 - 52, x1, y1 - 30], fill="#F3EEE8")
        cx = (x0 + x1) // 2
        for i in range(-2, 3):
            d.rounded_rectangle([cx + i * 44 - 14, y1 - 40, cx + i * 44 + 14, y1 - 12], 6, fill="#D8CEC5")
        d.text((x1 - 70, y1 - 38), "21:30", font=SANS(16), fill=SUB)

def phone(im, xy, shot, width):
    x0, y0 = xy
    s = shot.convert("RGB").resize((width, int(width * shot.height / shot.width)), Image.LANCZOS)
    bez = 14
    box = (x0, y0, x0 + width + 2 * bez, y0 + s.height + 2 * bez)
    shadow(im, box, 46, alpha=120)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle(box, 46, fill="#1B1B22", outline="#34343F", width=3)
    mask = Image.new("L", s.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, s.width - 1, s.height - 1], 34, fill=255)
    im.paste(s, (x0 + bez, y0 + bez), mask)  # no notch: it would hide the page's header
    return box

def cover(shots):
    W, H = 1800, 920
    im = Image.new("RGBA", (W, H), PAPER)
    glow(im, (1350, 160), 460, (215, 204, 200), 160)
    glow(im, (700, 920), 380, (192, 133, 82), 50)
    d = ImageDraw.Draw(im)
    x, nx = 100, 100
    for t in ["Electron", "Groq · Llama 3.3", "Whisper"]:
        nx = chip(d, (nx, 128), t, SANS_B(19), BROWN, BEIGE) + 10
    d.text((x - 6, 182), "Ekmek", font=SERIF(140), fill=DARK)
    d.text((x, 358), "A voice assistant for Windows", font=SANS_B(36), fill=BROWN)
    y = 430
    for line in wrap(d, "Talk or type to a small always-on-top window. Whisper turns your voice into text, "
                        "Llama 3.3 decides what to do, and Ekmek opens apps, plays Spotify, sets volume and "
                        "brightness, or just chats, always calling you \"efendim\".", SANS(25), 640):
        d.text((x, y), line, font=SANS(25), fill=DARK); y += 39
    d.text((x, y + 30), "Hüseyin Baran Işık", font=SANS_B(19), fill=SUB)

    desktop(im, (800, 70, 1400, 860))
    w = Image.open(os.path.join(shots, "widget-chat.png")).convert("RGBA")
    w = w.resize((380, int(w.height * 380 / w.width)), Image.LANCZOS)
    im.alpha_composite(w, (1400 - w.width - 10, 860 - 52 - w.height + 6))  # bottom-right, where the app opens
    phone(im, (1440, 250), Image.open(os.path.join(shots, "phone.png")), 252)
    return im.convert("RGB")

def demo(shots):
    frames_dir = os.path.join(shots, "frames")
    files = sorted(f for f in os.listdir(frames_dir) if f.endswith(".png"))
    fw, fh = Image.open(os.path.join(frames_dir, files[0])).size
    W, H = fw + 220, fh + 170
    base = Image.new("RGBA", (W, H), PAPER)  # flat colours only: gradients band in a GIF palette
    d = ImageDraw.Draw(base)
    nx = chip(d, (40, 30), "Fig. 2", SANS_B(18), BROWN, BEIGE)
    d.text((nx + 14, 28), "The real interface", font=SERIF(30), fill=DARK)
    d.rounded_rectangle([40, 90, W - 40, H - 30], 16, fill=DESK)
    out = []
    for f in files:
        p = base.copy()
        p.alpha_composite(Image.open(os.path.join(frames_dir, f)).convert("RGBA"), (W - 40 - fw - 10, 90 + 4))
        out.append(p.convert("RGB").quantize(colors=160, method=Image.Quantize.FASTOCTREE))
    out[0].save(os.path.join(OUT, "demo.gif"), save_all=True, append_images=out[1:] + [out[-1]] * 10,
                duration=100, loop=0, optimize=True)

def phone_fig(shots):
    """Fig. 3: the phone remote, served by the app on the same Wi-Fi."""
    W, H = 1400, 980
    im = Image.new("RGBA", (W, H), PAPER)
    d = ImageDraw.Draw(im)
    nx = chip(d, (70, 44), "Fig. 3", SANS_B(18), BROWN, BEIGE)
    d.text((nx + 14, 42), "The phone remote", font=SERIF(32), fill=DARK)
    phone(im, (110, 120), Image.open(os.path.join(shots, "phone.png")), 340)
    d = ImageDraw.Draw(im)
    x, y = 580, 170
    items = [("Same Wi-Fi, no install", "The desktop app starts a small web server on port 3847 and prints its address in the console. A QR code of it is served at /api/qr."),
             ("Quick commands", "Volume up, volume down, mute, night mode, game mode and Spotify, one tap each."),
             ("Chat", "Type a command; it goes through the same Llama 3.3 prompt. Volume, brightness and other system actions run; opening apps does not."),
             ("System panel", "Volume and brightness sliders, and play / previous / next media keys.")]
    for title, text in items:
        d.text((x, y), title, font=SANS_B(26), fill=DARK)
        y += 40
        for line in wrap(d, text, SANS(22), 720):
            d.text((x, y), line, font=SANS(22), fill=SUB); y += 34
        y += 30
    return im.convert("RGB")

if __name__ == "__main__":
    shots = sys.argv[1]
    cover(shots).save(os.path.join(OUT, "cover.png"), optimize=True)
    demo(shots)
    phone_fig(shots).save(os.path.join(OUT, "phone.png"), optimize=True)
    print("figures ->", OUT)
