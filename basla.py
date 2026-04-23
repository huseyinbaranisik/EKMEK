"""
basla.py - Ekmek AI Asistan | Stabilize Versiyon
"""

import sys
import time
import logging
import argparse
import threading
from typing import Optional

# UTF-8 Ayari
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Modul Yuklemeleri
from ayarlar import (
    UYANMA_KELIMESI, HATA_AYIKLAMA_MODU, KONUSMA_DILI,
    MIKROFON_ENERJI_ESIGI, MIKROFON_DURUS_ESIGI
)
from cekirdek.baglanti_kontrol import baglanti_kontrol_et
from cekirdek.yonlendirici import komutu_yonlendir
from cekirdek.sesli_yanit import konustur, selam_ver
from arayuz.ana_pencere import ekmek_gui

# Ses Tanima Kontrolu
SES_TANIMA_MEVCUT = False
try:
    import speech_recognition as sr
    SES_TANIMA_MEVCUT = True
except ImportError:
    pass

logging.basicConfig(level=logging.DEBUG if HATA_AYIKLAMA_MODU else logging.INFO)
kayit_tutuyucu = logging.getLogger("ekmek.basla")

def _mikrofon_dinle() -> Optional[str]:
    if not SES_TANIMA_MEVCUT: return None
    
    tanici = sr.Recognizer()
    # Enerji esigini ortam sesine gore dinamik yap
    tanici.dynamic_energy_threshold = True
    tanici.energy_threshold = MIKROFON_ENERJI_ESIGI 

    try:
        with sr.Microphone() as kaynak:
            kayit_tutuyucu.debug("Ortam sesi ayarlaniyor...")
            tanici.adjust_for_ambient_noise(kaynak, duration=0.5)
            kayit_tutuyucu.info("Dinleniyor... (Ekmek demenizi bekliyorum)")
            ses = tanici.listen(kaynak, timeout=5, phrase_time_limit=8)
            
        kayit_tutuyucu.debug("Ses alindi, cozuluyor...")
        if baglanti_kontrol_et():
            metin = tanici.recognize_google(ses, language=KONUSMA_DILI)
        else:
            metin = tanici.recognize_sphinx(ses, language="tr-TR")
        
        return metin.lower()
    except sr.UnknownValueError:
        return None
    except Exception as e:
        kayit_tutuyucu.debug("Mikrofon hatasi: %s", e)
        return None

def sesli_mod_dongusu():
    if not SES_TANIMA_MEVCUT:
        ekmek_gui.mesaj_ekle("Sistem", "Hata: Ses tanima kutuphanesi eksik.")
        return

    while True:
        try:
            ham_metin = _mikrofon_dinle()
            if ham_metin:
                kayit_tutuyucu.info(f"Duyulan: {ham_metin}")
                if UYANMA_KELIMESI.lower() in ham_metin:
                    komut = ham_metin.replace(UYANMA_KELIMESI.lower(), "").strip()
                    if not komut:
                        konustur("Efendim?")
                    else:
                        ekmek_gui.mesaj_ekle("Siz (Ses)", komut)
                        komutu_yonlendir(komut)
        except Exception as e:
            time.sleep(1)

def metin_mod_dongusu():
    while True:
        try:
            girilen = input(" [Ekmek]> ").strip()
            if girilen:
                ekmek_gui.mesaj_ekle("Siz", girilen)
                komutu_yonlendir(girilen)
        except EOFError: break

def basla():
    parser = argparse.ArgumentParser()
    parser.add_argument("--metin", action="store_true")
    args = parser.parse_args()

    # Selamlama
    threading.Thread(target=selam_ver, daemon=True).start()

    # Dongu baslat
    hedef = metin_mod_dongusu if args.metin else sesli_mod_dongusu
    threading.Thread(target=hedef, daemon=True).start()

    # GUI Ana Thread
    ekmek_gui.baslat()

if __name__ == "__main__":
    basla()
