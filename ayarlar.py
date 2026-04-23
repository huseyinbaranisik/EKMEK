# =============================================================================
# ayarlar.py — Ekmek AI Asistan | Merkezi Yapılandırma Dosyası
# Tüm sabit değerler ve ayarlar bu tek dosyada toplanmıştır.
# =============================================================================

# ── Uyanma Kelimesi ───────────────────────────────────────────────────────────
UYANMA_KELIMESI: str = "ekmek"           # Asistanı uyandıran tetikleyici kelime

# ── Bağlantı Kontrolü ─────────────────────────────────────────────────────────
BAGLANTI_TEST_SUNUCUSU: str = "8.8.8.8"  # Google DNS — bağlantı testi için
BAGLANTI_TEST_PORTU: int = 53             # DNS portu
BAGLANTI_ZAMAN_ASIMI: float = 1.0        # Saniye cinsinden zaman aşımı süresi

# ── TDK Modülü ────────────────────────────────────────────────────────────────
TDK_ADRESI: str = "https://sozluk.gov.tr/"
YEREL_SOZLUK_YOLU: str = "veri/sozluk.json"   # Offline sözlük dosyasının yolu

# ── Yazılım Asistanı ──────────────────────────────────────────────────────────
DESTEKLENEN_DILLER: list[str] = ["python", "react", "react native"]
STACKOVERFLOW_API_ADRESI: str = "https://api.stackexchange.com/2.3/search/advanced"
GITHUB_ARAMA_API: str = "https://api.github.com/search/repositories"

# ── Ollama (Çevrimdışı Yerel Model) ───────────────────────────────────────────
OLLAMA_SUNUCU_ADRESI: str = "http://localhost:11434"
OLLAMA_MODEL_ADI: str = "llama3"          # Kurulu modele göre değiştirin

# ── Ses / Konuşma Tanıma ──────────────────────────────────────────────────────
KONUSMA_DILI: str = "tr-TR"
MIKROFON_ENERJI_ESIGI: int = 300          # Sessiz ortam için düşürün
MIKROFON_DURUS_ESIGI: float = 0.8         # Konuşma duraklamasını belirler

# ── Sesli Yanıt (TTS) Ayarları ───────────────────────────────────────────────
SES_HIZI: int = 180              # Jarvis hızı (150-200 idealdir)
SES_DUZEYI: float = 1.0          # 0.0 ile 1.0 arası
SES_CINSIYET: str = "erkek"      # "erkek" veya "kadin"

# ── Antigravity Otomasyon Ayarları ───────────────────────────────────────────
RETRY_BUTON_RENK: str = "#0078d4" # Mavi retry butonu tahmini rengi
DEGISIKLIK_KABUL_RENK: str = "#28a745" # Yeşil kabul butonu tahmini rengi

# ── Genel ─────────────────────────────────────────────────────────────────────
HATA_AYIKLAMA_MODU: bool = True           # True → ayrıntılı log çıktısı
SURUM: str = "0.1.0"
