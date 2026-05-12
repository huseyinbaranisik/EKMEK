const { contextBridge, ipcRenderer } = require('electron');

/**
 * Ekmek AI Asistan - Ön Yükleme Betiği
 * Ana süreç ile arayüz süreci arasındaki güvenli iletişimi sağlar.
 */

contextBridge.exposeInMainWorld('electronAPI', {
  // Uygulama başlatma komutu
  uygulamayiBaslat: (hedef) => ipcRenderer.invoke('uygulamayi-baslat', hedef),

  // Sistem kontrolleri (ses, parlaklık vb.)
  sistemKontrolu: (veri) => ipcRenderer.invoke('sistem-kontrolu', veri),

  // Groq üzerinden komut yorumlama
  komutuYorumla: (gecmis) => ipcRenderer.invoke('komutu-yorumla', gecmis),

  // Ses verisini metne çevirme (Whisper)
  sesiMetneCevir: (sesVerisi) => ipcRenderer.invoke('sesi-metne-cevir', sesVerisi),

  // Pencereyi gizle (tray'e minimize et)
  pencereyiKapat: () => ipcRenderer.invoke('pencereyi-kapat'),

  // ── Uzak Kontrol ─────────────────────────────────────────────────────────
  sunucuBilgisiAl: () => ipcRenderer.invoke('sunucu-bilgisi-al'),

  // ── Sözlük ───────────────────────────────────────────────────────────────
  sozlukYukle:   ()              => ipcRenderer.invoke('sozluk-yukle'),
  sozlukEkle:    (kelime)        => ipcRenderer.invoke('sozluk-ekle', kelime),
  sozlukSil:     (kelime)        => ipcRenderer.invoke('sozluk-sil', kelime),
  sozlukDuzenle: (eski, yeni)    => ipcRenderer.invoke('sozluk-duzenle', { eski, yeni }),
  sozlukAra:     (sorgu)         => ipcRenderer.invoke('sozluk-ara', sorgu),

  // ── Uzak komut geldi bildirimi (renderer → renderer için) ────────────────
  uzakKomutDinle: (callback) => ipcRenderer.on('uzak-komut-geldi', (_e, veri) => callback(veri)),
});
