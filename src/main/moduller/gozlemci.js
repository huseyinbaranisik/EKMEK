const si = require('systeminformation');

let gozlemciDongusu = null;
let sonUyariZamani = 0;
const UYARI_BEKLEME_SURESI = 5 * 60 * 1000; // Aynı uyarıyı en az 5 dakikada bir ver

function gozlemciyiBaslat(anaPencere) {
    if (gozlemciDongusu) return;

    gozlemciDongusu = setInterval(async () => {
        try {
            const simdi = Date.now();
            if (simdi - sonUyariZamani < UYARI_BEKLEME_SURESI) return;

            const pil = await si.battery();
            const bellek = await si.mem();
            const sicaklik = await si.cpuTemperature();

            let uyarilar = [];

            // 1. Pil Kontrolü
            if (pil.hasBattery && pil.percent <= 20 && !pil.isCharging) {
                uyarilar.push(`Efendim araya giriyorum, bilgisayarınızın şarjı yüzde ${pil.percent} seviyesine düştü. Lütfen şarja takın.`);
            }

            // 2. RAM Kontrolü
            const ramYuzde = (bellek.active / bellek.total) * 100;
            if (ramYuzde > 90) {
                uyarilar.push("Efendim, bellek kullanımınız yüzde 90'ı geçti. Bilgisayarınız zorlanıyor olabilir.");
            }

            // 3. Sıcaklık Kontrolü
            if (sicaklik.main && sicaklik.main > 80) {
                uyarilar.push(`Efendim, işlemci sıcaklığınız ${Math.round(sicaklik.main)} dereceye ulaştı. Sisteminizi dinlendirmeniz faydalı olabilir.`);
            }

            if (uyarilar.length > 0) {
                sonUyariZamani = simdi;
                
                // Pencereyi göster
                if (anaPencere && !anaPencere.isVisible()) {
                    anaPencere.show();
                }

                // Ön tarafa uyarılardan ilkini sesli olarak göndermek için IPC sinyali
                anaPencere.webContents.send('uzak-komut-geldi', { 
                    tip: 'sesli_uyari', 
                    mesaj: uyarilar[0] 
                });
            }
        } catch (hata) {
            console.error("Gözlemci hatası:", hata);
        }
    }, 60000); // Her 60 saniyede bir kontrol et
}

function gozlemciyiDurdur() {
    if (gozlemciDongusu) {
        clearInterval(gozlemciDongusu);
        gozlemciDongusu = null;
    }
}

module.exports = { gozlemciyiBaslat, gozlemciyiDurdur };
