"""Captures the real interface pages in Chromium (the engine Electron uses) and saves PNGs and GIF frames.

The calls into Electron's main process are stubbed so they never invent an answer: speech-to-text returns
nothing, and the Groq reply stays pending (so the chat shows the app's own typing indicator). A fake microphone
lets the record button reach its real "Dinleniyor..." state. The phone page gets the health response that
moduller/uzak_kontrol.js returns.

usage: python tools/capture_ui.py <out_dir>      (needs playwright)
"""
import glob, json, os, sys
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.abspath(sys.argv[1])
os.makedirs(os.path.join(OUT, "frames"), exist_ok=True)
CHROME = sorted(glob.glob(os.path.expanduser("~/AppData/Local/ms-playwright/chromium-*/chrome-win64/chrome.exe")))
STUB = """
window.electronAPI = {
  pencereyiKapat: async () => {}, sunucuBilgisiAl: async () => ({}), uzakKomutDinle: () => {},
  uygulamayiBaslat: async () => ({}), sistemKontrolu: async () => ({}),
  sesiMetneCevir: () => new Promise(r => setTimeout(() => r(''), 1800)),
  komutuYorumla: () => new Promise(() => {}),
  sozlukYukle: async () => ({}), sozlukEkle: async () => ({}), sozlukSil: async () => ({}),
  sozlukDuzenle: async () => ({}), sozlukAra: async () => ({}),
};
"""
HEALTH = json.dumps({"durum": "aktif", "mesaj": "Ekmek AI çalışıyor efendim!"})
n = 0

def grab(page, count=1):
    global n
    for _ in range(count):
        page.screenshot(path=os.path.join(OUT, "frames", f"{n:04d}.png"), omit_background=True)
        n += 1
        page.wait_for_timeout(90)

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROME[-1] if CHROME else None,
                          args=["--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream"])
    url = "file:///" + os.path.join(ROOT, "index.html").replace("\\", "/")

    # stills at 2x
    ctx = b.new_context(viewport={"width": 400, "height": 640}, device_scale_factor=2)
    ctx.add_init_script(STUB)
    page = ctx.new_page(); page.goto(url, wait_until="load"); page.wait_for_timeout(1500)
    page.screenshot(path=os.path.join(OUT, "widget.png"), omit_background=True)
    page.click("#chat-gec-btn"); page.wait_for_timeout(1200)
    page.fill("#chat-girisi", "Spotify'da lofi çal"); page.press("#chat-girisi", "Enter"); page.wait_for_timeout(800)
    page.screenshot(path=os.path.join(OUT, "widget-chat.png"), omit_background=True)
    ctx.close()

    # GIF frames at 1x
    ctx = b.new_context(viewport={"width": 400, "height": 640}, device_scale_factor=1)
    ctx.add_init_script(STUB)
    page = ctx.new_page(); page.goto(url, wait_until="load"); page.wait_for_timeout(1500)
    grab(page, 10)
    page.click("#mic-btn"); grab(page, 16)            # Dinleniyor...
    page.click("#mic-btn"); grab(page, 22)            # Düşünülüyor... then Hazır (no text came back)
    page.click("#chat-gec-btn"); grab(page, 12)
    page.click("#chat-girisi")
    for ch in "Spotify'da lofi çal":
        page.keyboard.type(ch); grab(page)
    grab(page, 4)
    page.press("#chat-girisi", "Enter"); grab(page, 18)  # user bubble + typing indicator (reply pending)
    ctx.close()

    # phone remote page at 2x
    ctx = b.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True, has_touch=True)
    ctx.route("**/api/saglik", lambda r: r.fulfill(status=200, content_type="application/json", body=HEALTH))
    page = ctx.new_page()
    page.goto("file:///" + os.path.join(ROOT, "uzak_arayuz", "index.html").replace("\\", "/"), wait_until="load")
    page.wait_for_timeout(1500)
    page.screenshot(path=os.path.join(OUT, "phone.png"))
    b.close()
print(n, "frames ->", OUT)
