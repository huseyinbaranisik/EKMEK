/**
 * Ekmek AI Asistan - Arayüz Süreci
 * Kullanıcı etkileşimlerini, ses kaydını ve asistanın yanıtlarını yönetir.
 * Mikrofon modu ve Chat modu arasında geçişi yönetir.
 */

// ── Durum Değişkenleri ─────────────────────────────────────────────────────
let sesAkisi          = null;
let sesKaydedici      = null;
let sesParcalari      = [];
let kayitDevamEdiyor  = false;
let sohbetGecmisi     = [];   // Hem chat hem mikrofon modu ortak geçmiş kullanır
let chatModu          = false;

// ── DOM Referansları ───────────────────────────────────────────────────────
let mikrofonButonu, durumMetni, yanitMetni, gorselDalgalar;
let chatGecBtn, mikGecBtn, chatGirisi, gonderBtn, chatListesi;
let mikrofonModuEl, chatModuEl, anaKonteyner;

// ── Başlangıç ─────────────────────────────────────────────────────────────
window.addEventListener('DOMContentLoaded', arayuzuHazirla);

function arayuzuHazirla() {
    mikrofonButonu  = document.getElementById('mic-btn');
    durumMetni      = document.getElementById('status-text');
    yanitMetni      = document.getElementById('response-text');
    gorselDalgalar  = document.querySelector('.visualizer');
    chatGecBtn      = document.getElementById('chat-gec-btn');
    mikGecBtn       = document.getElementById('mik-gec-btn');
    chatGirisi      = document.getElementById('chat-girisi');
    gonderBtn       = document.getElementById('gonder-btn');
    chatListesi     = document.getElementById('chat-listesi');
    mikrofonModuEl  = document.getElementById('mikrofon-modu');
    chatModuEl      = document.getElementById('chat-modu');
    anaKonteyner    = document.getElementById('ana-konteyner');

    // Kapat butonu — pencereyi tray'e minimize eder
    document.getElementById('kapat-btn')?.addEventListener('click', () => {
        window.electronAPI.pencereyiKapat();
    });

    // Mikrofon butonu
    mikrofonButonu?.addEventListener('click', async () => {
        kayitDevamEdiyor ? kaydiDurdur() : kaydiBaslat();
    });

    // Chat moduna geç
    chatGecBtn?.addEventListener('click', chatModunaGec);

    // Mikrofon moduna geri dön
    mikGecBtn?.addEventListener('click', mikrofonModunaGec);

    // Enter ile mesaj gönder
    chatGirisi?.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            mesajGonder();
        }
    });

    gonderBtn?.addEventListener('click', mesajGonder);

    durumMetni.innerText = "Hazır";

    // Ses API hazır olunca karşılama sesini oku
    window.speechSynthesis.onvoiceschanged = () => {
        konus("Size nasıl yardımcı olabilirim efendim?");
        window.speechSynthesis.onvoiceschanged = null; // Bir kez çalıştır
    };
}

// ═══════════════════════════════════════════════════════════════════════════
//  MOD GEÇİŞ FONKSİYONLARI
// ═══════════════════════════════════════════════════════════════════════════

function chatModunaGec() {
    if (chatModu) return;

    // Kayıt devam ediyorsa önce durdur
    if (kayitDevamEdiyor) kaydiDurdur();

    chatModu = true;
    anaKonteyner.classList.add('chat-aktif');
    chatGecBtn.disabled = true;

    mikrofonModuEl.classList.add('mod-cikiyor');
    mikrofonModuEl.addEventListener('animationend', () => {
        mikrofonModuEl.classList.remove('mod-cikiyor');
        mikrofonModuEl.classList.add('chat-gizli');

        chatModuEl.classList.remove('chat-gizli');
        chatModuEl.classList.add('mod-giriyor');

        chatModuEl.addEventListener('animationend', () => {
            chatModuEl.classList.remove('mod-giriyor');
            chatGirisi?.focus();
            chatGecBtn.disabled = false;
        }, { once: true });
    }, { once: true });
}

function mikrofonModunaGec() {
    if (!chatModu) return;
    chatModu = false;

    chatModuEl.classList.add('mod-cikiyor');
    chatModuEl.addEventListener('animationend', () => {
        chatModuEl.classList.remove('mod-cikiyor');
        chatModuEl.classList.add('chat-gizli');

        mikrofonModuEl.classList.remove('chat-gizli');
        mikrofonModuEl.classList.add('mod-giriyor');
        anaKonteyner.classList.remove('chat-aktif');

        mikrofonModuEl.addEventListener('animationend', () => {
            mikrofonModuEl.classList.remove('mod-giriyor');
        }, { once: true });
    }, { once: true });
}

// ═══════════════════════════════════════════════════════════════════════════
//  CHAT MODU
// ═══════════════════════════════════════════════════════════════════════════

async function mesajGonder() {
    const metin = chatGirisi?.value.trim();
    if (!metin) return;

    chatGirisi.value = '';
    chatGirisi.disabled = true;
    gonderBtn.disabled = true;

    chataBalonEkle('kullanici', metin);
    const yaziyorId = yaziyorGoster();

    sohbetGecmisi.push({ role: "user", content: metin });
    if (sohbetGecmisi.length > 20) sohbetGecmisi.shift();

    try {
        const sonuc = await window.electronAPI.komutuYorumla(sohbetGecmisi);
        yaziyorKaldir(yaziyorId);

        const yanit = sonuc.response;
        chataBalonEkle('asistan', yanit);
        sohbetGecmisi.push({ role: "assistant", content: yanit });

        konus(yanit);

        if (sonuc.action === 'open') {
            await window.electronAPI.uygulamayiBaslat(sonuc.target);
        } else if (sonuc.action === 'system') {
            await window.electronAPI.sistemKontrolu({ tip: sonuc.target, deger: sonuc.value });
        }

    } catch (hata) {
        console.error("Chat hata:", hata);
        yaziyorKaldir(yaziyorId);
        chataBalonEkle('asistan', 'Bağlantı sorunu oluştu efendim, lütfen tekrar deneyin.');
    } finally {
        chatGirisi.disabled = false;
        gonderBtn.disabled = false;
        chatGirisi.focus();
    }
}

/** Chat listesine mesaj balonu ekler. */
function chataBalonEkle(tip, metin) {
    const div = document.createElement('div');
    div.className = `chat-mesaj ${tip}`;

    const balon = document.createElement('div');
    balon.className = 'chat-balon';
    balon.textContent = metin;

    div.appendChild(balon);
    chatListesi.appendChild(div);
    chatListesi.scrollTop = chatListesi.scrollHeight;
}

/** "Yazıyor..." animasyonunu ekler, benzersiz ID döndürür. */
function yaziyorGoster() {
    const id = `yaziyor-${Date.now()}`;
    const div = document.createElement('div');
    div.className = 'chat-mesaj asistan chat-yaziyor';
    div.id = id;

    const balon = document.createElement('div');
    balon.className = 'chat-balon';
    balon.innerHTML = '<span class="nokta"></span><span class="nokta"></span><span class="nokta"></span>';

    div.appendChild(balon);
    chatListesi.appendChild(div);
    chatListesi.scrollTop = chatListesi.scrollHeight;
    return id;
}

/** "Yazıyor..." animasyonunu kaldırır. */
function yaziyorKaldir(id) {
    document.getElementById(id)?.remove();
}

// ═══════════════════════════════════════════════════════════════════════════
//  MİKROFON MODU
// ═══════════════════════════════════════════════════════════════════════════

async function kaydiBaslat() {
    if (kayitDevamEdiyor) return;

    try {
        kayitDevamEdiyor = true;

        if (sesAkisi) {
            sesAkisi.getTracks().forEach(t => t.stop());
        }

        sesAkisi     = await navigator.mediaDevices.getUserMedia({ audio: true });
        sesKaydedici = new MediaRecorder(sesAkisi);
        sesParcalari = [];

        sesKaydedici.ondataavailable = (e) => {
            if (e.data.size > 0) sesParcalari.push(e.data);
        };

        sesKaydedici.onstop = async () => {
            // Mikrofonu serbest bırak
            sesAkisi?.getTracks().forEach(t => t.stop());
            sesAkisi = null;

            const sesBloku      = new Blob(sesParcalari, { type: 'audio/webm' });
            const diziTamponu   = await sesBloku.arrayBuffer();

            durumMetni.innerText = "Düşünülüyor...";
            gorselDalgalar.classList.remove('active');

            const metin = await window.electronAPI.sesiMetneCevir(diziTamponu);

            if (metin?.trim()) {
                komutuIsle(metin);
            } else {
                durumMetni.innerText = "Hazır";
                mikrofonButonu.disabled  = false;
                kayitDevamEdiyor = false;
            }
        };

        sesKaydedici.start();
        mikrofonButonu.classList.add('recording');
        gorselDalgalar.classList.add('active');
        durumMetni.innerText = "Dinleniyor...";
        yanitMetni.innerText = "";

    } catch (hata) {
        console.error("Mikrofon erişim hatası:", hata);
        durumMetni.innerText = "Mikrofona erişilemedi!";
        kayitDevamEdiyor = false;
    }
}

function kaydiDurdur() {
    if (sesKaydedici && sesKaydedici.state !== 'inactive') {
        sesKaydedici.stop();
        kayitDevamEdiyor = false;
        mikrofonButonu.classList.remove('recording');
        mikrofonButonu.disabled = true;
    }
}

async function komutuIsle(metin) {
    sohbetGecmisi.push({ role: "user", content: metin });
    if (sohbetGecmisi.length > 20) sohbetGecmisi.shift();

    try {
        const sonuc = await window.electronAPI.komutuYorumla(sohbetGecmisi);

        yanitMetni.innerText = sonuc.response;
        sohbetGecmisi.push({ role: "assistant", content: sonuc.response });

        konus(sonuc.response);

        if (sonuc.action === 'open') {
            await window.electronAPI.uygulamayiBaslat(sonuc.target);
        } else if (sonuc.action === 'system') {
            await window.electronAPI.sistemKontrolu({ tip: sonuc.target, deger: sonuc.value });
        }

        durumMetni.innerText = "Hazır";

    } catch (hata) {
        console.error("Komut işleme hatası:", hata);
        durumMetni.innerText = "Bir sorun oluştu.";
    } finally {
        mikrofonButonu.disabled = false;
        kayitDevamEdiyor = false;
    }
}

// ═══════════════════════════════════════════════════════════════════════════
//  SES OKUMA
// ═══════════════════════════════════════════════════════════════════════════

function konus(metin) {
    window.speechSynthesis.cancel();

    const ses = new SpeechSynthesisUtterance(metin);
    ses.lang  = 'tr-TR';
    ses.rate  = 1.1;
    ses.pitch = 1.0;

    const sesler     = window.speechSynthesis.getVoices();
    const turkceSes  = sesler.find(s => s.lang.startsWith('tr'));
    if (turkceSes) ses.voice = turkceSes;

    window.speechSynthesis.speak(ses);
}
