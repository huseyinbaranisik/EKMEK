const { exec } = require('child_process');
const loudness = require('loudness');

/**
 * Sistem Kontrol Modülü
 * Donanım seviyesindeki işlemleri (ses, parlaklık, klavye ışığı) yönetir.
 */

/**
 * exec'i Promise'e sarar — hata yakalanabilir hale gelir.
 */
function calistir(komut) {
    return new Promise((resolve, reject) => {
        exec(komut, { windowsHide: true }, (hata, stdout, stderr) => {
            if (hata) reject(hata);
            else resolve(stdout);
        });
    });
}

// PowerShell klavye tuşu simülasyon betiği
const donanimTusuBetigi = (vKey, taramaKodu, tekrar = 1, genisletilmis = false) => {
    const asagiBayrak = genisletilmis ? '0x01' : '0';
    const yukariBayrak = genisletilmis ? '0x03' : '2';
    return `
    Add-Type -TypeDefinition @"
    using System;
    using System.Runtime.InteropServices;
    public class Keyboard {
        [DllImport("user32.dll")]
        public static extern void keybd_event(byte bVk, byte bScan, uint dwFlags, uint dwExtraInfo);
    }
"@;
    for($i=0; $i<${tekrar}; $i++){
        [Keyboard]::keybd_event(${vKey}, ${taramaKodu}, ${asagiBayrak}, 0); 
        Start-Sleep -m 50;
        [Keyboard]::keybd_event(${vKey}, ${taramaKodu}, ${yukariBayrak}, 0); 
        Start-Sleep -m 100;
    }
`;
};

/**
 * Güvenlik filtresi — tehlikeli sistem komutlarını engeller.
 */
function guvenlikKontrolu(deger) {
    const tehlikeliPattern = /del|rm|format|erase|rd|md|rename|move|copy|attrib|system32|windows|drivers/i;
    return tehlikeliPattern.test(String(deger));
}

async function sistemKontroluGerceklestir(tip, deger) {
    if (guvenlikKontrolu(tip) || guvenlikKontrolu(deger)) {
        return { success: false, message: "Kritik sistem dosyaları koruma altında efendim." };
    }

    try {
        switch (tip) {
            case 'tus_basimi': {
                const betik = donanimTusuBetigi(deger, '0');
                await calistir(`powershell -NoProfile -WindowStyle Hidden -Command "${betik}"`);
                return { success: true, message: "Tuş gönderildi." };
            }

            case 'parlaklik': {
                let seviye = parseInt(deger);
                if (isNaN(seviye)) seviye = (deger === 'high' || deger === 'aç') ? 100 : 20;
                seviye = Math.max(0, Math.min(100, seviye));
                await calistir(
                    `powershell -NoProfile -WindowStyle Hidden -Command "(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1, ${seviye})"`
                );
                return { success: true, message: `Parlaklık %${seviye} yapıldı.` };
            }

            case 'ses': {
                let seviye = parseInt(deger);
                if (isNaN(seviye)) seviye = (deger === 'up' || deger === 'aç') ? 80 : 20;
                seviye = Math.max(0, Math.min(100, seviye));
                await loudness.setVolume(seviye);
                return { success: true, message: `Ses %${seviye} yapıldı.` };
            }

            case 'sessiz': {
                const suankiSes = await loudness.getVolume();
                if (suankiSes > 0) {
                    await loudness.setVolume(0);
                    return { success: true, message: "Ses kapatıldı efendim." };
                } else {
                    await loudness.setVolume(50);
                    return { success: true, message: "Ses açıldı efendim." };
                }
            }

            case 'klavye_isigi': {
                let seviye = parseInt(deger);
                if (isNaN(seviye)) seviye = (deger === 'on' || deger === 'high' || deger === 'aç') ? 100 : 0;
                let wmiSeviyesi = seviye > 75 ? 4 : seviye > 50 ? 3 : seviye > 25 ? 2 : seviye > 0 ? 1 : 0;
                await calistir(
                    `powershell -NoProfile -WindowStyle Hidden -Command "$wmi = Get-WmiObject -Namespace root\\WMI -Class AcerGamingFunction; $inParams = $wmi.GetMethodParameters('SetGamingKBBacklight'); $inParams['gmInput'] = [byte]${wmiSeviyesi}; $wmi.InvokeMethod('SetGamingKBBacklight', $inParams, $null)"`
                );
                return { success: true, message: `Klavye ışığı ayarlandı.` };
            }

            case 'medya_oynat': {
                const betik = donanimTusuBetigi('0xB3', '0', 1, true);
                await calistir(`powershell -NoProfile -WindowStyle Hidden -Command "${betik}"`);
                return { success: true, message: "Oynatılıyor." };
            }

            case 'medya_sonraki': {
                const betik = donanimTusuBetigi('0xB0', '0', 1, true);
                await calistir(`powershell -NoProfile -WindowStyle Hidden -Command "${betik}"`);
                return { success: true, message: "Sonraki parça." };
            }

            case 'medya_onceki': {
                const betik = donanimTusuBetigi('0xB1', '0', 1, true);
                await calistir(`powershell -NoProfile -WindowStyle Hidden -Command "${betik}"`);
                return { success: true, message: "Önceki parça." };
            }

            default:
                return { success: false, message: `Bilinmeyen sistem komutu: ${tip}` };
        }
    } catch (hata) {
        console.error(`Sistem Kontrol Hatası (${tip}):`, hata.message);
        return { success: false, message: `İşlem gerçekleştirilemedi efendim.` };
    }
}

module.exports = { sistemKontroluGerceklestir };
