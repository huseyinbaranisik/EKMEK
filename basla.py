"""
basla.py — Ekmek AI Asistan | Ana Başlangıç Noktası
====================================================

Çalıştırma:
    py basla.py            → Mikrofon modu (gerçek kullanım)
    py basla.py --metin    → Klavye modu  (geliştirme ve test)
    py basla.py --debug    → Ayrıntılı log çıktısı

Gereksinimler:
    pip install -r gereksinimler.txt
"""

import sys
import time
import logging
import argparse
from typing import Optional

# ── Windows Terminal UTF-8 Zorunluluğu ───────────────────────────────────────
# cp1254/cp850 gibi dar karakter kodlamaları emoji ve Türkçe karakterleri
# kırar. Bunu önlemek için stdout/stderr UTF-8'e zorlanır.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ── Proje İçi Modüller ────────────────────────────────────────────────────────
from ayarlar import (
    UYANMA_KELIMESI,
    HATA_AYIKLAMA_MODU,
    SURUM,
    KONUSMA_DILI,
    MIKROFON_ENERJI_ESIGI,
    MIKROFON_DURUS_ESIGI,
)
from cekirdek.baglanti_kontrol import baglanti_kontrol_et
from cekirdek.yonlendirici import komutu_yonlendir
from cekirdek.sesli_yanit import konustur, selam_ver
from arayuz.ana_pencere import arayuz_thread_baslat, ekmek_gui


# ─────────────────────────────────────────────────────────────────────────────
# Loglama Yapılandırması
# ─────────────────────────────────────────────────────────────────────────────

def _loglama_ayarla(hata_ayiklama: bool = False) -> None:
    """
    Konsol log çıktısını yapılandırır.
    colorlog kuruluysa renkli çıktı, kurulu değilse düz metin kullanılır.

    Parametreler:
        hata_ayiklama: True ise DEBUG seviyesi, False ise INFO seviyesi.
    """
    seviye   = logging.DEBUG if hata_ayiklama else logging.INFO
    bicimleme = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    zaman_bicimi = "%H:%M:%S"

    try:
        import colorlog  # pip install colorlog
        isleyici = colorlog.StreamHandler()
        isleyici.setFormatter(colorlog.ColoredFormatter(
            f"%(log_color)s{bicimleme}",
            datefmt=zaman_bicimi,
            log_colors={
                "DEBUG":    "cyan",
                "INFO":     "green",
                "WARNING":  "yellow",
                "ERROR":    "red",
                "CRITICAL": "bold_red",
            },
        ))
        logging.basicConfig(level=seviye, handlers=[isleyici])
    except ImportError:
        logging.basicConfig(level=seviye, format=bicimleme, datefmt=zaman_bicimi)


kayit_tutuyucu = logging.getLogger("ekmek.basla")


# ─────────────────────────────────────────────────────────────────────────────
# Başlık Ekranı
# ─────────────────────────────────────────────────────────────────────────────

def _baslik_yazdir() -> None:
    """Asistan başladığında kullanıcıya bilgi veren başlık metnini yazar."""
    internet_durumu = baglanti_kontrol_et()
    baslangic_modu  = "[CEVRIMICI]" if internet_durumu else "[CEVRIMDISI]"
    ayrac = "=" * 54
    print(f"""
+{ayrac}+
|   EKMEK AI Asistan  --  v{SURUM:<27}|
|   Uyanma kelimesi  : '{UYANMA_KELIMESI}'                           |
|   Baslangic modu   : {baslangic_modu:<33}|
|   Cikis icin       : Ctrl+C  veya  'cikis' yazin     |
+{ayrac}+
""")


# ─────────────────────────────────────────────────────────────────────────────
# Ses Tanıma (Mikrofon → Metin)
# ─────────────────────────────────────────────────────────────────────────────

def _mikrofon_dinle() -> Optional[str]:
    """
    Mikrofonu açar, kullanıcı konuşmasını kaydeder ve metne dönüştürür.
    İnternet varsa Google STT, yoksa Sphinx offline STT kullanır.

    Döndürür:
        Tanınan komut metni; ses yoksa veya tanınamadıysa None.
    """
    try:
        import speech_recognition as sr
    except ImportError:
        kayit_tutuyucu.error(
            "SpeechRecognition kurulu degil: pip install SpeechRecognition pyaudio"
        )
        return None

    ses_tanici = sr.Recognizer()
    ses_tanici.energy_threshold         = MIKROFON_ENERJI_ESIGI
    ses_tanici.pause_threshold          = MIKROFON_DURUS_ESIGI
    ses_tanici.dynamic_energy_threshold = True   # Ortam sesine otomatik uyum

    try:
        with sr.Microphone() as mikrofon_kaynagi:
            print("  [MIC] Dinleniyor... (konusun)")
            # Önce ortam gürültüsüne uyum sağla (0.5 saniye)
            ses_tanici.adjust_for_ambient_noise(mikrofon_kaynagi, duration=0.5)
            ses_kaydi = ses_tanici.listen(
                mikrofon_kaynagi,
                timeout=8,              # 8 saniye ses beklenir
                phrase_time_limit=15,   # Tek cümle en fazla 15 saniye
            )

        # İnternet varsa bulut STT, yoksa yerel Sphinx
        if baglanti_kontrol_et():
            tanınan_metin = ses_tanici.recognize_google(ses_kaydi, language=KONUSMA_DILI)
        else:
            try:
                tanınan_metin = ses_tanici.recognize_sphinx(ses_kaydi, language="tr-TR")
            except sr.RequestError:
                kayit_tutuyucu.warning(
                    "Sphinx (offline STT) kurulu degil. "
                    "Alternatif: pip install openai-whisper"
                )
                return None

        kayit_tutuyucu.debug("Mikrofon tanidi: '%s'", tanınan_metin)
        return tanınan_metin.lower()

    except sr.WaitTimeoutError:
        kayit_tutuyucu.debug("Ses bekleme suresi doldu.")
        return None
    except sr.UnknownValueError:
        kayit_tutuyucu.debug("Ses anlasilamiyor.")
        return None
    except sr.RequestError as hata:
        kayit_tutuyucu.warning("STT servisi hatasi: %s", hata)
        return None
    except OSError as hata:
        kayit_tutuyucu.error("Mikrofon erisim hatasi: %s", hata)
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Uyanma Kelimesi Yardımcıları
# ─────────────────────────────────────────────────────────────────────────────

def _uyanma_kelimesi_var_mi(metin: str) -> bool:
    """Metinde uyanma kelimesi geçiyor mu? (Büyük/küçük harf duyarsız)"""
    return UYANMA_KELIMESI.lower() in metin.lower()


def _uyanma_kelimesini_temizle(metin: str) -> str:
    """Metin içindeki uyanma kelimesini çıkarır ve boşlukları düzeltir."""
    return metin.lower().replace(UYANMA_KELIMESI.lower(), "").strip()


# ─────────────────────────────────────────────────────────────────────────────
# Ana Döngü — Mikrofon Modu
# ─────────────────────────────────────────────────────────────────────────────

def sesli_mod_dongusu() -> None:
    """
    Sürekli çalışan sesli komut dinleme döngüsü.
    Uyanma kelimesi duyulduğunda komut yönlendiricisine iletir.
    try-except bloğu sayesinde internet kesilse bile asistan çökmez.
    """
    kayit_tutuyucu.info(
        "[SESLI MOD] Uyanma kelimesi bekleniyor: '%s'", UYANMA_KELIMESI
    )

    while True:   # ← Sonsuz dinleme döngüsü
        try:
            ham_metin = _mikrofon_dinle()

            if ham_metin is None:
                continue   # Ses gelmedi veya anlaşılamadı → tekrar dinle

            kayit_tutuyucu.debug("Ham ses metni: '%s'", ham_metin)

            # ── Çıkış komutu kontrolü ────────────────────────────────────────
            cikis_kelimeleri = ("cikis", "kapat", "dur", "exit", "quit")
            if any(cikis in ham_metin for cikis in cikis_kelimeleri):
                print("\nEkmek asistan kapatiliyor. Gule gule!")
                break

            # ── Uyanma kelimesi kontrolü ─────────────────────────────────────
            if not _uyanma_kelimesi_var_mi(ham_metin):
                kayit_tutuyucu.debug("Uyanma kelimesi yok, bekleniyor...")
                continue

            islenecek_komut = _uyanma_kelimesini_temizle(ham_metin)
            if not islenecek_komut:
                konustur("Efendim?")
                ekmek_gui.mesaj_ekle("Sistem", "Uyanma kelimesi algilandi.")
                continue

            print(f"\n  [KOMUT] Alindi: '{islenecek_komut}'")
            ekmek_gui.mesaj_ekle("Siz", islenecek_komut)
            komutu_yonlendir(islenecek_komut)
            print()

        except KeyboardInterrupt:
            print("\n\nCtrl+C ile cikild. Ekmek asistan kapatiliyor...")
            break
        except Exception as beklenmedik_hata:   # ← Asistan hiçbir zaman çökmez!
            kayit_tutuyucu.error(
                "Beklenmedik hata (dongu devam ediyor): %s",
                beklenmedik_hata,
                exc_info=HATA_AYIKLAMA_MODU,
            )
            time.sleep(1)   # Kısa bekleme sonrası döngü yeniden başlar


# ─────────────────────────────────────────────────────────────────────────────
# Ana Döngü — Klavye (Metin) Modu
# ─────────────────────────────────────────────────────────────────────────────

def metin_mod_dongusu() -> None:
    """
    Mikrofon gerektirmeyen klavye modlu komut döngüsü.
    Geliştirme ve test ortamı için uygundur.
    """
    kayit_tutuyucu.info("[METIN MOD] Baslatildi.")
    print(f"  [IPUCU] Komutu '{UYANMA_KELIMESI} <komutunuz>' seklinde yazin.\n")

    while True:
        try:
            girilen_metin = input("  [Ekmek]> ").strip()

            if not girilen_metin:
                continue

            # ── Çıkış komutu ─────────────────────────────────────────────────
            if girilen_metin.lower() in ("cikis", "exit", "quit", "q"):
                print("\nEkmek asistan kapatiliyor. Gule gule!")
                break

            # ── Uyanma kelimesi (metin modunda isteğe bağlı) ─────────────────
            if _uyanma_kelimesi_var_mi(girilen_metin):
                islenecek_komut = _uyanma_kelimesini_temizle(girilen_metin)
            else:
                islenecek_komut = girilen_metin   # Doğrudan komut kabul edilir

            if not islenecek_komut:
                print("  [?] Bos komut. Bir seyler yazin.")
                continue

            komutu_yonlendir(islenecek_komut)
            print()

        except KeyboardInterrupt:
            print("\n\nCtrl+C ile cikild. Ekmek asistan kapatiliyor...")
            break
        except EOFError:
            break
        except Exception as beklenmedik_hata:   # ← Asistan hiçbir zaman çökmez!
            kayit_tutuyucu.error(
                "Beklenmedik hata (dongu devam ediyor): %s",
                beklenmedik_hata,
                exc_info=HATA_AYIKLAMA_MODU,
            )
            time.sleep(0.5)


# ─────────────────────────────────────────────────────────────────────────────
# Giriş Noktası
# ─────────────────────────────────────────────────────────────────────────────

def basla() -> None:
    """Komut satırı argümanlarını ayrıştırır ve uygun döngüyü başlatır."""
    arg_ayristirici = argparse.ArgumentParser(
        description="Ekmek — Hibrit Kisisel AI Asistan",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Ornekler:\n"
            "  py basla.py             -> Mikrofon modu\n"
            "  py basla.py --metin     -> Klavye modu (gelistirme/test)\n"
            "  py basla.py --debug     -> Ayrintili log ciktisi\n"
        ),
    )
    arg_ayristirici.add_argument(
        "--metin", "-m",
        action="store_true",
        help="Mikrofon yerine klavyeden komut al (gelistirme modu)",
    )
    arg_ayristirici.add_argument(
        "--debug", "-d",
        action="store_true",
        default=HATA_AYIKLAMA_MODU,
        help="DEBUG seviyesinde loglama etkinlestir",
    )
    alinan_argümanlar = arg_ayristirici.parse_args()

    _loglama_ayarla(hata_ayiklama=alinan_argümanlar.debug)
    _baslik_yazdir()

    # Arayüzü ve TTS başlangıcını tetikle
    arayuz_thread_baslat()
    selam_ver()

    if alinan_argümanlar.metin:
        metin_mod_dongusu()
    else:
        sesli_mod_dongusu()


if __name__ == "__main__":
    basla()
