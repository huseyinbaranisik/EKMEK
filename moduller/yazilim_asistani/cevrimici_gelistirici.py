"""
moduller/yazilim_asistani/cevrimici_gelistirici.py — Ekmek AI Asistan

Çevrimiçi Yazılım Asistanı — iki kaynaktan arama yapar:
  1. StackOverflow API — en çok oylanan soruları listeler
  2. GitHub Arama API — en yıldızlı repoları listeler
  Desteklenen diller: Python, React, React Native
"""

import logging
from typing import Optional

import requests

from ayarlar import STACKOVERFLOW_API_ADRESI, GITHUB_ARAMA_API

kayit_tutuyucu = logging.getLogger(__name__)

# ── Dil → API etiket/filtre eşlemesi ─────────────────────────────────────────
# Her dil için (StackOverflow etiketi, GitHub dil filtresi) çifti tanımlanır.
DIL_ETIKET_ESLESMESI = {
    "python":       ("python",      "Python"),
    "react native": ("react-native","JavaScript"),
    "react":        ("reactjs",     "JavaScript"),
}

# Sorgu oluştururken çıkarılacak gereksiz kelimeler
GEREKSIZ_KELIMELER = {
    "python", "react", "native", "icin", "nasil", "yap",
    "bul", "goster", "asistan", "kod", "hata", "duzelt", "ekmek",
}


# ─────────────────────────────────────────────────────────────────────────────
# StackOverflow Arama
# ─────────────────────────────────────────────────────────────────────────────

def _stackoverflow_ara(sorgu: str, etiket: str, sonuc_adedi: int = 3) -> None:
    """
    StackExchange API v2.3 üzerinden StackOverflow'da soru arar.

    Parametreler:
        sorgu      : Aranacak ifade.
        etiket     : StackOverflow filtre etiketi (python, reactjs …).
        sonuc_adedi: Gösterilecek maksimum sonuç sayısı.
    """
    istek_parametreleri = {
        "order":    "desc",
        "sort":     "relevance",
        "q":        sorgu,
        "tagged":   etiket,
        "site":     "stackoverflow",
        "pagesize": sonuc_adedi,
        "filter":   "withbody",
    }
    try:
        yanit = requests.get(STACKOVERFLOW_API_ADRESI, params=istek_parametreleri, timeout=8)
        yanit.raise_for_status()
        sonuclar = yanit.json().get("items", [])

        if not sonuclar:
            print(f"  [BILGI] StackOverflow'da '{sorgu}' icin sonuc bulunamadi.")
            return

        print(f"\n  [STACKOVERFLOW] '{sorgu}' icin en iyi {len(sonuclar)} sonuc:")
        for sira, soru in enumerate(sonuclar, 1):
            baslik      = soru.get("title", "Baslik yok")
            baglanti    = soru.get("link", "")
            puan        = soru.get("score", 0)
            cevaplandi  = "CEVAPLANDI" if soru.get("is_answered") else "CEVAPSIZ"
            print(f"    {sira}. [{cevaplandi}] [{puan} oy] {baslik}")
            print(f"       Baglanti: {baglanti}")

    except requests.RequestException as hata:
        kayit_tutuyucu.error("StackOverflow API hatasi: %s", hata)
        print("  [HATA] StackOverflow'a ulasilamiyor.")


# ─────────────────────────────────────────────────────────────────────────────
# GitHub Arama
# ─────────────────────────────────────────────────────────────────────────────

def _github_ara(sorgu: str, dil_filtresi: Optional[str] = None, sonuc_adedi: int = 3) -> None:
    """
    GitHub Search API üzerinden en yıldızlı repoları arar.

    Parametreler:
        sorgu       : Aranacak ifade.
        dil_filtresi: Programlama dili filtresi (örn. "Python").
        sonuc_adedi : Gösterilecek maksimum sonuç sayısı.
    """
    tam_sorgu = sorgu
    if dil_filtresi:
        tam_sorgu += f" language:{dil_filtresi}"

    istek_parametreleri = {
        "q":        tam_sorgu,
        "sort":     "stars",
        "order":    "desc",
        "per_page": sonuc_adedi,
    }
    istek_basliklar = {"Accept": "application/vnd.github+json"}

    try:
        yanit = requests.get(
            GITHUB_ARAMA_API, params=istek_parametreleri,
            headers=istek_basliklar, timeout=8,
        )
        yanit.raise_for_status()
        sonuclar = yanit.json().get("items", [])

        if not sonuclar:
            print(f"  [BILGI] GitHub'da '{sorgu}' icin sonuc bulunamadi.")
            return

        print(f"\n  [GITHUB] '{sorgu}' icin en iyi {len(sonuclar)} repo:")
        for sira, repo in enumerate(sonuclar, 1):
            repo_adi    = repo.get("full_name", "")
            aciklama    = repo.get("description") or "Aciklama yok"
            yildiz      = repo.get("stargazers_count", 0)
            baglanti    = repo.get("html_url", "")
            print(f"    {sira}. [{yildiz:,} yildiz] {repo_adi}")
            print(f"       {aciklama[:80]}{'...' if len(aciklama) > 80 else ''}")
            print(f"       Baglanti: {baglanti}")

    except requests.RequestException as hata:
        kayit_tutuyucu.error("GitHub API hatasi: %s", hata)
        print("  [HATA] GitHub'a ulasilamiyor.")


# ─────────────────────────────────────────────────────────────────────────────
# Yardımcı: Dil Tespiti
# ─────────────────────────────────────────────────────────────────────────────

def _dil_tespit_et(komut: str) -> tuple[str, str]:
    """
    Komut metninden programlama dilini tespit eder.

    Döndürür:
        (stackoverflow_etiketi, github_dil_filtresi) çifti.
    """
    kucuk_komut = komut.lower()
    for dil_anahtar, (so_etiketi, gh_dil) in DIL_ETIKET_ESLESMESI.items():
        if dil_anahtar in kucuk_komut:
            return so_etiketi, gh_dil
    return "python", "Python"   # varsayılan dil


# ─────────────────────────────────────────────────────────────────────────────
# Ana Giriş Noktası
# ─────────────────────────────────────────────────────────────────────────────

def yazilim_cevrimici_yardim(komut: str) -> None:
    """
    Çevrimiçi yazılım asistanının ana fonksiyonu.
    StackOverflow ve GitHub'dan en güncel çözümleri getirir.

    Parametreler:
        komut: Kullanıcıdan gelen komut metni.
    """
    print("  [YAZILIM CEVRIMICI] Web aramasi baslatiliyor...")

    so_etiketi, gh_dil = _dil_tespit_et(komut)
    print(f"  [DIL] Tespit edilen: {gh_dil} (SO etiketi: #{so_etiketi})")

    # Gereksiz kelimeleri çıkararak temiz bir sorgu oluştur
    anlamli_kelimeler = [
        k for k in komut.split()
        if k.lower() not in GEREKSIZ_KELIMELER and len(k) > 1
    ]
    sorgu = " ".join(anlamli_kelimeler) if anlamli_kelimeler else komut

    _stackoverflow_ara(sorgu, etiket=so_etiketi)
    _github_ara(sorgu, dil_filtresi=gh_dil)
