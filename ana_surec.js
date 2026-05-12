const { app, BrowserWindow, ipcMain, screen, Tray, Menu, nativeImage } = require('electron');
const path = require('path');
const fs   = require('fs');
require('dotenv').config();

/**
 * Ekmek AI Asistan - Ana Süreç
 * Uygulamanın iskeletini, system tray'i, uzak kontrol sunucusunu
 * ve modüller arası iletişimi yönetir.
 */

let anaPencere;
let tray;

const SOZLUK_YOLU = path.join(__dirname, 'veri', 'sozluk.json');

function pencereOlustur() {
    const anaEkran = screen.getPrimaryDisplay();
    const { width, height } = anaEkran.workAreaSize;

    anaPencere = new BrowserWindow({
        width: 400,
        height: 600,
        x: width - 420,
        y: height - 620,
        frame: false,
        transparent: true,
        alwaysOnTop: true,
        show: false,
        icon: path.join(__dirname, 'icon.png'),
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            preload: path.join(__dirname, 'on_yukleme.js')
        }
    });

    anaPencere.loadFile('index.html');

    anaPencere.once('ready-to-show', () => {
        anaPencere.show();
    });

    // Kapatınca tamamen kapatma — tray'e minimize et
    anaPencere.on('close', (olay) => {
        if (!app.isQuiting) {
            olay.preventDefault();
            anaPencere.hide();
        }
    });

    anaPencere.on('closed', () => {
        anaPencere = null;
    });
}

/**
 * System Tray oluşturur — sağ tık menüsü ile kontrol.
 */
function trayOlustur() {
    const ikonYolu = path.join(__dirname, 'icon.png');
    const ikonGorsel = nativeImage.createFromPath(ikonYolu).resize({ width: 16, height: 16 });

    tray = new Tray(ikonGorsel);
    tray.setToolTip('Ekmek AI Asistan');

    const menu = Menu.buildFromTemplate([
        {
            label: 'Göster / Gizle',
            click: () => {
                if (anaPencere) {
                    anaPencere.isVisible() ? anaPencere.hide() : anaPencere.show();
                }
            }
        },
        { type: 'separator' },
        {
            label: 'Her Zaman Üstte',
            type: 'checkbox',
            checked: true,
            click: (item) => {
                if (anaPencere) anaPencere.setAlwaysOnTop(item.checked);
            }
        },
        { type: 'separator' },
        {
            label: 'Çıkış',
            click: () => {
                app.isQuiting = true;
                app.quit();
            }
        }
    ]);

    tray.setContextMenu(menu);

    // Tray ikonuna çift tıklayınca pencereyi göster/gizle
    tray.on('double-click', () => {
        if (anaPencere) {
            anaPencere.isVisible() ? anaPencere.hide() : anaPencere.show();
        }
    });
}

// Uygulama Yaşam Döngüsü
app.whenReady().then(() => {
    pencereOlustur();
    trayOlustur();

    // Uzak kontrol sunucusunu başlat
    const { sunucuyuBaslat } = require('./moduller/uzak_kontrol');
    sunucuyuBaslat(anaPencere);

    // Medya ve mikrofon izinlerini otomatik onayla
    const { session } = require('electron');
    session.defaultSession.setPermissionRequestHandler((webContents, permission, callback) => {
        const izinliPermissions = ['media', 'audioCapture', 'microphone'];
        callback(izinliPermissions.includes(permission));
    });
});

app.on('window-all-closed', () => {
    // Tray var olduğu sürece uygulamayı kapat (macOS hariç)
    if (process.platform !== 'darwin' && !tray) app.quit();
});

app.on('before-quit', () => {
    app.isQuiting = true;
    const { sunucuyuDurdur } = require('./moduller/uzak_kontrol');
    sunucuyuDurdur();
});

// ===================== IPC İletişimi =====================

ipcMain.handle('uygulamayi-baslat', async (event, hedef) => {
    const { uygulamayiBaslat } = require('./moduller/uygulama');
    return await uygulamayiBaslat(hedef);
});

ipcMain.handle('sistem-kontrolu', async (event, veri) => {
    const { sistemKontroluGerceklestir } = require('./moduller/sistem');
    return await sistemKontroluGerceklestir(veri.tip, veri.deger);
});

ipcMain.handle('komutu-yorumla', async (event, gecmis) => {
    const { komutuYorumla } = require('./moduller/zeka');
    return await komutuYorumla(gecmis);
});

ipcMain.handle('sesi-metne-cevir', async (event, sesVerisi) => {
    const { sesiMetneCevir } = require('./moduller/zeka');
    return await sesiMetneCevir(sesVerisi);
});

ipcMain.handle('pencereyi-kapat', () => {
    if (anaPencere) anaPencere.hide();
});

// ── Uzak kontrol bilgisi ──────────────────────────────────────────────────────
ipcMain.handle('sunucu-bilgisi-al', () => {
    const { sunucuBilgisiAl } = require('./moduller/uzak_kontrol');
    return sunucuBilgisiAl();
});

// ── Sözlük IPC ────────────────────────────────────────────────────────────────

/** Sözlüğü yükle */
ipcMain.handle('sozluk-yukle', () => {
    try {
        const ham = fs.readFileSync(SOZLUK_YOLU, 'utf-8');
        return JSON.parse(ham);
    } catch (e) {
        return { hata: e.message };
    }
});

/** Sözlüğe kelime ekle */
ipcMain.handle('sozluk-ekle', (event, kelime) => {
    try {
        const ham  = fs.readFileSync(SOZLUK_YOLU, 'utf-8');
        const data = JSON.parse(ham);

        const temiz = kelime.trim().toLowerCase();
        if (!temiz) return { basari: false, mesaj: 'Boş kelime.' };
        if (data.kelimeler.includes(temiz)) return { basari: false, mesaj: 'Kelime zaten var.' };

        data.kelimeler.push(temiz);
        data.kelimeler.sort();
        data.kelime_sayisi = data.kelimeler.length;

        fs.writeFileSync(SOZLUK_YOLU, JSON.stringify(data, null, 2), 'utf-8');
        return { basari: true, mesaj: `"${temiz}" eklendi.`, yeni_sayi: data.kelime_sayisi };
    } catch (e) {
        return { basari: false, mesaj: e.message };
    }
});

/** Sözlükten kelime sil */
ipcMain.handle('sozluk-sil', (event, kelime) => {
    try {
        const ham  = fs.readFileSync(SOZLUK_YOLU, 'utf-8');
        const data = JSON.parse(ham);

        const indeks = data.kelimeler.indexOf(kelime);
        if (indeks === -1) return { basari: false, mesaj: 'Kelime bulunamadı.' };

        data.kelimeler.splice(indeks, 1);
        data.kelime_sayisi = data.kelimeler.length;

        fs.writeFileSync(SOZLUK_YOLU, JSON.stringify(data, null, 2), 'utf-8');
        return { basari: true, mesaj: `"${kelime}" silindi.`, yeni_sayi: data.kelime_sayisi };
    } catch (e) {
        return { basari: false, mesaj: e.message };
    }
});

/** Kelimeyi düzenle */
ipcMain.handle('sozluk-duzenle', (event, { eski, yeni }) => {
    try {
        const ham  = fs.readFileSync(SOZLUK_YOLU, 'utf-8');
        const data = JSON.parse(ham);

        const indeks = data.kelimeler.indexOf(eski);
        if (indeks === -1) return { basari: false, mesaj: 'Kelime bulunamadı.' };

        const temiz = yeni.trim().toLowerCase();
        if (!temiz) return { basari: false, mesaj: 'Boş kelime.' };
        if (data.kelimeler.includes(temiz)) return { basari: false, mesaj: 'Bu kelime zaten var.' };

        data.kelimeler[indeks] = temiz;
        data.kelimeler.sort();
        data.kelime_sayisi = data.kelimeler.length;

        fs.writeFileSync(SOZLUK_YOLU, JSON.stringify(data, null, 2), 'utf-8');
        return { basari: true, mesaj: `"${eski}" → "${temiz}" güncellendi.` };
    } catch (e) {
        return { basari: false, mesaj: e.message };
    }
});

/** Kelime ara */
ipcMain.handle('sozluk-ara', (event, sorgu) => {
    try {
        const ham  = fs.readFileSync(SOZLUK_YOLU, 'utf-8');
        const data = JSON.parse(ham);

        const q = sorgu.trim().toLowerCase();
        if (!q) return { basari: true, sonuclar: [], toplam: 0 };

        const sonuclar = data.kelimeler
            .filter(k => k.includes(q))
            .slice(0, 100); // En fazla 100 sonuç

        return { basari: true, sonuclar, toplam: sonuclar.length };
    } catch (e) {
        return { basari: false, mesaj: e.message };
    }
});
