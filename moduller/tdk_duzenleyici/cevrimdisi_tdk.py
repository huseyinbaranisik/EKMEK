"""
moduller/tdk_duzenleyici/cevrimdisi_tdk.py — Ekmek AI Asistan

Çevrimdışı TDK modülü — iki işlev sunar:
  1. veri/sozluk.json dosyasındaki yerel kelime listesiyle kelime doğrulama
  2. python-docx ile Word belgesindeki şüpheli kelimeleri [!] ile işaretleme
  İnternet gerektirmez.
"""

import json
import logging
import re
from pathlib import Path
from typing import Optional, Set

from docx import Document

from ayarlar import YEREL_SOZLUK_YOLU

kayit_tutuyucu = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Yerel Sözlük Yükleme (Bellekte Saklanır — Tek Seferlik)
# ─────────────────────────────────────────────────────────────────────────────

_SOZLUK_BELLEGI: Optional[Set[str]] = None   # İlk çağrıda dolar, sonra cache'den gelir


def _yerel_sozlugu_yukle() -> Set[str]:
    """
    veri/sozluk.json dosyasını okuyarak tüm kelimeleri bir kümeye yükler.
    Dosya bulunamazsa boş küme döner ve kullanıcıyı uyarır.

    Döndürür:
        Küçük harfli kelimelerden oluşan küme (set).
    """
    global _SOZLUK_BELLEGI

    # Daha önce yüklendiyse bellekten döndür
    if _SOZLUK_BELLEGI is not None:
        return _SOZLUK_BELLEGI

    sozluk_dosya_yolu = Path(YEREL_SOZLUK_YOLU)
    if not sozluk_dosya_yolu.exists():
        kayit_tutuyucu.warning("Yerel sozluk bulunamadi: %s", sozluk_dosya_yolu)
        print(f"  [UYARI] Sozluk dosyasi yok: {sozluk_dosya_yolu}")
        _SOZLUK_BELLEGI = set()
        return _SOZLUK_BELLEGI

    try:
        with sozluk_dosya_yolu.open(encoding="utf-8") as dosya:
            veri = json.load(dosya)

        # Desteklenen JSON formatları:
        # Format 1 → {"kelimeler": ["kelime1", ...]}
        # Format 2 → ["kelime1", "kelime2", ...]
        if isinstance(veri, dict) and "kelimeler" in veri:
            _SOZLUK_BELLEGI = {k.lower() for k in veri["kelimeler"]}
        elif isinstance(veri, list):
            _SOZLUK_BELLEGI = {k.lower() for k in veri}
        else:
            kayit_tutuyucu.error("Sozluk formati tanimlanamadi.")
            _SOZLUK_BELLEGI = set()

        kayit_tutuyucu.info("Yerel sozluk yuklendi: %d kelime", len(_SOZLUK_BELLEGI))
        return _SOZLUK_BELLEGI

    except (json.JSONDecodeError, IOError) as hata:
        kayit_tutuyucu.error("Sozluk yuklenirken hata: %s", hata)
        _SOZLUK_BELLEGI = set()
        return _SOZLUK_BELLEGI


# ─────────────────────────────────────────────────────────────────────────────
# Yardımcı: Kelime Varlık Kontrolü
# ─────────────────────────────────────────────────────────────────────────────

def _kelime_mevcut_mu(kelime: str) -> bool:
    """Verilen kelimeyi yerel sözlükte arar. True → mevcut, False → yok."""
    sozluk = _yerel_sozlugu_yukle()
    return kelime.lower() in sozluk


# ─────────────────────────────────────────────────────────────────────────────
# Word Belgesi Düzenleme
# ─────────────────────────────────────────────────────────────────────────────

def _belgeyi_cevrimdisi_kontrol_et(belge_yolu: str) -> None:
    """
    Word belgesindeki kelimeleri yerel sözlük ile karşılaştırır.
    Sözlükte bulunmayanları [!] etiketiyle işaretler ve yeni dosya kaydeder.

    Parametreler:
        belge_yolu: .docx dosyasının tam yolu.
    """
    yol = Path(belge_yolu)
    if not yol.exists():
        print(f"  [HATA] Dosya bulunamadi: {belge_yolu}")
        return

    sozluk = _yerel_sozlugu_yukle()
    if not sozluk:
        print("  [UYARI] Sozluk bos, belge kontrolu yapilamiyor.")
        return

    belge = Document(belge_yolu)
    hatali_kelime_sayisi = 0

    for paragraf in belge.paragraphs:
        bulunan_kelimeler = re.findall(r"\b[a-zA-ZçÇğĞıİöÖşŞüÜ]+\b", paragraf.text)
        for kelime in bulunan_kelimeler:
            if not _kelime_mevcut_mu(kelime):
                paragraf.text = paragraf.text.replace(kelime, f"{kelime}[!]", 1)
                hatali_kelime_sayisi += 1

    kayit_yolu = yol.parent / f"{yol.stem}_cevrimdisi_duzenlendi{yol.suffix}"
    belge.save(kayit_yolu)
    print(f"  [TAMAM] Belge (cevrimdisi) duzenlendi: {kayit_yolu}")
    print(f"  [BILGI] Supheli kelime sayisi: {hatali_kelime_sayisi}")


# ─────────────────────────────────────────────────────────────────────────────
# Ana Giriş Noktası
# ─────────────────────────────────────────────────────────────────────────────

def tdk_cevrimdisi_kontrol(komut: str) -> None:
    """
    Çevrimdışı TDK modülünün ana fonksiyonu.
    Komutta .docx yolu varsa belgeyi işler; yoksa tekil kelime kontrolü yapar.

    Parametreler:
        komut: Kullanıcıdan gelen komut metni.
    """
    print("  [TDK CEVRIMDISI] Yerel sozluk veritabani kullaniliyor...")

    # Komutta .docx dosya yolu var mı?
    docx_eslesmesi = re.search(r'[\w/\\:. -]+\.docx', komut, re.IGNORECASE)
    if docx_eslesmesi:
        bulunan_belge_yolu = docx_eslesmesi.group(0).strip()
        print(f"  [BELGE] Hedef belge: {bulunan_belge_yolu}")
        _belgeyi_cevrimdisi_kontrol_et(bulunan_belge_yolu)
        return

    # Tekil kelime kontrolü
    kontrol_edilecek_kelimeler = [k for k in komut.split() if len(k) > 2]
    kontrol_sayisi = 0

    for ham_kelime in kontrol_edilecek_kelimeler:
        temiz_kelime = re.sub(r"[^a-zA-ZçÇğĞıİöÖşŞüÜ]", "", ham_kelime)
        if not temiz_kelime:
            continue
        mevcut_mu = _kelime_mevcut_mu(temiz_kelime)
        durum = "mevcut" if mevcut_mu else "bulunamadi"
        print(f"  [KELIME] '{temiz_kelime}' → Yerel sozlukte {durum}")
        kontrol_sayisi += 1

    if kontrol_sayisi == 0:
        print("  [BILGI] Kontrol edilecek kelime bulunamadi.")
