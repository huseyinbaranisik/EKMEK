import sys
import time
import logging
import argparse
import threading
from typing import Optional

# UTF-8 Standartlasdirma
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Ayarlar ve Moduller
from ayarlar import (
    UYANMA_KELIMESI, HATA_AYIKLAMA_MODU, KONUSMA_DILI,
    MIKROFON_ENERJI_ESIGI, MIKROFON_DURUS_ESIGI
)
from cekirdek.baglanti_kontrol import baglanti_kontrol_et
from cekirdek.yonlendirici import komutu_yonlendir
from cekirdek.sesli_yanit import konustur, selam_ver
from arayuz.ana_pencere import ekmek_gui

# Ses Tanima Modulu Kontrolu
try:
    import speech_recognition as sr
    SES_TANIMA_MEVCUT = True
except ImportError:
    SES_TANIMA_MEVCUT = False

logging.basicConfig(level=logging.DEBUG if HATA_AYIKLAMA_MODU else logging.INFO)
kayit_tutuyucu = logging.getLogger("ekmek.basla")

def _mikrofon_dinle(tanici: sr.Recognizer) -> Optional[str]:
    try:
        with sr.Microphone() as kaynak:
            kayit_tutuyucu.debug(f"Enerji Esigi: {tanici.energy_threshold} | Dinleniyor...")
            # Ortam gurultusune gore her seferinde ufak bir kalibrasyon
            tanici.adjust_for_ambient_noise(kaynak, duration=0.3)
            audio = tanici.listen(kaynak, timeout=5, phrase_time_limit=10)
            
        kayit_tutuyucu.debug("Ses yakalandi, isleniyor...")
        
        if baglanti_kontrol_et():
            metin = tanici.recognize_google(audio, language=KONUSMA_DILI)
        else:
            metin = tanici.recognize_sphinx(audio, language="tr-TR")
            
        return metin.lower()
    except (sr.WaitTimeoutError, sr.UnknownValueError):
        return None
    except Exception as e:
        kayit_tutuyucu.debug(f"Hata: {e}")
        return None

def sesli_mod_dongusu():
    if not SES_TANIMA_MEVCUT:
        kayit_tutuyucu.error("SpeechRecognition yuklu degil!")
        return

    tanici = sr.Recognizer()
    tanici.energy_threshold = MIKROFON_ENERJI_ESIGI
    tanici.dynamic_energy_threshold = True
    tanici.pause_threshold = MIKROFON_DURUS_ESIGI

    kayit_tutuyucu.info("[SESLI MOD] Ekmek seni dinlemeye hazir.")

    while True:
        try:
            metin = _mikrofon_dinle(tanici)
            if metin:
                kayit_tutuyucu.info(f"Duyulan: {metin}")
                if UYANMA_KELIMESI.lower() in metin:
                    komut = metin.replace(UYANMA_KELIMESI.lower(), "").strip()
                    if not komut:
                        konustur("Efendim?")
                    else:
                        ekmek_gui.mesaj_ekle("Siz (Ses)", komut)
                        komutu_yonlendir(komut)
        except Exception as e:
            kayit_tutuyucu.error(f"Dongu Hatasi: {e}")
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
    arglar = parser.parse_args()

    # Arka planda selamlama
    threading.Thread(target=selam_ver, daemon=True).start()

    # Ana Dongu
    hedef = metin_mod_dongusu if arglar.metin else sesli_mod_dongusu
    threading.Thread(target=hedef, daemon=True).start()

    # GUI (Ana Thread)
    ekmek_gui.baslat()

if __name__ == "__main__":
    basla()
