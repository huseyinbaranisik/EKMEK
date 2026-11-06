"""
cekirdek/yonlendirici.py — Ekmek AI Asistan
Gelen komutu internet durumuna göre doğru işleyiciye yönlendirir.
"""

import logging
from cekirdek.baglanti_kontrol import baglanti_kontrol_et
from cekirdek.cevrimici_ajan import cevrimici_ajan_isle
from cekirdek.cevrimdisi_ajan import cevrimdisi_ajan_isle

kayit_tutuyucu = logging.getLogger(__name__)


def komutu_yonlendir(komut: str) -> None:
    """
    Komutu önce bağlantıyı kontrol ederek çevrimiçi veya
    çevrimdışı işleyiciye yönlendirir.

    Parametreler:
        komut: Kullanıcıdan gelen sesli veya yazılı komut metni.
    """
    if not komut or not komut.strip():
        kayit_tutuyucu.warning("Bos komut alindi, yonlendirme yapilmiyor.")
        return

    internet_var_mi = baglanti_kontrol_et()

    if internet_var_mi:
        kayit_tutuyucu.info("Mod: CEVRIMICI | Komut: '%s'", komut)
        cevrimici_ajan_isle(komut)
    else:
        kayit_tutuyucu.info("Mod: CEVRIMDISI | Komut: '%s'", komut)
        cevrimdisi_ajan_isle(komut)
