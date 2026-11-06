import tkinter as tk
from tkinter import scrolledtext, messagebox
import queue

class EkmekArayuz:
    def __init__(self):
        self.root = None
        self.metin_alani = None
        self.kuyruk = queue.Queue()
        self.ayar_buton = None

    def baslat(self):
        self.root = tk.Tk()
        self.root.title("Ekmek AI")
        self.root.geometry("400x350")
        self.root.attributes('-topmost', True)
        self.root.configure(bg='#1e1e1e')
        
        # Merkeze yerlestir
        ekran_w = self.root.winfo_screenwidth()
        ekran_h = self.root.winfo_screenheight()
        x = (ekran_w // 2) - 200
        y = (ekran_h // 2) - 175
        self.root.geometry(f"400x350+{x}+{y}")

        tk.Label(self.root, text="🍞", fg="white", bg="#1e1e1e", font=("Arial", 40)).pack(pady=5)
        tk.Label(self.root, text="EKMEK AI ASISTAN", fg="#0078d4", bg="#1e1e1e", font=("Arial", 12, "bold")).pack()

        self.metin_alani = scrolledtext.ScrolledText(self.root, width=40, height=10, bg="#2d2d2d", fg="#d4d4d4", font=("Consolas", 10))
        self.metin_alani.pack(padx=10, pady=10)
        self.metin_alani.config(state=tk.DISABLED)

        # Ayarlar butonu - command lambda ile guvene alindi
        self.ayar_buton = tk.Button(self.root, text="⚙ Ayarlar", command=self.ayarlar_ac, bg="#333333", fg="white", relief="flat")
        self.ayar_buton.pack(pady=5)

        self.root.after(100, self._kuyruk_kontrol)
        self.root.mainloop()

    def ayarlar_ac(self):
        # Print yerine messagebox kullanarak donguyu engelliyoruz
        messagebox.showinfo("Ekmek AI", "Ayarlar sekmesi yakinda eklenecek!")

    def mesaj_ekle(self, gonderen, mesaj):
        self.kuyruk.put(f"{gonderen}: {mesaj}\n")

    def _kuyruk_kontrol(self):
        try:
            while True:
                mesaj = self.kuyruk.get_nowait()
                self.metin_alani.config(state=tk.NORMAL)
                self.metin_alani.insert(tk.END, mesaj)
                self.metin_alani.see(tk.END)
                self.metin_alani.config(state=tk.DISABLED)
                self.root.deiconify()
        except queue.Empty:
            pass
        self.root.after(100, self._kuyruk_kontrol)

ekmek_gui = EkmekArayuz()
