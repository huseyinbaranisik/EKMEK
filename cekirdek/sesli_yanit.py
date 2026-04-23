"""
cekirdek/sesli_yanit.py - Ekmek AI Asistan
Edge-TTS kullanarak çok daha doğal ve akıcı bir Türkçe ile konuşur.
Kütüphane bağımlılığı minimuma indirilmiştir.
"""

import os
import asyncio
import logging
import subprocess
from ayarlar import SES_HIZI, SES_DUZEYI, SES_CINSIYET

kayit_tutuyucu = logging.getLogger(__name__)

# Ses dosyası yolu
GECICI_SES_DOSYASI = os.path.abspath("veri/yanit.mp3")

def _mp3_cal_windows():
    """Ek kütüphane gerektirmeden PowerShell üzerinden ses çalar."""
    if not os.path.exists(GECICI_SES_DOSYASI): return
    
    komut = (
        f"$player = New-Object -ComObject WMPlayer.OCX;"
        f"$player.URL = '{GECICI_SES_DOSYASI}';"
        f"$player.controls.play();"
        f"while ($player.playState -ne 1) {{ Start-Sleep -Milliseconds 100 }}"
    )
    subprocess.run(["powershell", "-Command", komut], capture_output=True)

def konustur(metin: str):
    """Doğal sesi (Edge-TTS) kullanarak konuşur."""
    if not metin: return
    
    kayit_tutuyucu.debug("Konusturuluyor: %s", metin)

    # Önceki dosyayı temizle
    if os.path.exists(GECICI_SES_DOSYASI):
        try: os.remove(GECICI_SES_DOSYASI)
        except: pass

    try:
        import edge_tts
        # Hız ayarı (+10% gibi)
        hiz_yuzde = f"{int((SES_HIZI - 200) / 2)}%"
        if not hiz_yuzde.startswith(('-', '+')): hiz_yuzde = "+" + hiz_yuzde
        ses_adi = "tr-TR-AhmetNeural" if SES_CINSIYET == "erkek" else "tr-TR-EmelNeural"

        async def _kaydet():
            iletisim = edge_tts.Communicate(metin, ses_adi, rate=hiz_yuzde)
            await iletisim.save(GECICI_SES_DOSYASI)

        asyncio.run(_kaydet())
        _mp3_cal_windows()
    except ImportError:
        kayit_tutuyucu.warning("edge-tts yuklu degil, sesli yanit verilemiyor.")
    except Exception as hata:
        kayit_tutuyucu.error("Sesli yanit hatasi: %s", hata)

def selam_ver():
    konustur("Merhaba efendim. Ben Ekmek. Sizi dinliyorum.")
