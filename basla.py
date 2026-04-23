"""
basla.py - Ekmek AI Asistan | Ana Baslangic Noktasi
==================================================
"""

import sys
import time
import logging
import argparse
import threading
from typing import Optional

# -- Windows Terminal UTF-8 Zorunlulugu ---------------------------------------
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# -- Proje Ici Moduller --------------------------------------------------------
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

# SpeechRecognition kontrolü (Döngü dısında bir kez yapılır)
SES_TANIMA_MEVCUT = False
try:
    import speech_recognition as sr
    SES_TANIMA_MEVCUT = True
except ImportError:
    pass

# -----------------------------------------------------------------------------
# Loglama Yapılandırması
# -----------------------------------------------------------------------------

def _loglama_ayarla(hata_ayiklama: bool = False) -> None:
    seviye = logging.DEBUG if hata_ayiklama else logging.INFO
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

# -----------------------------------------------------------------------------
# Ses Tanıma (Mikrofon -> Metin)
# -----------------------------------------------------------------------------

def _mikrofon_dinle() -> Optional[str]:
    if not SES_TANIMA_MEVCUT:
        return None

    ses_tanici = sr.Recognizer()
    ses_tanici.energy_threshold = MIKROFON_ENERJI_ESIGI
    ses_tanici.pause_threshold = MIKROFON_DURUS_ESIGI
    ses_tanici.dynamic_energy_threshold = True

    try:
        with sr.Microphone() as mikrofon_kaynagi:
            ses_tanici.adjust_for_ambient_noise(mikrofon_kaynagi, duration=0.3)
            ses_kaydi = ses_tanici.listen(mikrofon_kaynagi, timeout=5, phrase_time_limit=10)

        if baglanti_kontrol_et():
            taninan_metin = ses_tanici.recognize_google(ses_kaydi, language=KONUSMA_DILI)
        else:
            taninan_metin = ses_tanici.recognize_sphinx(ses_kaydi, language="tr-TR")

        return taninan_metin.lower()
    except Exception:
        return None

# -----------------------------------------------------------------------------
# Ana Donguler
# -----------------------------------------------------------------------------

def sesli_mod_dongusu():
    if not SES_TANIMA_MEVCUT:
        kayit_tutuyucu.error("SpeechRecognition yuklu degil. Sesli mod calistirilemiyor.")
        ekmek_gui.mesaj_ekle("Sistem", "Hata: Mikrofon kutuphanesi eksik.")
        return

    kayit_tutuyucu.info("[SESLI MOD] Dinleniyor...")
    while True:
        try:
            ham_metin = _mikrofon_dinle()
            if ham_metin:
                if any(c in ham_metin for c in ("cikis", "kapat", "dur")): break
                
                if UYANMA_KELIMESI.lower() in ham_metin.lower():
                    islenecek = ham_metin.lower().replace(UYANMA_KELIMESI.lower(), "").strip()
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
    kayit_tutuyucu.info("[METIN MOD] Baslatildi.")
    while True:
        try:
            girilen = input("  [Ekmek]> ").strip()
            if girilen.lower() in ("cikis", "exit"): break
            
            islenecek = girilen.lower().replace(UYANMA_KELIMESI.lower(), "").strip() if UYANMA_KELIMESI.lower() in girilen.lower() else girilen
            ekmek_gui.mesaj_ekle("Siz (Metin)", islenecek)
            komutu_yonlendir(islenecek)
        except EOFError: break
        except Exception as e:
            kayit_tutuyucu.error("Metin dongusu hatasi: %s", e)

# -----------------------------------------------------------------------------
# Baslangic ve Main
# -----------------------------------------------------------------------------

def basla():
    arg_ayristirici = argparse.ArgumentParser()
    arg_ayristirici.add_argument("--metin", "-m", action="store_true")
    arg_ayristirici.add_argument("--debug", "-d", action="store_true", default=HATA_AYIKLAMA_MODU)
    arglar = arg_ayristirici.parse_args()

    _loglama_ayarla(hata_ayiklama=arglar.debug)
    
    print("\n🍞 EKMEK ASISTAN BASLATILIYOR...")
    
    # 1. Selamlamayi arka planda yap
    threading.Thread(target=selam_ver, daemon=True).start()

    # 2. Modu baslat
    hedef = metin_mod_dongusu if arglar.metin else sesli_mod_dongusu
    arka_plan = threading.Thread(target=hedef, daemon=True)
    arka_plan.start()

    # 3. GUI Baslat
    ekmek_gui.baslat()

if __name__ == "__main__":
    basla()
