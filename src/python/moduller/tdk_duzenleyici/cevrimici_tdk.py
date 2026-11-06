"""
moduller/tdk_duzenleyici/cevrimici_tdk.py — Ekmek AI Asistan

Çevrimiçi TDK modülü — iki işlev sunar:
  1. TDK Güncel Türkçe Sözlük API'si üzerinden tek kelime doğrulama
  2. python-docx ile Word belgesindeki şüpheli kelimeleri [?] ile işaretleme
"""

import logging
import re
from pathlib import Path
from typing import Optional

import requests
from docx import Document

from ayarlar import TDK_ADRESI

kayit_tutuyucu = logging.getLogger(__name__)

# TDK'nın resmi, ücretsiz JSON API adresi
TDK_API_ADRESI = "https://sozluk.gov.tr/gts"


# ─────────────────────────────────────────────────────────────────────────────
# Yardımcı: TDK API Sorgulama
# ─────────────────────────────────────────────────────────────────────────────

def _tdk_sorgula(kelime: str) -> Optional[dict]:
    """
    TDK Güncel Türkçe Sözlük JSON API'sini sorgular.

    Parametreler:
        kelime: Sorgulanacak kelime.

    Döndürür:
        API'den dönen veri sözlüğü; kelime bulunamazsa None.
    """
    try:
        sorgu_parametreleri = {"ara": kelime}
        istek_basliklar = {
            "User-Agent": "EkmekAIAsistan/0.1 (egitim projesi)",
            "Referer": TDK_ADRESI,
        }
        yanit = requests.get(
            TDK_API_ADRESI,
            params=sorgu_parametreleri,
            headers=istek_basliklar,
            timeout=5,
        )
        yanit.raise_for_status()
        veri = yanit.json()

        # API boş liste döndürürse kelime sözlükte yok demektir
        if isinstance(veri, list) and len(veri) > 0:
            return veri[0]
        return None

    except requests.RequestException as hata:
        kayit_tutuyucu.error("TDK API istegi basarisiz: %s", hata)
        return None
    except ValueError as hata:
        kayit_tutuyucu.error("TDK API yaniti JSON degil: %s", hata)
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Word Belgesi Düzenleme
# ─────────────────────────────────────────────────────────────────────────────

def _belgeyi_kontrol_et_ve_duzenle(belge_yolu: str) -> None:
    """
    Word belgesindeki her kelimeyi TDK API ile kontrol eder.
    Sözlükte bulunmayanları [?] etiketiyle işaretler ve yeni dosya kaydeder.

    Parametreler:
        belge_yolu: .docx dosyasının tam yolu.
    """
    yol = Path(belge_yolu)
    if not yol.exists():
        print(f"  [HATA] Dosya bulunamadi: {belge_yolu}")
        return

    belge = Document(belge_yolu)
    hatali_kelime_sayisi = 0

    for paragraf in belge.paragraphs:
        bulunan_kelimeler = re.findall(r"\b[a-zA-ZçÇğĞıİöÖşŞüÜ]+\b", paragraf.text)
        for kelime in bulunan_kelimeler:
            sorgu_sonucu = _tdk_sorgula(kelime.lower())
            if sorgu_sonucu is None:
                paragraf.text = paragraf.text.replace(kelime, f"{kelime}[?]", 1)
                hatali_kelime_sayisi += 1
                kayit_tutuyucu.info("TDK'da bulunamadi: %s", kelime)

    kayit_yolu = yol.parent / f"{yol.stem}_tdk_duzenlendi{yol.suffix}"
    belge.save(kayit_yolu)
    print(f"  [TAMAM] Belge duzenlendi: {kayit_yolu}")
    print(f"  [BILGI] Supheli kelime sayisi: {hatali_kelime_sayisi}")


# ─────────────────────────────────────────────────────────────────────────────
# Ana Giriş Noktası
# ─────────────────────────────────────────────────────────────────────────────

def tdk_cevrimici_kontrol(komut: str) -> None:
    """
    Çevrimiçi TDK modülünün ana fonksiyonu.
    Komutta .docx yolu varsa belgeyi işler; yoksa tekil kelime kontrolü yapar.

    Parametreler:
        komut: Kullanıcıdan gelen komut metni.
    """
    print("  [TDK CEVRIMICI] TDK API uzerinden kelime dogrulama basladi...")

    # Komutta .docx dosya yolu var mı?
    docx_eslesmesi = re.search(r'[\w/\\:. -]+\.docx', komut, re.IGNORECASE)
    if docx_eslesmesi:
        bulunan_belge_yolu = docx_eslesmesi.group(0).strip()
        print(f"  [BELGE] Hedef belge: {bulunan_belge_yolu}")
        _belgeyi_kontrol_et_ve_duzenle(bulunan_belge_yolu)
        return

    # Tekil kelime kontrolü — komuttaki 3 harften uzun kelimeleri sorgula
    kontrol_edilecek_kelimeler = [k for k in komut.split() if len(k) > 2]
    kontrol_sayisi = 0

    for ham_kelime in kontrol_edilecek_kelimeler:
        temiz_kelime = re.sub(r"[^a-zA-ZçÇğĞıİöÖşŞüÜ]", "", ham_kelime)
        if not temiz_kelime:
            continue
        sorgu_sonucu = _tdk_sorgula(temiz_kelime.lower())
        durum = "bulundu" if sorgu_sonucu else "bulunamadi"
        print(f"  [KELIME] '{temiz_kelime}' → TDK'da {durum}")
        kontrol_sayisi += 1

    if kontrol_sayisi == 0:
        print("  [BILGI] Kontrol edilecek kelime bulunamadi.")
