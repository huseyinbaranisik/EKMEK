/**
 * Ekmek AI Asistan — Mobil Uzak Kontrol JS
 * Telefon arayüzünün tüm mantığını yönetir.
 */

// ── Durum ────────────────────────────────────────────────────────────────────
const API = ''; // Aynı sunucu, göreceli URL
let panelAcik = false;
let bagliMi   = false;
let sesGecikme, parlaklikGecikme;

// ── DOM ──────────────────────────────────────────────────────────────────────
const chatListesi     = document.getElementById('chat-listesi');
const mesajGirisi     = document.getElementById('mesaj-girisi');
const gonderBtn       = document.getElementById('gonder-btn');
const baglantiDurumu  = document.getElementById('baglanti-durumu');
const temizleBtn      = document.getElementById('temizle-btn');
const sistemAcBtn     = document.getElementById('sistem-ac-btn');
const sistemPanel     = document.getElementById('sistem-panel');
const panelTutamac    = document.getElementById('panel-tutamac');
const sesKaydirici    = document.getElementById('ses-kaydirici');
const parlaklikKaydirici = document.getElementById('parlaklik-kaydirici');
const sesDeger        = document.getElementById('ses-deger');
const parlaklikDeger  = document.getElementById('parlaklik-deger');

// ── Overlay ──────────────────────────────────────────────────────────────────
const overlay = document.createElement('div');
overlay.className = 'overlay';
document.body.appendChild(overlay);

// ── Bağlantı Kontrolü ────────────────────────────────────────────────────────
async function baglantiKontrol() {
  try {
    const res = await fetch(`${API}/api/saglik`, { signal: AbortSignal.timeout(3000) });
    if (res.ok) {
      bagliMi = true;
      baglantiDurumu.textContent = '✓ Bağlandı';
      baglantiDurumu.classList.add('aktif');
    }
  } catch {
    bagliMi = false;
    baglantiDurumu.textContent = 'Bağlanamadı';
    baglantiDurumu.classList.remove('aktif');
  }
}

// Her 10 saniyede bir kontrol et
baglantiKontrol();
setInterval(baglantiKontrol, 10000);

// ── Mesaj Gönder ─────────────────────────────────────────────────────────────
async function mesajGonder() {
  const metin = mesajGirisi.value.trim();
  if (!metin) return;

  mesajGirisi.value = '';
  gonderBtn.disabled = true;

  balonEkle('kullanici', metin);
  const yaziyorId = yaziyorGoster();

  try {
    const res = await fetch(`${API}/api/komut`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ metin }),
      signal: AbortSignal.timeout(15000)
    });

    const veri = await res.json();
    yaziyorKaldir(yaziyorId);

    if (veri.yanit) {
      balonEkle('asistan', veri.yanit);
    } else if (veri.hata) {
      balonEkle('asistan', `⚠️ ${veri.hata}`);
    }
  } catch (hata) {
    yaziyorKaldir(yaziyorId);
    balonEkle('asistan', '⚠️ Bağlantı hatası. Sunucu çalışıyor mu?');
  } finally {
    gonderBtn.disabled = false;
    mesajGirisi.focus();
  }
}

// ── Hızlı Komutlar ───────────────────────────────────────────────────────────
document.querySelectorAll('.komut-kart').forEach(btn => {
  btn.addEventListener('click', async () => {
    const komut = btn.dataset.komut;
    if (!komut) return;

    btn.classList.add('yukleniyor');
    balonEkle('kullanici', komut);
    const yaziyorId = yaziyorGoster();

    try {
      const res = await fetch(`${API}/api/komut`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ metin: komut }),
        signal: AbortSignal.timeout(10000)
      });

      const veri = await res.json();
      yaziyorKaldir(yaziyorId);
      balonEkle('asistan', veri.yanit || '✓ Komut gönderildi.');

      btn.classList.remove('yukleniyor');
      btn.classList.add('basarili');
      setTimeout(() => btn.classList.remove('basarili'), 1500);

    } catch {
      yaziyorKaldir(yaziyorId);
      balonEkle('asistan', '⚠️ Komut gönderilemedi.');
      btn.classList.remove('yukleniyor');
    }
  });
});

// ── Sistem Kontrolleri ────────────────────────────────────────────────────────
async function sistemKomutu(tip, deger) {
  try {
    await fetch(`${API}/api/sistem`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tip, deger: String(deger) }),
      signal: AbortSignal.timeout(5000)
    });
  } catch (e) {
    console.warn('Sistem komutu hatası:', e.message);
  }
}

// Ses kaydırıcı
sesKaydirici.addEventListener('input', () => {
  sesDeger.textContent = `${sesKaydirici.value}%`;
  clearTimeout(sesGecikme);
  sesGecikme = setTimeout(() => sistemKomutu('ses', sesKaydirici.value), 400);
});

// Parlaklık kaydırıcı
parlaklikKaydirici.addEventListener('input', () => {
  parlaklikDeger.textContent = `${parlaklikKaydirici.value}%`;
  clearTimeout(parlaklikGecikme);
  parlaklikGecikme = setTimeout(() => sistemKomutu('parlaklik', parlaklikKaydirici.value), 400);
});

// Medya butonları
document.getElementById('medya-oynat').addEventListener('click',   () => sistemKomutu('medya_oynat', ''));
document.getElementById('medya-sonraki').addEventListener('click', () => sistemKomutu('medya_sonraki', ''));
document.getElementById('medya-onceki').addEventListener('click',  () => sistemKomutu('medya_onceki', ''));

// ── Panel Aç / Kapat ─────────────────────────────────────────────────────────
function panelAc() {
  panelAcik = true;
  sistemPanel.classList.add('acik');
  overlay.classList.add('aktif');
  sistemAcBtn.classList.add('aktif');
}
function panelKapat() {
  panelAcik = false;
  sistemPanel.classList.remove('acik');
  overlay.classList.remove('aktif');
  sistemAcBtn.classList.remove('aktif');
}

sistemAcBtn.addEventListener('click', () => panelAcik ? panelKapat() : panelAc());
overlay.addEventListener('click', panelKapat);

// Swipe ile kapat
let baslangicY = 0;
sistemPanel.addEventListener('touchstart', e => {
  baslangicY = e.touches[0].clientY;
}, { passive: true });
sistemPanel.addEventListener('touchend', e => {
  const fark = e.changedTouches[0].clientY - baslangicY;
  if (fark > 60) panelKapat();
}, { passive: true });

// ── Sohbet Geçmişini Temizle ──────────────────────────────────────────────────
temizleBtn.addEventListener('click', async () => {
  try {
    await fetch(`${API}/api/gecmis`, { method: 'DELETE' });
  } catch { /* önemsiz */ }

  chatListesi.innerHTML = `
    <div class="chat-karsilama">
      <div class="karsilama-icon">🤖</div>
      <p>Geçmiş temizlendi efendim. Nasıl yardımcı olabilirim?</p>
    </div>`;
});

// ── Gönder Butonu / Enter ─────────────────────────────────────────────────────
gonderBtn.addEventListener('click', mesajGonder);
mesajGirisi.addEventListener('keydown', e => {
  if (e.key === 'Enter') { e.preventDefault(); mesajGonder(); }
});

// ── Yardımcı Fonksiyonlar ─────────────────────────────────────────────────────
function balonEkle(tip, metin) {
  const div   = document.createElement('div');
  div.className = `chat-mesaj ${tip}`;
  const balon = document.createElement('div');
  balon.className = 'chat-balon';
  balon.textContent = metin;
  div.appendChild(balon);
  chatListesi.appendChild(div);
  chatListesi.scrollTop = chatListesi.scrollHeight;
}

function yaziyorGoster() {
  const id  = `yaziyor-${Date.now()}`;
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

function yaziyorKaldir(id) {
  document.getElementById(id)?.remove();
}
