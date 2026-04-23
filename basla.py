import sys
import time
import logging
import argparse
import threading
import numpy as np
import sounddevice as sd
import io
from typing import Optional

# UTF-8 Standartlasdirma
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Ayarlar ve Moduller
from ayarlar import (
    UYANMA_KELIMESI, HATA_AYIKLAMA_MODU, KONUSMA_DILI
)
from cekirdek.baglanti_kontrol import baglanti_kontrol_et
from cekirdek.yonlendirici import komutu_yonlendir
from cekirdek.sesli_yanit import konustur, selam_ver
from arayuz.ana_pencere import ekmek_gui

# Speech Recognition Modulu
try:
    import speech_recognition as sr
    SES_TANIMA_MEVCUT = True
except ImportError:
    SES_TANIMA_MEVCUT = False

logging.basicConfig(level=logging.DEBUG if HATA_AYIKLAMA_MODU else logging.INFO)
kayit_tutuyucu = logging.getLogger("ekmek.basla")

def _ses_kaydet_ve_tani(tanici: sr.Recognizer, sure=5, ornekleme_hizi=16000) -> Optional[str]:
    """PyAudio yerine sounddevice kullanarak ses kaydeder ve tanir."""
    try:
        kayit_tutuyucu.debug(f"Dinleniyor... ({sure} sn)")
        # Sesi numpy dizisi olarak kaydet
        kayit = sd.rec(int(sure * ornekleme_hizi), samplerate=ornekleme_hizi, channels=1, dtype='int16')
        sd.wait() # Kayit bitene kadar bekle
        
        # Numpy dizisini wav formatina donustur
        import scipy.io.wavfile as wav
        buffer = io.BytesIO()
        wav.write(buffer, ornekleme_hizi, kayit)
        buffer.seek(0)
        
        with sr.AudioFile(buffer) as kaynak:
            audio = tanici.record(kaynak)
            
        if baglanti_kontrol_et():
            metin = tanici.recognize_google(audio, language=KONUSMA_DILI)
        else:
            metin = tanici.recognize_sphinx(audio, language="tr-TR")
            
        return metin.lower()
    except Exception as e:
        # Sessizlik durumunda hata vermesini engelle
        return None

def sesli_mod_dongusu():
    if not SES_TANIMA_MEVCUT:
        kayit_tutuyucu.error("SpeechRecognition yuklu degil!")
        return

    tanici = sr.Recognizer()
    kayit_tutuyucu.info("[SESLI MOD] Ekmek (sounddevice ile) dinliyor.")

    while True:
        try:
            # Her seferinde 4 saniyelik parcalar halinde dinle
            metin = _ses_kaydet_ve_tani(tanici, sure=4)
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

    # Selamlama
    threading.Thread(target=selam_ver, daemon=True).start()

    # Dongu
    hedef = metin_mod_dongusu if arglar.metin else sesli_mod_dongusu
    threading.Thread(target=hedef, daemon=True).start()

    ekmek_gui.baslat()

if __name__ == "__main__":
    basla()
