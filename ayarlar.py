# =============================================================================
# ayarlar.py - Ekmek AI Asistan | Merkezi Yapilandirma Dosyasi
# Tum sabit degerler ve ayarlar bu tek dosyada toplanmistir.
# =============================================================================

# -- Uyanma Kelimesi -----------------------------------------------------------
UYANMA_KELIMESI: str = "ekmek"           # Asistani uyandiran tetikleyici kelime

# -- Baglanti Kontrolu ---------------------------------------------------------
BAGLANTI_TEST_SUNUCUSU: str = "8.8.8.8"  # Google DNS - baglanti testi icin
BAGLANTI_TEST_PORTU: int = 53             # DNS portu
BAGLANTI_ZAMAN_ASIMI: float = 1.0        # Saniye cinsinden zaman asimi suresi

# -- TDK Modulu ----------------------------------------------------------------
TDK_ADRESI: str = "https://sozluk.gov.tr/"
YEREL_SOZLUK_YOLU: str = "veri/sozluk.json"   # Offline sozluk dosyasinin yolu

# -- Yazilim Asistani ----------------------------------------------------------
DESTEKLENEN_DILLER: list[str] = ["python", "react", "react native"]
STACKOVERFLOW_API_ADRESI: str = "https://api.stackexchange.com/2.3/search/advanced"
GITHUB_ARAMA_API: str = "https://api.github.com/search/repositories"

# -- Ollama (Cevrimdisi Yerel Model) -------------------------------------------
OLLAMA_SUNUCU_ADRESI: str = "http://localhost:11434"
OLLAMA_MODEL_ADI: str = "llama3"          # Kurulu modele gore degistirin

# -- Ses / Konusma Tanima ------------------------------------------------------
KONUSMA_DILI: str = "tr-TR"
MIKROFON_ENERJI_ESIGI: int = 300          # Sessiz ortam icin dusurun
MIKROFON_DURUS_ESIGI: float = 0.8         # Konusma duraklamasini belirler

# -- Sesli Yanit (TTS) Ayarlari -----------------------------------------------
SES_HIZI: int = 180              # Jarvis hizi (150-200 idealdir)
SES_DUZEYI: float = 1.0          # 0.0 ile 1.0 arasi
SES_CINSIYET: str = "erkek"      # "erkek" veya "kadin"

# -- Antigravity Otomasyon Ayarlari -------------------------------------------
RETRY_BUTON_RENK: str = "#0078d4" # Mavi retry butonu tahmini rengi
DEGISIKLIK_KABUL_RENK: str = "#28a745" # Yesil kabul butonu tahmini rengi

# -- Genel ---------------------------------------------------------------------
HATA_AYIKLAMA_MODU: bool = True           # True -> ayrintili log ciktisi
SURUM: str = "0.1.0"
