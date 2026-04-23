"""
cekirdek/cevrimdisi_ajan.py — Ekmek AI Asistan
İnternet bağlantısı olmadığında devreye giren çevrimdışı işleyici.
Yerel Ollama modeli ve JSON sözlük ile çalışır, internet gerektirmez.
"""

import logging
from moduller.tdk_duzenleyici.cevrimdisi_tdk import tdk_cevrimdisi_kontrol
from moduller.yazilim_asistani.cevrimdisi_gelistirici import yazilim_cevrimdisi_yardim
from moduller.otomasyon.antigravity_kontrol import antigravity_hata_yinele

kayit_tutuyucu = logging.getLogger(__name__)

# ── Anahtar kelime → işleyici fonksiyon tablosu ───────────────────────────────
# Komut içinde bu kelimelerden biri geçerse karşısındaki fonksiyon çağrılır.
CEVRIMDISI_ANAHTAR_KELIMELER: dict = {
    # TDK / Belge düzenleme
    "belge":        tdk_cevrimdisi_kontrol,
    "kelime":       tdk_cevrimdisi_kontrol,
    "tdk":          tdk_cevrimdisi_kontrol,
    "duzenle":      tdk_cevrimdisi_kontrol,
    "yazim":        tdk_cevrimdisi_kontrol,
    # Yazılım asistanı
    "python":       yazilim_cevrimdisi_yardim,
    "react":        yazilim_cevrimdisi_yardim,
    "react native": yazilim_cevrimdisi_yardim,
    "kod":          yazilim_cevrimdisi_yardim,
    "hata":         yazilim_cevrimdisi_yardim,
    "antigravity":  antigravity_hata_yinele,
}


def cevrimdisi_ajan_isle(komut: str) -> None:
    """
    Çevrimdışı mod işleyicisi.
    Komutu anahtar kelime tablosuna göre ilgili yerel modüle yönlendirir.

    Parametreler:
        komut: Kullanıcıdan gelen komut metni.
    """
    print("\n[CEVRIMDISI AJAN] Yerel model (Ollama) devrede...")

    kucuk_komut = komut.lower()

    for anahtar_kelime, isleyici in CEVRIMDISI_ANAHTAR_KELIMELER.items():
        if anahtar_kelime in kucuk_komut:
            kayit_tutuyucu.debug(
                "Eslesen anahtar kelime: '%s' → %s",
                anahtar_kelime,
                isleyici.__name__,
            )
            isleyici(komut)
            return

    _genel_cevrimdisi_yanit(komut)


def _genel_cevrimdisi_yanit(komut: str) -> None:
    """Tanımlanmamış komutlar için genel çevrimdışı yanıt."""
    from ayarlar import OLLAMA_MODEL_ADI
    print(f"  [YEREL MODEL] Ollama/{OLLAMA_MODEL_ADI} yanitliyor: '{komut}'")
    print("  (Gercek uygulamada: Ollama HTTP API cagrisi yapilacak)")
