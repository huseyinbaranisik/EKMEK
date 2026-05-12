/**
 * Ekmek AI Asistan - Uzak Kontrol Sunucusu
 * Telefon üzerinden aynı Wi-Fi ağında erişim sağlar.
 * Express ile HTTP sunucu açar, QR kod oluşturur.
 */

const express   = require('express');
const http      = require('http');
const path      = require('path');
const os        = require('os');
const QRCode    = require('qrcode');
const { komutuYorumla } = require('./zeka');
const { sistemKontroluGerceklestir } = require('./sistem');

const app    = express();
const PORT   = process.env.UZAK_PORT || 3847;

let sunucu    = null;
let pencereRef = null; // Electron penceresi referansı (bildirim göndermek için)

// ── Middleware ──────────────────────────────────────────────────────────────
app.use(express.json());
app.use(express.static(path.join(__dirname, '..', 'uzak_arayuz')));

// ── Yerel IP al ─────────────────────────────────────────────────────────────
function yerelIpAl() {
    const arayuzler = os.networkInterfaces();
    for (const ad of Object.keys(arayuzler)) {
        for (const arayuz of arayuzler[ad]) {
            if (arayuz.family === 'IPv4' && !arayuz.internal) {
                return arayuz.address;
            }
        }
    }
    return '127.0.0.1';
}

// ── API Rotaları ─────────────────────────────────────────────────────────────

/** Sağlık kontrolü */
app.get('/api/saglik', (req, res) => {
    res.json({ durum: 'aktif', mesaj: 'Ekmek AI çalışıyor efendim!' });
});

/** Sohbet geçmişi depola (basit in-memory) */
let uzakGecmis = [];

/** Komut gönder */
app.post('/api/komut', async (req, res) => {
    const { metin } = req.body;
    if (!metin || typeof metin !== 'string') {
        return res.status(400).json({ hata: 'Geçersiz komut.' });
    }

    uzakGecmis.push({ role: 'user', content: metin });
    if (uzakGecmis.length > 20) uzakGecmis.shift();

    try {
        const sonuc = await komutuYorumla(uzakGecmis);
        uzakGecmis.push({ role: 'assistant', content: sonuc.response });

        // Sistem komutlarını çalıştır
        if (sonuc.action === 'system') {
            await sistemKontroluGerceklestir(sonuc.target, sonuc.value);
        }

        // Electron penceresine bildir (masaüstü arayüzüne de yansıt)
        if (pencereRef && !pencereRef.isDestroyed()) {
            pencereRef.webContents.send('uzak-komut-geldi', {
                kullanici: metin,
                asistan: sonuc.response
            });
        }

        res.json({ basari: true, yanit: sonuc.response, aksiyon: sonuc.action });
    } catch (hata) {
        console.error('Uzak komut hatası:', hata);
        res.status(500).json({ hata: 'Sunucu hatası.' });
    }
});

/** Sistem kontrolü (ses, parlaklık vb.) */
app.post('/api/sistem', async (req, res) => {
    const { tip, deger } = req.body;
    if (!tip) return res.status(400).json({ hata: 'tip parametresi eksik.' });

    try {
        const sonuc = await sistemKontroluGerceklestir(tip, deger);
        res.json(sonuc);
    } catch (hata) {
        res.status(500).json({ hata: 'Sistem komutu başarısız.' });
    }
});

/** Sohbet geçmişini temizle */
app.delete('/api/gecmis', (req, res) => {
    uzakGecmis = [];
    res.json({ basari: true });
});

/** QR kodu PNG olarak döndür */
app.get('/api/qr', async (req, res) => {
    const ip  = yerelIpAl();
    const url = `http://${ip}:${PORT}`;
    try {
        const buffer = await QRCode.toBuffer(url, {
            errorCorrectionLevel: 'H',
            type: 'png',
            margin: 2,
            color: { dark: '#000000', light: '#ffffff' }
        });
        res.set('Content-Type', 'image/png');
        res.send(buffer);
    } catch (e) {
        res.status(500).json({ hata: 'QR oluşturulamadı.' });
    }
});

/** Bağlantı bilgisi */
app.get('/api/baglan', (req, res) => {
    const ip  = yerelIpAl();
    const url = `http://${ip}:${PORT}`;
    res.json({ ip, port: PORT, url });
});

// ── Sunucu Başlat / Durdur ───────────────────────────────────────────────────

function sunucuyuBaslat(electronPencere) {
    pencereRef = electronPencere;

    sunucu = http.createServer(app);
    sunucu.listen(PORT, '0.0.0.0', () => {
        const ip  = yerelIpAl();
        const url = `http://${ip}:${PORT}`;
        console.log(`[Uzak Kontrol] Sunucu aktif: ${url}`);
    });

    sunucu.on('error', (hata) => {
        console.error('[Uzak Kontrol] Sunucu hatası:', hata.message);
    });

    return sunucu;
}

function sunucuyuDurdur() {
    if (sunucu) {
        sunucu.close(() => console.log('[Uzak Kontrol] Sunucu kapatıldı.'));
        sunucu = null;
    }
}

function sunucuBilgisiAl() {
    const ip  = yerelIpAl();
    const url = `http://${ip}:${PORT}`;
    return { ip, port: PORT, url, aktif: sunucu !== null };
}

module.exports = { sunucuyuBaslat, sunucuyuDurdur, sunucuBilgisiAl };
