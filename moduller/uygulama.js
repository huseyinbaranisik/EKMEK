const { shell } = require('electron');
const { exec } = require('child_process');
const { sistemKontroluGerceklestir } = require('./sistem');

/**
 * Uygulama Yönetim Modülü
 * Uygulama başlatma ve Spotify entegrasyonunu yönetir.
 */

const ozelDurumlar = {
    'lol': 'C:\\Riot Games\\Riot Client\\RiotClientServices.exe',
    'league of legends': 'C:\\Riot Games\\Riot Client\\RiotClientServices.exe',
    'calculator': 'calc.exe',
    'hesap makinesi': 'calc.exe',
    'notepad': 'notepad.exe',
    'chrome': 'chrome.exe',
    'instagram': 'instagram://'
};

const spotifyEslesmeleri = {
    'beğenilenler': 'spotify:collection:tracks',
    'beğenilen şarkılar': 'spotify:collection:tracks',
    'en sevdiğim': 'spotify:collection:tracks',
    'en sevdiğim şarkılar': 'spotify:collection:tracks',
    'favorilerim': 'spotify:collection:tracks'
};

async function uygulamayiBaslat(hedef) {
    let hedefKucuk = hedef.toLowerCase().trim();
    
    // Spotify Araması veya Çalma Listesi
    if (spotifyEslesmeleri[hedefKucuk] || hedefKucuk.startsWith('spotify:')) {
        const uri = spotifyEslesmeleri[hedefKucuk] || hedef;
        // Windows 'start' komutu protokolleri doğrudan ilgili uygulamada açar
        exec(`start ${uri}`);
        
        // Otomatik oynatma için bekleme ve tuş simülasyonu
        setTimeout(() => {
            sistemKontroluGerceklestir('tus_basimi', '0x0D'); // Enter
            setTimeout(() => sistemKontroluGerceklestir('medya_oynat'), 1000);
        }, 3000);
        return { success: true, message: `Spotify talebiniz işleniyor efendim.` };
    }

    if (hedefKucuk.startsWith('spotify search:')) {
        const sorgu = hedef.substring(15).trim();
        exec(`start spotify:search:${encodeURIComponent(sorgu)}`);
        
        setTimeout(() => {
            sistemKontroluGerceklestir('tus_basimi', '0x0D');
            setTimeout(() => sistemKontroluGerceklestir('medya_oynat'), 1000);
        }, 4500);
        return { success: true, message: `Spotify'da "${sorgu}" aranıyor efendim.` };
    }

    // Web URL Kontrolü (http veya https ile başlıyorsa)
    if (hedefKucuk.startsWith('http://') || hedefKucuk.startsWith('https://')) {
        shell.openExternal(hedef);
        return { success: true, message: `Web adresi açılıyor.` };
    }

    // Tarayıcı + URL Kontrolü (örn: "opera.exe https://youtube.com")
    const parcalar = hedef.split(' ');
    if (parcalar.length > 1 && (parcalar[0].endsWith('.exe') || parcalar[0].includes('opera') || parcalar[0].includes('chrome'))) {
        exec(`start ${hedef}`);
        return { success: true, message: `${parcalar[0]} ile sayfa açılıyor.` };
    }

    // Özel Tanımlı Uygulamalar
    if (ozelDurumlar[hedefKucuk]) {
        const yol = ozelDurumlar[hedefKucuk];
        if (hedefKucuk.includes('lol')) {
            exec(`start "" "${yol}" --launch-product=league_of_legends --launch-patchline=live`);
        } else if (yol.includes('://')) {
            exec(`start ${yol}`);
        } else {
            shell.openPath(yol).catch(() => exec(`start ${yol}`));
        }
        return { success: true, message: `${hedef} açılıyor efendim.` };
    }

    // Genel Başlatma (Dosya yolu veya sistem komutu)
    try {
        const hata = await shell.openPath(hedef);
        if (hata) {
            // Hata varsa terminal üzerinden 'start' ile zorla
            exec(`start ${hedef}`, (err) => {
                if (err) console.error("Başlatma hatası:", err);
            });
        }
    } catch (e) {
        exec(`start ${hedef}`);
    }

    return { success: true, message: `${hedef} açılıyor efendim.` };
}

module.exports = { uygulamayiBaslat };
