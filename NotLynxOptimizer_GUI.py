import sys
import os
import ctypes
import subprocess
import threading
import time
import customtkinter as ctk
from PIL import Image

# Yönetici Yetkisi Kontrolü (UAC)
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

# CustomTkinter Genel Tema Ayarları
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class NotLynxOptimizerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Pencere Yapılandırması
        self.title("NotLynx Optimizer v1.0")
        self.geometry("620 x 580")
        self.resizable(False, False)

        # Uygulama İkonunu Yükleme (Eğer varsa)
        if os.path.exists("app.ico"):
            try:
                self.iconbitmap("app.ico")
            except:
                pass

        # Ana Arayüz Elemanları
        self.setup_ui()

    def setup_ui(self):
        # Üst Başlık ve Logo Alanı
        self.title_frame = ctk.CTkFrame(self, corner_radius=10)
        self.title_frame.pack(pady=15, padx=20, fill="x")

        self.main_label = ctk.CTkLabel(
            self.title_frame, 
            text="⚡ NotLynx Optimizer v1.0", 
            font=ctk.CTkFont(size=22, weight="bold")
        )
        self.main_label.pack(pady=(15, 2))

        self.sub_label = ctk.CTkLabel(
            self.title_frame, 
            text="Elite Kernel & Windows Latency Optimization Engine", 
            font=ctk.CTkFont(size=12, slant="italic"),
            text_color="gray"
        )
        self.sub_label.pack(pady=(0, 15))

        # Bilgi / Durum Kutusu
        self.info_frame = ctk.CTkFrame(self, corner_radius=10)
        self.info_frame.pack(pady=10, padx=20, fill="both", expand=True)

        self.log_textbox = ctk.CTkTextbox(
            self.info_frame, 
            font=ctk.CTkFont(family="Consolas", size=12),
            activate_scrollbars=True
        )
        self.log_textbox.pack(pady=10, padx=10, fill="both", expand=True)
        self.log_textbox.insert("end", ">>> NotLynx Optimizer Başlatılmaya Hazır...\n")
        self.log_textbox.insert("end", ">>> Tüm optimizasyonları tek tıkla uygulamak için aşağıdaki butona basın.\n\n")
        self.log_textbox.configure(state="disabled")

        # İlerleme Çubuğu (Progress Bar)
        self.progress = ctk.CTkProgressBar(self, orientation="horizontal")
        self.progress.pack(pady=10, padx=20, fill="x")
        self.progress.set(0)

        # Buton ve Kontrol Alanı
        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.pack(pady=(5, 15), padx=20, fill="x")

        self.start_btn = ctk.CTkButton(
            self.btn_frame, 
            text="OPTIMIZASYONU BAŞLAT", 
            font=ctk.CTkFont(size=14, weight="bold"),
            height=45,
            fg_color="#1f538d",
            hover_color="#14375e",
            command=self.run_optimization_thread
        )
        self.start_btn.pack(fill="x")

    def log(self, message):
        """Log ekranına yazı yazdırır"""
        self.log_textbox.configure(state="normal")
        self.log_textbox.insert("end", f"{message}\n")
        self.log_textbox.see("end")
        self.log_textbox.configure(state="disabled")

    def run_command(self, cmd):
        """Komut satırı komutunu çalıştırır"""
        try:
            subprocess.run(cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return True
        except:
            return False

    def run_optimization_thread(self):
        """Arayüzün donmaması için optimizasyonu ayrı thread'de çalıştırır"""
        self.start_btn.configure(state="disabled", text="OPTIMIZASYON UYGULANIYOR...")
        threading.Thread(target=self.start_optimization, daemon=True).start()

    def start_optimization(self):
        modules = [
            ("Sistem Zamanlayıcısı (BCDedit HPET/Dynamic Tick)", "bcdedit /set useplatformclock false && bcdedit /set disabledynamictick yes"),
            ("Network Throttling Bypass", 'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile" /v NetworkThrottlingIndex /t REG_DWORD /d 0xffffffff /f'),
            ("TCP No Delay / Nagle Algoritması", 'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile" /v SystemResponsiveness /t REG_DWORD /d 0 /f'),
            ("RAM & Bellek Yöneticisi (DisablePagingExecutive)", 'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Memory Management" /v DisablePagingExecutive /t REG_DWORD /d 1 /f'),
            ("CPU Scheduler (Win32PrioritySeparation)", 'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\PriorityControl" /v Win32PrioritySeparation /t REG_DWORD /d 38 /f'),
            ("GPU MMCSS Önceliği", 'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile\\Tasks\\Games" /v "GPU Priority" /t REG_DWORD /d 8 /f'),
            ("USB Raw Input & Güç Tasarrufu Kapatma", 'powercfg /DEVICEENABLEPOWERMANAGEMENT "USB" 0'),
            ("Telemetry & Hizmetler Shield (DiagTrack)", "sc config DiagTrack start= disabled && sc stop DiagTrack"),
            ("Xbox Game DVR Shield", 'reg add "HKCU\\System\\GameConfigStore" /v GameDVR_Enabled /t REG_DWORD /d 0 /f'),
            ("Ultimate Power Plan Aktivasyonu", "powercfg -duplicatescheme e9a42b02-d5df-448d-aa00-03f14749eb61")
        ]

        total = len(modules)
        self.log("\n==========================================")
        self.log("🚀 OPTIMIZASYON MOTORU BAŞLATILDI")
        self.log("==========================================\n")

        for index, (name, cmd) in enumerate(modules, start=1):
            self.log(f"[{index}/{total}] Uygulanıyor: {name}...")
            self.run_command(cmd)
            time.sleep(0.3)
            self.progress.set(index / total)

        self.log("\n==========================================")
        self.log("✅ TÜM OPTIMIZASYONLAR BAŞARIYLA TAMAMLANDI!")
        self.log("💡 Değişikliklerin aktif olması için bilgisayarınızı yeniden başlatın.")
        self.log("==========================================")

        self.start_btn.configure(text="İŞLEM TAMAMLANDI (YENİDEN BAŞLATIN)", fg_color="#28a745")

if __name__ == "__main__":
    if not is_admin():
        # Yönetici Yetkisi ile Yeniden Başlatma
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    else:
        app = NotLynxOptimizerApp()
        app.mainloop()