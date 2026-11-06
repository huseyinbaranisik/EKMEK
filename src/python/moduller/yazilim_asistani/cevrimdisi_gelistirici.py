"""
moduller/yazilim_asistani/cevrimdisi_gelistirici.py — Ekmek AI Asistan

Çevrimdışı Yazılım Asistanı:
  • Ollama HTTP API üzerinden yerel LLM modeline istek gönderir (streaming)
  • İnternet gerektirmez — localhost:11434 üzerinde çalışır
  • Desteklenen diller: Python, React, React Native
"""

import json
import logging
import urllib.request
import urllib.error
from typing import Optional

from ayarlar import OLLAMA_SUNUCU_ADRESI, OLLAMA_MODEL_ADI

kayit_tutuyucu = logging.getLogger(__name__)

# ── Dil → Sistem Talimatı Eşlemesi ───────────────────────────────────────────
# Ollama modeline gönderilen sistem rolü — modeli ilgili dile odaklar.
DIL_SISTEM_TALIMATLARI = {
    "python":       "Sen deneyimli bir Python geliştiricisisin. Türkçe yanıt ver.",
    "react native": "Sen deneyimli bir React Native geliştiricisisin. Türkçe yanıt ver.",
    "react":        "Sen deneyimli bir React.js geliştiricisisin. Türkçe yanıt ver.",
}
VARSAYILAN_SISTEM_TALIMATI = "Sen deneyimli bir yazilim geliştiricisisin. Türkçe yanıt ver."


# ─────────────────────────────────────────────────────────────────────────────
# Yardımcı: Dil Bağlamı Tespiti
# ─────────────────────────────────────────────────────────────────────────────

def _dil_baglami_tespit_et(komut: str) -> str:
    """Komut metnine göre uygun sistem talimatını döndürür."""
    kucuk_komut = komut.lower()
    for dil_anahtar, sistem_talimati in DIL_SISTEM_TALIMATLARI.items():
        if dil_anahtar in kucuk_komut:
            return sistem_talimati
    return VARSAYILAN_SISTEM_TALIMATI


# ─────────────────────────────────────────────────────────────────────────────
# Ollama API Çağrısı (Akan / Streaming)
# ─────────────────────────────────────────────────────────────────────────────

def _ollama_cagir(sistem_talimati: str, kullanici_sorusu: str) -> Optional[str]:
    """
    Ollama'nın /api/chat endpoint'ini çağırarak yerel LLM'den yanıt alır.
    Yanıt token token (streaming) ekrana yazdırılır.

    Parametreler:
        sistem_talimati : Modelin rolünü belirleyen sistem mesajı.
        kullanici_sorusu: Kullanıcının soru veya komut metni.

    Döndürür:
        Modelin ürettiği tam yanıt metni; hata durumunda None.
    """
    istek_adresi = f"{OLLAMA_SUNUCU_ADRESI}/api/chat"
    istek_verisi = {
        "model":    OLLAMA_MODEL_ADI,
        "stream":   True,
        "messages": [
            {"role": "system", "content": sistem_talimati},
            {"role": "user",   "content": kullanici_sorusu},
        ],
    }
    kodlanmis_veri = json.dumps(istek_verisi).encode("utf-8")
    http_istegi = urllib.request.Request(
        istek_adresi,
        data=kodlanmis_veri,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        tam_yanit_parcalari = []
        print(f"\n  [YEREL MODEL] Ollama [{OLLAMA_MODEL_ADI}] yanitliyor...\n  ", end="", flush=True)

        with urllib.request.urlopen(http_istegi, timeout=60) as acik_baglanti:
            for ham_satir in acik_baglanti:
                satir = ham_satir.decode("utf-8").strip()
                if not satir:
                    continue
                try:
                    yanit_parcasi = json.loads(satir)
                    token = yanit_parcasi.get("message", {}).get("content", "")
                    print(token, end="", flush=True)
                    tam_yanit_parcalari.append(token)
                    if yanit_parcasi.get("done"):
                        break
                except json.JSONDecodeError:
                    continue

        print()   # Satır sonu
        return "".join(tam_yanit_parcalari)

    except urllib.error.URLError as hata:
        kayit_tutuyucu.error("Ollama'ya baglanilmadi: %s", hata)
        return None
    except TimeoutError:
        kayit_tutuyucu.error("Ollama zaman asimi.")
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Ana Giriş Noktası
# ─────────────────────────────────────────────────────────────────────────────

def yazilim_cevrimdisi_yardim(komut: str) -> None:
    """
    Çevrimdışı yazılım asistanının ana fonksiyonu.
    Ollama yerel modeline soruyu iletir ve yanıtı ekrana yazar.

    Parametreler:
        komut: Kullanıcıdan gelen komut metni.
    """
    print(f"  [YAZILIM CEVRIMDISI] Yerel model ({OLLAMA_MODEL_ADI}) devrede...")

    secilen_sistem_talimati = _dil_baglami_tespit_et(komut)

    alinan_yanit = _ollama_cagir(secilen_sistem_talimati, komut)

    if alinan_yanit is None:
        print(f"\n  [HATA] Ollama'ya ulasilamiyor.")
        print(f"  [IPUCU] 'ollama serve' komutuyla Ollama'yi baslatın.")
        print(f"  [IPUCU] 'ollama pull {OLLAMA_MODEL_ADI}' komutuyla modeli indirin.")
    else:
        kayit_tutuyucu.info("Ollama yaniti alindi (%d karakter).", len(alinan_yanit))
