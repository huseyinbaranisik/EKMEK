"""
arayuz/ana_pencere.py — Ekmek AI Asistan
Uyanma kelimesi algılandığında ekrana gelen, geçmişi gösteren mini pencere.
"""

import tkinter as tk
from tkinter import scrolledtext
import threading
import queue

class EkmekArayuz:
    def __init__(self):
        self.root = None
        self.metin_alani = None
        self.kuyruk = queue.Queue()
        self.pencere_acik = False

    def baslat(self):
        """Arayüzü ana thread dışında çalışacak şekilde hazırlar."""
        self.root = tk.Tk()
        self.root.title("Ekmek AI")
        self.root.geometry("400x300")
        self.root.attributes('-topmost', True) # Her zaman üstte
        self.root.configure(bg='#1e1e1e')
        
        # Ekranın ortasına yerleştir
        ekran_genislik = self.root.winfo_screenwidth()
        ekran_yukseklik = self.root.winfo_screenheight()
        x = (ekran_genislik // 2) - (400 // 2)
        y = (ekran_yukseklik // 2) - (300 // 2)
        self.root.geometry(f"400x300+{x}+{y}")

        # Başlık etiketi (Logo niyetine ekmek emojisi)
        etiket = tk.Label(self.root, text="🍞", fg="white", bg="#1e1e1e", font=("Arial", 48))
        etiket.pack(pady=5)
        
        baslik = tk.Label(self.root, text="EKMEK AI ASİSTAN", fg="#0078d4", bg="#1e1e1e", font=("Arial", 14, "bold"))
        baslik.pack(pady=2)

        # Konuşma geçmişi alanı
        self.metin_alani = scrolledtext.ScrolledText(self.root, width=45, height=10, bg="#2d2d2d", fg="#d4d4d4", font=("Consolas", 10))
        self.metin_alani.pack(padx=10, pady=5)
        self.metin_alani.config(state=tk.DISABLED)

        # Ayarlar butonu (taslak)
        self.ayar_buton = tk.Button(self.root, text="Ayarlar", command=self.ayarlar_ac, bg="#0078d4", fg="white")
        self.ayar_buton.pack(pady=10)

        # Başlangıçta gizli tut (isteğe bağlı, uyanma kelimesiyle açılacaksa)
        # self.root.withdraw() 
        
        self.root.after(100, self._kuyruk_kontrol)
        self.root.mainloop()

    def ayarlar_ac(self):
        print("Ayarlar sekmesi yakinda eklenecek...")

    def mesaj_ekle(self, gonderen, mesaj):
        """Kuyruğa yeni bir mesaj ekler."""
        self.kuyruk.put(f"{gonderen}: {mesaj}\n")

    def _kuyruk_kontrol(self):
        """Kuyruktaki mesajları arayüze basar."""
        try:
            while True:
                mesaj = self.kuyruk.get_nowait()
                self.metin_alani.config(state=tk.NORMAL)
                self.metin_alani.insert(tk.END, mesaj)
                self.metin_alani.see(tk.END)
                self.metin_alani.config(state=tk.DISABLED)
                
                # Eğer pencere gizliyse göster
                self.root.deiconify()
        except queue.Empty:
            pass
        self.root.after(100, self._kuyruk_kontrol)

    def goster(self):
        """Pencereyi ekrana getirir."""
        if self.root:
            self.root.deiconify()

    def gizle(self):
        """Pencereyi gizler."""
        if self.root:
            self.root.withdraw()

# Küresel arayüz objesi
ekmek_gui = EkmekArayuz()
