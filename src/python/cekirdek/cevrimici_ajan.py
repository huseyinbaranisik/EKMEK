"""
cekirdek/cevrimici_ajan.py — Ekmek AI Asistan
İnternet bağlantısı mevcut olduğunda devreye giren çevrimiçi işleyici.
Her gelen komut önce anahtar kelime tablosuna bakılarak ilgili modüle yönlendirilir.
"""

import logging
from moduller.tdk_duzenleyici.cevrimici_tdk import tdk_cevrimici_kontrol
from moduller.yazilim_asistani.cevrimici_gelistirici import yazilim_cevrimici_yardim
from moduller.otomasyon.antigravity_kontrol import antigravity_hata_yinele

kayit_tutuyucu = logging.getLogger(__name__)

# ── Anahtar kelime → işleyici fonksiyon tablosu ───────────────────────────────
# Komut içinde bu kelimelerden biri geçerse karşısındaki fonksiyon çağrılır.
CEVRIMICI_ANAHTAR_KELIMELER: dict = {
    # TDK / Belge düzenleme
    "belge":        tdk_cevrimici_kontrol,
    "kelime":       tdk_cevrimici_kontrol,
    "tdk":          tdk_cevrimici_kontrol,
    "duzenle":      tdk_cevrimici_kontrol,
    "yazim":        tdk_cevrimici_kontrol,
    # Yazılım asistanı
    "python":       yazilim_cevrimici_yardim,
    "react":        yazilim_cevrimici_yardim,
    "react native": yazilim_cevrimici_yardim,
    "kod":          yazilim_cevrimici_yardim,
    "hata":         yazilim_cevrimici_yardim,
    "stackoverflow": yazilim_cevrimici_yardim,
    "github":       yazilim_cevrimici_yardim,
    # Otomasyon
    "antigravity":  antigravity_hata_yinele,
}


def cevrimici_ajan_isle(komut: str) -> None:
    """
    Çevrimiçi mod işleyicisi.
    Komutu anahtar kelime tablosuna göre ilgili modüle yönlendirir.
    Eşleşme bulunamazsa genel bir bulut yanıtı gösterir.

    Parametreler:
        komut: Kullanıcıdan gelen komut metni.
    """
    print("\n[CEVRIMICI AJAN] Bulut API'leri ve Web Ajanlari devrede...")

    kucuk_komut = komut.lower()

    for anahtar_kelime, isleyici in CEVRIMICI_ANAHTAR_KELIMELER.items():
        if anahtar_kelime in kucuk_komut:
            kayit_tutuyucu.debug(
                "Eslesen anahtar kelime: '%s' → %s",
                anahtar_kelime,
                isleyici.__name__,
            )
            isleyici(komut)
            return

    # Hiçbir modüle uymayan genel komut
    _genel_cevrimici_yanit(komut)


def _genel_cevrimici_yanit(komut: str) -> None:
    """Tanımlanmamış komutlar için genel çevrimiçi yanıt."""
    print(f"  [BOT] Genel bulut modeli yanitliyor: '{komut}'")
    print("  (Gercek uygulamada: OpenAI / Gemini API cagrisi yapilacak)")
