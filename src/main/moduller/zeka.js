/**
 * Ekmek AI Asistan - Yapay Zeka Modülü
 * Groq API (Llama ve Whisper) entegrasyonunu yönetir.
 */

const Groq = require('groq-sdk');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { sistemKontroluGerceklestir } = require('./sistem');
const { exec } = require('child_process');

const groq = new Groq({ apiKey: process.env.GROQ_API_KEY });

// Model yapılandırması
const SOHBET_MODELI = process.env.SOHBET_MODELI || "llama-3.3-70b-versatile";
const SES_MODELI   = process.env.SES_MODELI   || "whisper-large-v3";

const SISTEM_MESAJI = `Sen 'Ekmek' adında, kullanıcıya karşı çok sadık, nazik, samimi ve zeki bir Windows asistanısın.

Kişilik Özelliklerin:
1. Kullanıcıya HER ZAMAN "efendim" diyerek hitap et. Bu senin sadakatini ve nezaketini gösterir.
2. Bir arkadaş kadar samimi ol ama saygılı çizgini (efendim hitabını) asla bozma.
3. Kullanıcının halini hatırını sor, onunla sohbet et ama her zaman asil bir dil kullan.

TEKNİK KURALLAR:
1. Şarkı/Müzik talepleri -> "action": "open", "target": "spotify search: ŞARKI ADI"
2. YouTube/Web -> "action": "open", "target": "URL"
3. Sistem ayarları -> "action": "system"
4. Mod değiştirme -> "action": "mode", "target": "oyun" | "gece"
5. Makro/Protokol Çalıştırma: Kullanıcı "yazılım modunu başlat", "çalışma ortamımı hazırla" veya "yazılıma başla" gibi işlemler istediğinde -> "action": "macro", "target": "yazilim"
6. Ekran İnceleme: SADECE kullanıcı AÇIKÇA "ekranıma göz at", "ekranımı incele", "ekranıma bak" gibi ifadeler kullandığında -> "action": "vision", "target": "screen"
7. +18 KISITLAMASI: Eğer kullanıcı cinsel içerikli (porno vb.), yasadışı veya ahlaka aykırı bir talepte bulunursa KESİNLİKLE reddet. "action": "unknown" dön ve yanıt olarak: "Üzgünüm efendim, ancak bu tür içeriklere erişmenize veya işlem yapmanıza izin veremem." de.
8. Fare Tıklaması: Eğer önceki mesajlarda asistan "[KOORDINAT: X, Y]" formatında bir yeri tıklamak için izin istemişse ve kullanıcı "evet", "tıkla", "onaylıyorum" dediyse -> "action": "click", "target": "mouse", "value": {"x": <X değeri>, "y": <Y değeri>}

Yanıtlarını HER ZAMAN geçerli bir JSON formatında döndür:
{ "action": "open" | "system" | "mode" | "macro" | "vision" | "click" | "unknown", "target": "string", "value": "any", "response": "Efendim hitabını içeren samimi yanıt" }`;

/**
 * Sohbet geçmişini alıp AI yanıtı döndürür.
 * JSON parse başarısız olursa ikinci bir deneme yapar.
 */
async function komutuYorumla(gecmis) {
    try {
        const tamamlama = await groq.chat.completions.create({
            messages: [
                { role: "system", content: SISTEM_MESAJI },
                ...gecmis
            ],
            model: SOHBET_MODELI,
            response_format: { type: "json_object" },
            temperature: 0.7,
            max_tokens: 512,
        });

        const icerik = tamamlama.choices[0]?.message?.content || '{}';
        let sonuc;

        try {
            sonuc = JSON.parse(icerik);
        } catch {
            // JSON bozuksa içindeki JSON'u bulmaya çalış
            const eslesme = icerik.match(/\{[\s\S]*\}/);
            sonuc = eslesme ? JSON.parse(eslesme[0]) : null;
        }

        if (!sonuc || !sonuc.response) {
            return { action: 'unknown', response: "Anlayamadım efendim, tekrar söyler misiniz?" };
        }

        // Mod mantığı
        if (sonuc.action === 'mode') {
            const mod = (sonuc.target || '').toLowerCase();
            if (mod === 'oyun') {
                sistemKontroluGerceklestir('ses', '60');
                sistemKontroluGerceklestir('klavye_isigi', '100');
                sistemKontroluGerceklestir('parlaklik', '100');
                exec('start spotify');
                sonuc.response = "Oyun modu aktif efendim! Ses, parlaklık ve klavye ışığı ayarlandı.";
            } else if (mod === 'gece') {
                sistemKontroluGerceklestir('ses', '20');
                sistemKontroluGerceklestir('parlaklik', '0');
                sistemKontroluGerceklestir('klavye_isigi', '0');
                sonuc.response = "Gece modu aktif efendim. İyi geceler dilerim.";
            } else if (mod === 'normal' || mod === 'varsayilan') {
                sistemKontroluGerceklestir('ses', '50');
                sistemKontroluGerceklestir('parlaklik', '60');
                sonuc.response = "Normal mod aktif efendim.";
            }
        }

        return sonuc;

    } catch (hata) {
        console.error('Groq Komut Hatası:', hata.message);
        return { action: 'unknown', response: "Bağlantı sorunu yaşıyorum efendim, lütfen tekrar deneyin." };
    }
}

/**
 * Ses verisini Whisper ile metne çevirir.
 */
async function sesiMetneCevir(arrayBuffer) {
    const tampon = Buffer.from(arrayBuffer);
    const geciciDosya = path.join(os.tmpdir(), `ekmek_${Date.now()}.webm`);

    try {
        fs.writeFileSync(geciciDosya, tampon);

        const desifre = await groq.audio.transcriptions.create({
            file: fs.createReadStream(geciciDosya),
            model: SES_MODELI,
            language: "tr",
            response_format: "json",
        });

        return desifre.text || "";

    } catch (hata) {
        console.error('Whisper Dönüştürme Hatası:', hata.message);
        return "";
    } finally {
        try {
            if (fs.existsSync(geciciDosya)) fs.unlinkSync(geciciDosya);
        } catch { /* Geçici dosya silinemedi, önemsiz */ }
    }
}

/**
 * Ekran görüntüsünü ve soruyu Groq Vision API ile yorumlar.
 */
async function ekraniYorumla(base64Image, soru) {
    try {
        const tamamlama = await groq.chat.completions.create({
            messages: [
                {
                    role: "user",
                    content: [
                        { type: "text", text: "Şu anda kullanıcının ekranında bir sorun var. Kullanıcı diyor ki: '" + soru + "'. Ekran görüntüsünü incele ve ne yapılması gerektiğini adım adım, nazik ve samimi bir dille (mutlaka 'efendim' diyerek) anlat. Eğer sorun çözülebilir bir şeyse ve tıklanması gereken belirli bir buton/yer tespit edersen, yanıtında mutlaka tıklanacak yerin koordinatlarını '[KOORDINAT: X, Y]' formatında ver. Fare kontrolü istiyorsan 'Şu noktaya tıklamam için izin veriyor musunuz efendim?' gibi bir cümleyle bitir." },
                        { type: "image_url", image_url: { url: `data:image/png;base64,${base64Image}` } }
                    ]
                }
            ],
            model: "llama-3.2-90b-vision-preview",
            temperature: 0.5,
            max_tokens: 1024,
        });

        return tamamlama.choices[0]?.message?.content || "Ekranı incelerken bir sorun oluştu efendim.";
    } catch (hata) {
        console.error('Groq Vision Hatası:', hata.message);
        return "Ekran görüntünüzü incelerken bağlantı sorunu yaşadım efendim.";
    }
}

module.exports = { komutuYorumla, sesiMetneCevir, ekraniYorumla };
