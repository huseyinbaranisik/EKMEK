"""
cekirdek/baglanti_kontrol.py — Ekmek AI Asistan
İnternet bağlantısını milisaniyeler içinde kontrol eder.
"""

import socket
import logging
from ayarlar import BAGLANTI_TEST_SUNUCUSU, BAGLANTI_TEST_PORTU, BAGLANTI_ZAMAN_ASIMI

kayit_tutuyucu = logging.getLogger(__name__)


def baglanti_kontrol_et() -> bool:
    """
    Google DNS (8.8.8.8:53) üzerinden TCP bağlantısı deneyerek
    aktif internet bağlantısı olup olmadığını kontrol eder.

    Döndürür:
        True  → İnternet bağlantısı var
        False → İnternet bağlantısı yok
    """
    try:
        socket.setdefaulttimeout(BAGLANTI_ZAMAN_ASIMI)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as soket:
            soket.connect((BAGLANTI_TEST_SUNUCUSU, BAGLANTI_TEST_PORTU))
        kayit_tutuyucu.debug("✅ İnternet bağlantısı aktif.")
        return True
    except (socket.timeout, socket.error, OSError) as hata:
        kayit_tutuyucu.debug("❌ İnternet bağlantısı yok. Sebep: %s", hata)
        return False
