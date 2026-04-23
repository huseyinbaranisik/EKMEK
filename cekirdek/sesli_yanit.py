"""
cekirdek/sesli_yanit.py — Ekmek AI Asistan
Asistanın metinleri sese çevirerek kullanıcıyla konuşmasını sağlar.
"""

import pyttsx3
import logging
from ayarlar import SES_HIZI, SES_DUZEYI, SES_CINSIYET

kayit_tutuyucu = logging.getLogger(__name__)

# TTS motorunu başlat
motor = pyttsx3.init()

def _ses_ayarlarini_uygula():
    """ayarlar.py dosyasındaki değerleri TTS motoruna yükler."""
    motor.setProperty('rate', SES_HIZI)
    motor.setProperty('volume', SES_DUZEYI)
    
    sesler = motor.getProperty('voices')
    # Genelde 0 erkek, 1 kadındır ama sisteme göre değişebilir.
    if SES_CINSIYET == "kadin" and len(sesler) > 1:
        motor.setProperty('voice', sesler[1].id)
    else:
        motor.setProperty('voice', sesler[0].id)

def konustur(metin: str):
    """Verilen metni sesli olarak okur."""
    if not metin:
        return
        
    kayit_tutuyucu.debug("Konusturuluyor: %s", metin)
    try:
        _ses_ayarlarini_uygula()
        motor.say(metin)
        motor.runAndWait()
    except Exception as hata:
        kayit_tutuyucu.error("Sesli yanit sirasinda hata: %s", hata)

# Jarvis tarzı bir karşılama için örnek fonksiyon
def selam_ver():
    konustur("Merhaba efendim. Ben Ekmek. Sizi dinliyorum.")
