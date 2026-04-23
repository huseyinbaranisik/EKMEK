"""
basla.py — Ekmek AI Asistan | Ana Başlangıç Noktası (THREAD-SAFE VERSIYON)
========================================================================
Tkinter threading hatasını (Tcl_AsyncDelete) çözmek için:
- Arayüz (GUI) ana thread'de (main thread) çalışır.
- Ses/Metin döngüsü arka plan thread'inde çalışır.
"""

import sys
import time
import logging
import argparse
import threading
from typing import Optional

# ── Windows Terminal UTF-8 Zorunluluğu ───────────────────────────────────────
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ── Proje İçi Modüller ────────────────────────────────────────────────────────
from ayarlar import (
    UYANMA_KELIMESI,
    HATA_AYIKLAMA_MODU,
    SURUM,
    KONUSMA_DILI,
    MIKROFON_ENERJI_ESIGI,
    MIKROFON_DURUS_ESIGI,
)
from cekirdek.baglanti_kontrol import baglanti_kontrol_et
from cekirdek.yonlendirici import komutu_yonlendir
from cekirdek.sesli_yanit import konustur, selam_ver
from arayuz.ana_pencere import ekmek_gui

# ─────────────────────────────────────────────────────────────────────────────
# Loglama Yapılandırması
# ─────────────────────────────────────────────────────────────────────────────

def _loglama_ayarla(hata_ayiklama: bool = False) -> None:
    seviye   = logging.DEBUG if hata_ayiklama else logging.INFO
    bicimleme = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    zaman_bicimi = "%H:%M:%S"

    try:
        import colorlog
        isleyici = colorlog.StreamHandler()
        isleyici.setFormatter(colorlog.ColoredFormatter(
            f"%(log_color)s{bicimleme}",
            datefmt=zaman_bicimi,
            log_colors={
                "DEBUG": "cyan", "INFO": "green", "WARNING": "yellow",
                "ERROR": "red", "CRITICAL": "bold_red",
            },
        ))
        logging.basicConfig(level=seviye, handlers=[isleyici])
    except ImportError:
        logging.basicConfig(level=seviye, format=bicimleme, datefmt=zaman_bicimi)

kayit_tutuyucu = logging.getLogger("ekmek.basla")

# ─────────────────────────────────────────────────────────────────────────────
# Ses Tanıma (Mikrofon → Metin)
# ─────────────────────────────────────────────────────────────────────────────

def _mikrofon_dinle() -> Optional[str]:
    try:
        import speech_recognition as sr
    except ImportError:
        kayit_tutuyucu.error("SpeechRecognition eksik.")
        return None

    ses_tanici = sr.Recognizer()
    ses_tanici.energy_threshold = MIKROFON_ENERJI_ESIGI
    ses_tanici.pause_threshold = MIKROFON_DURUS_ESIGI
    ses_tanici.dynamic_energy_threshold = True

    try:
        with sr.Microphone() as mikrofon_kaynagi:
            # Ortam gürültüsüne hızlıca uyum sağla
            ses_tanici.adjust_for_ambient_noise(mikrofon_kaynagi, duration=0.3)
            ses_kaydi = ses_tanici.listen(mikrofon_kaynagi, timeout=5, phrase_time_limit=10)

        if baglanti_kontrol_et():
            tanınan_metin = ses_tanici.recognize_google(ses_kaydi, language=KONUSMA_DILI)
        else:
            tanınan_metin = ses_tanici.recognize_sphinx(ses_kaydi, language="tr-TR")

        return tanınan_metin.lower()

    except Exception:
        return None

# ─────────────────────────────────────────────────────────────────────────────
# Ana Döngüler (ARKA PLAN THREAD'İNDE ÇALIŞIRLAR)
# ─────────────────────────────────────────────────────────────────────────────

def _uyanma_kontrol(metin: str) -> bool:
    return UYANMA_KELIMESI.lower() in metin.lower()

def _temizle(metin: str) -> str:
    return metin.lower().replace(UYANMA_KELIMESI.lower(), "").strip()

def sesli_mod_dongusu():
    kayit_tutuyucu.info("[SESLI MOD] Arka planda dinleniyor...")
    while True:
        try:
            ham_metin = _mikrofon_dinle()
            if ham_metin:
                if any(c in ham_metin for c in ("cikis", "kapat", "dur")): break
                
                if _uyanma_kontrol(ham_metin):
                    islenecek = _temizle(ham_metin)
                    if not islenecek:
                        konustur("Efendim?")
                        ekmek_gui.mesaj_ekle("Sistem", "Sizi dinliyorum...")
                    else:
                        ekmek_gui.mesaj_ekle("Siz (Ses)", islenecek)
                        komutu_yonlendir(islenecek)
        except Exception as e:
            kayit_tutuyucu.error("Ses dongusu hatasi: %s", e)
            time.sleep(1)

def metin_mod_dongusu():
    kayit_tutuyucu.info("[METIN MOD] Arka planda baslatildi.")
    while True:
        try:
            # Not: input() fonksiyonu GUI varken terminalde bazen karisabilir,
            # ileride bunu tamamen GUI üzerinden alacağız.
            girilen = input("  [Ekmek]> ").strip()
            if girilen.lower() in ("cikis", "exit"): break
            
            islenecek = _temizle(girilen) if _uyanma_kontrol(girilen) else girilen
            ekmek_gui.mesaj_ekle("Siz (Metin)", islenecek)
            komutu_yonlendir(islenecek)
        except EOFError: break
        except Exception as e:
            kayit_tutuyucu.error("Metin dongusu hatasi: %s", e)

# ─────────────────────────────────────────────────────────────────────────────
# Başlangıç ve Main
# ─────────────────────────────────────────────────────────────────────────────

def basla():
    arg_ayristirici = argparse.ArgumentParser()
    arg_ayristirici.add_argument("--metin", "-m", action="store_true")
    arg_ayristirici.add_argument("--debug", "-d", action="store_true", default=HATA_AYIKLAMA_MODU)
    arglar = arg_ayristirici.parse_args()

    _loglama_ayarla(hata_ayiklama=arglar.debug)
    
    print("\n🍞 EKMEK ASİSTAN BAŞLATILIYOR...")
    
    # 1. TTS Selamlamasını arka planda yap (GUI'yi bloklamasın)
    threading.Thread(target=selam_ver, daemon=True).start()

    # 2. Seçilen modu arka plan thread'inde başlat
    hedef_fonksiyon = metin_mod_dongusu if arglar.metin else sesli_mod_dongusu
    arka_plan_thread = threading.Thread(target=hedef_fonksiyon, daemon=True)
    arka_plan_thread.start()

    # 3. ANA THREAD'DE GUI'YI BAŞLAT (KRİTİK!)
    # Bu satır çalışınca program burada bekler (GUI kapanana kadar)
    kayit_tutuyucu.info("Arayuz ana thread'de baslatiliyor...")
    ekmek_gui.baslat()

if __name__ == "__main__":
    basla()
