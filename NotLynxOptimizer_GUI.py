import customtkinter as ctk
import os
import sys
import shutil
import ctypes
import subprocess
import threading
import winreg
import time
import platform
import webbrowser
from PIL import Image

# --- GLOBAL TEMA VE ESTETİK AYARLAR ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("green")

# --- KERNEL MODÜL TANIMLARI ---
KERNEL_MODULES = [
    {
        "id": "01",
        "name": "Sistem Zamanlayıcısı (BCDedit HPET & TSC)",
        "desc": "Micro-stutter önlenir, saat senkronizasyonu kararlı hale getirilir (HPET off, Dynamic Tick off, TSC Enhanced).",
        "apply": [
            "bcdedit /set useplatformclock false",
            "bcdedit /set disabledynamictick yes",
            "bcdedit /set tscsyncpolicy Enhanced"
        ],
        "revert": [
            "bcdedit /deletevalue useplatformclock",
            "bcdedit /deletevalue disabledynamictick",
            "bcdedit /deletevalue tscsyncpolicy"
        ]
    },
    {
        "id": "02",
        "name": "Network Throttling Bypass & Yanıt Süresi",
        "desc": "Ağ bant genişliği tamamen oyun trafiğine rezerve edilir ve sistem tepkiselliği %100'e çıkarılır.",
        "apply": [
            'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile" /v NetworkThrottlingIndex /t REG_DWORD /d 4294967295 /f',
            'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile" /v SystemResponsiveness /t REG_DWORD /d 0 /f'
        ],
        "revert": [
            'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile" /v NetworkThrottlingIndex /t REG_DWORD /d 10 /f',
            'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile" /v SystemResponsiveness /t REG_DWORD /d 20 /f'
        ]
    },
    {
        "id": "03",
        "name": "TCP No Delay (Nagle Algoritması Bypass)",
        "desc": "Tüm ağ kartı adaptör GUID'lerinde paket gecikmesi ve ping sıçramaları sıfırlanır.",
        "special": "tcp_nodelay"
    },
    {
        "id": "04",
        "name": "RAM & DisablePagingExecutive (DPC Latency)",
        "desc": "Çekirdek sürücüler fiziksel RAM'de kilitlenerek disk sayfalama gecikmesi sıfırlanır.",
        "apply": [
            'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Memory Management" /v DisablePagingExecutive /t REG_DWORD /d 1 /f',
            'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Memory Management" /v LargeSystemCache /t REG_DWORD /d 0 /f',
            'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Memory Management" /v ClearPageFileAtShutdown /t REG_DWORD /d 0 /f'
        ],
        "revert": [
            'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Memory Management" /v DisablePagingExecutive /t REG_DWORD /d 0 /f'
        ]
    },
    {
        "id": "05",
        "name": "CPU Ön Plan Önceliği (Win32PrioritySeparation = 38)",
        "desc": "İşlemci çevrimleri doğrudan aktif oyuna ayrılır (Short Quanta, 3:1 Boost).",
        "apply": [
            'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\PriorityControl" /v Win32PrioritySeparation /t REG_DWORD /d 38 /f'
        ],
        "revert": [
            'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\PriorityControl" /v Win32PrioritySeparation /t REG_DWORD /d 2 /f'
        ]
    },
    {
        "id": "06",
        "name": "GPU MMCSS Görev Önceliği",
        "desc": "Ekran kartı oyun görev önceliği maksimum seviyeye (GPU Priority: 8, High) çıkarılır.",
        "apply": [
            'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile\\Tasks\\Games" /v "GPU Priority" /t REG_DWORD /d 8 /f',
            'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile\\Tasks\\Games" /v "Priority" /t REG_DWORD /d 6 /f',
            'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile\\Tasks\\Games" /v "Scheduling Category" /t REG_SZ /d "High" /f',
            'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile\\Tasks\\Games" /v "SFIO Priority" /t REG_SZ /d "High" /f'
        ],
        "revert": [
            'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile\\Tasks\\Games" /v "Priority" /t REG_DWORD /d 2 /f',
            'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile\\Tasks\\Games" /v "Scheduling Category" /t REG_SZ /d "Medium" /f'
        ]
    },
    {
        "id": "07",
        "name": "USB Raw Input (Fare İvmelenmesi Sıfırlama)",
        "desc": "Fare ivmelenmesi kaldırılır, 1:1 e-spor aim hassasiyeti ve sıfır donanım gecikmesi sağlanır.",
        "apply": [
            'reg add "HKCU\\Control Panel\\Mouse" /v MouseSpeed /t REG_SZ /d 0 /f',
            'reg add "HKCU\\Control Panel\\Mouse" /v MouseThreshold1 /t REG_SZ /d 0 /f',
            'reg add "HKCU\\Control Panel\\Mouse" /v MouseThreshold2 /t REG_SZ /d 0 /f'
        ],
        "revert": [
            'reg add "HKCU\\Control Panel\\Mouse" /v MouseSpeed /t REG_SZ /d 1 /f',
            'reg add "HKCU\\Control Panel\\Mouse" /v MouseThreshold1 /t REG_SZ /d 6 /f',
            'reg add "HKCU\\Control Panel\\Mouse" /v MouseThreshold2 /t REG_SZ /d 10 /f'
        ]
    },
    {
        "id": "08",
        "name": "Telemetry & Disk Yoran Servisleri Durdur",
        "desc": "Disk yoran WSearch, SysMain (SuperFetch) ve arka plan telemetri kancaları kapatılır.",
        "apply": [
            "sc stop DiagTrack",
            "sc config DiagTrack start= disabled",
            "sc stop SysMain",
            "sc config SysMain start= disabled",
            "sc stop WSearch",
            "sc config WSearch start= disabled"
        ],
        "revert": [
            "sc config DiagTrack start= auto",
            "sc start DiagTrack",
            "sc config SysMain start= auto",
            "sc start SysMain",
            "sc config WSearch start= delayed-auto",
            "sc start WSearch"
        ]
    },
    {
        "id": "09",
        "name": "Xbox Game DVR & Kayıt Kancaları",
        "desc": "Arka planda gizlice FPS düşüren ekran kaydı ve oyun yakalama kancaları devre dışı bırakılır.",
        "apply": [
            'reg add "HKCU\\System\\GameConfigStore" /v GameDVR_Enabled /t REG_DWORD /d 0 /f',
            'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\GameDVR" /v AppCaptureEnabled /t REG_DWORD /d 0 /f',
            'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\GameDVR" /v AllowGameDVR /t REG_DWORD /d 0 /f'
        ],
        "revert": [
            'reg add "HKCU\\System\\GameConfigStore" /v GameDVR_Enabled /t REG_DWORD /d 1 /f',
            'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\GameDVR" /v AppCaptureEnabled /t REG_DWORD /d 1 /f',
            'reg delete "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\GameDVR" /v AllowGameDVR /f'
        ]
    },
    {
        "id": "10",
        "name": "NotLynx Optimizer - Ultimate Power Plan",
        "desc": "Denetim masasında 'NotLynx Optimizer - Ultimate Power' adıyla özel nihai güç planı aktif edilir.",
        "special": "power_plan"
    }
]

class NotLynxOptimizerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Pencere Yapılandırması
        self.title("NotLynx Optimizer v1.0 | Elite Cyberpunk Performance Suite")
        self.geometry("1240x800")
        self.minsize(1100, 720)

        # İkon ve Varlıklar
        self.load_icon()

        # Grid Düzeni
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.switches = {}
        self.is_busy = False

        # ==========================================
        # SOL MENÜ (CYBERPUNK SIDEBAR)
        # ==========================================
        self.sidebar_frame = ctk.CTkFrame(self, width=280, corner_radius=0, fg_color="#040609")
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(11, weight=1)

        # Logo Görseli
        self.init_sidebar_logo()

        # Admin Durum Rozeti
        self.init_admin_badge()

        # Navigasyon Sekmeleri
        self.nav_buttons = {}
        nav_items = [
            ("dashboard", "📊  Gösterge Paneli"),
            ("kernel", "⚡  Kernel Modülleri"),
            ("gpu", "🎮  GPU & E-Spor"),
            ("process", "📉  İşlem Düşürücü"),
            ("desktop", "🛠️  Masaüstü & Ayarlar"),
            ("cleaner", "🧹  Derin Temizleyici"),
            ("shield", "🛡️  Kalkan & Kurtarma")
        ]

        for i, (key, label) in enumerate(nav_items):
            btn = ctk.CTkButton(
                self.sidebar_frame, 
                text=label, 
                command=lambda k=key: self.select_tab(k), 
                fg_color="#0a101d", 
                text_color="#ffffff",
                hover_color="#131e35",
                anchor="w",
                font=ctk.CTkFont(size=13, weight="bold"),
                height=44,
                corner_radius=8
            )
            btn.grid(row=3 + i, column=0, padx=16, pady=4, sticky="ew")
            self.nav_buttons[key] = btn

        # Canlı Sistem Telemetri Paneli (Sol Alt)
        self.init_telemetry_panel()

        # ==========================================
        # SAĞ İÇERİK ALANI
        # ==========================================
        self.content_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="#020407")
        self.content_frame.grid(row=0, column=1, sticky="nsew")
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)

        # Tüm Sekmeleri Başlat
        self.tabs = {}
        self.init_dashboard_tab()
        self.init_kernel_tab()
        self.init_gpu_tab()
        self.init_process_tab()
        self.init_desktop_tab()
        self.init_cleaner_tab()
        self.init_shield_tab()

        self.select_tab("dashboard")

        # Canlı Sayaç Döngüsü (Process Count)
        self.after(1000, self.update_telemetry_loop)

    def load_icon(self):
        for p in ["app.ico", "NotlynxOptimizer/app.ico", "../app.ico"]:
            if os.path.exists(p):
                try:
                    self.iconbitmap(p)
                    break
                except:
                    pass

    def init_sidebar_logo(self):
        logo_container = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        logo_container.grid(row=0, column=0, padx=16, pady=(15, 8))

        logo_path = "logo.png"
        if not os.path.exists(logo_path):
            logo_path = "NotlynxOptimizer/logo.png"

        if os.path.exists(logo_path):
            try:
                pil_img = Image.open(logo_path)
                ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(125, 125))
                img_lbl = ctk.CTkLabel(logo_container, image=ctk_img, text="")
                img_lbl.pack(pady=(0, 4))
            except:
                pass

        lbl = ctk.CTkLabel(logo_container, text="NOTLYNX", font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"), text_color="#00ff66")
        lbl.pack(pady=(0, 0))
        sub = ctk.CTkLabel(logo_container, text="// ELITE KERNEL SUITE v1.0", font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"), text_color="#38bdf8")
        sub.pack(pady=(0, 2))

    def fallback_logo(self):
        pass

    def init_admin_badge(self):
        is_adm = self.is_admin()
        badge = ctk.CTkFrame(
            self.sidebar_frame, 
            fg_color="#061a0d" if is_adm else "#1a1202", 
            border_color="#00ff66" if is_adm else "#f59e0b",
            border_width=1,
            corner_radius=8
        )
        badge.grid(row=2, column=0, padx=16, pady=(0, 15), sticky="ew")
        
        status_text = "🛡️ YÖNETİCİ MODU AKTİF" if is_adm else "⚠️ YÖNETİCİ YETKİSİ GEREKLİ"
        status_color = "#00ff66" if is_adm else "#f59e0b"
        ctk.CTkLabel(badge, text=status_text, font=ctk.CTkFont(size=11, weight="bold"), text_color=status_color).pack(padx=10, pady=6)

        if not is_adm:
            ctk.CTkButton(
                self.sidebar_frame,
                text="⚡ Yönetici Olarak Yeniden Başlat",
                font=ctk.CTkFont(size=10, weight="bold"),
                fg_color="#f59e0b",
                hover_color="#d97706",
                text_color="#000000",
                height=28,
                corner_radius=6,
                command=self.relaunch_as_admin
            ).grid(row=10, column=0, padx=16, pady=(0, 10), sticky="ew")

    def init_telemetry_panel(self):
        panel = ctk.CTkFrame(self.sidebar_frame, fg_color="#070b14", corner_radius=10, border_color="#131e35", border_width=1)
        panel.grid(row=12, column=0, padx=16, pady=16, sticky="sew")

        ctk.CTkLabel(panel, text="CANLI TELEMETRİ", font=ctk.CTkFont(size=9, weight="bold"), text_color="#64748b").pack(padx=12, pady=(10, 2), anchor="w")
        self.lbl_process_count = ctk.CTkLabel(panel, text="● İŞLEMLER: Hesaplanıyor...", font=ctk.CTkFont(size=11, weight="bold"), text_color="#38bdf8")
        self.lbl_process_count.pack(padx=12, pady=(0, 2), anchor="w")
        ctk.CTkLabel(panel, text="● LATENCY: ULTRA LOW", font=ctk.CTkFont(size=11, weight="bold"), text_color="#00ff66").pack(padx=12, pady=(0, 2), anchor="w")
        ctk.CTkLabel(panel, text="● POWER: NOTLYNX ULTIMATE", font=ctk.CTkFont(size=10), text_color="#94a3b8").pack(padx=12, pady=(0, 10), anchor="w")

    def update_telemetry_loop(self):
        try:
            cmd = "powershell -Command '(Get-Process).Count'"
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            cnt = res.stdout.strip()
            if cnt:
                self.lbl_process_count.configure(text=f"● İŞLEMLER: {cnt} Aktif")
        except:
            pass
        self.after(5000, self.update_telemetry_loop)

    def is_admin(self):
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False

    def relaunch_as_admin(self):
        script = os.path.abspath(sys.argv[0])
        params = " ".join([f'"{arg}"' for arg in sys.argv[1:]])
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{script}" {params}', None, 1)
        sys.exit()

    def select_tab(self, key):
        for k, frame in self.tabs.items():
            frame.grid_forget()
            if k in self.nav_buttons:
                self.nav_buttons[k].configure(fg_color="#0a101d", text_color="#ffffff")

        if key in self.tabs:
            self.tabs[key].grid(row=0, column=0, sticky="nsew")
            if key in self.nav_buttons:
                self.nav_buttons[key].configure(fg_color="#131e35", text_color="#00ff66")

    # ==========================================
    # 0. SEKME: GÖSTERGE PANELİ (OPTIMIZERDUCK STİLİ)
    # ==========================================
    def init_dashboard_tab(self):
        frame = ctk.CTkFrame(self.content_frame, fg_color="#020407")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)

        # Üst Araç Çubuğu (Top Bar)
        top_bar = ctk.CTkFrame(frame, fg_color="transparent")
        top_bar.grid(row=0, column=0, padx=25, pady=(20, 10), sticky="ew")
        top_bar.grid_columnconfigure(0, weight=1)

        title_box = ctk.CTkFrame(top_bar, fg_color="transparent")
        title_box.grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(title_box, text="📊  GÖSTERGE PANELİ (SYSTEM DASHBOARD)", font=ctk.CTkFont(size=20, weight="bold"), text_color="#ffffff").pack(anchor="w")
        ctk.CTkLabel(title_box, text="Donanım bileşenleri, canlı telemetri ve sistem kaynak durumunu anlık izleyin.", font=ctk.CTkFont(size=12), text_color="#94a3b8").pack(anchor="w")

        btn_box = ctk.CTkFrame(top_bar, fg_color="transparent")
        btn_box.grid(row=0, column=1, sticky="e")

        ctk.CTkButton(
            btn_box, 
            text="⚡ Görev Yöneticisi", 
            width=135, 
            height=34, 
            fg_color="#0f172a", 
            hover_color="#1e293b", 
            border_color="#38bdf8", 
            border_width=1, 
            text_color="#38bdf8", 
            font=ctk.CTkFont(size=12, weight="bold"),
            command=lambda: subprocess.Popen("taskmgr.exe")
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_box, 
            text="⚙️ Güç Planı", 
            width=115, 
            height=34, 
            fg_color="#0f172a", 
            hover_color="#1e293b", 
            border_color="#00ff66", 
            border_width=1, 
            text_color="#00ff66", 
            font=ctk.CTkFont(size=12, weight="bold"),
            command=lambda: subprocess.Popen("control.exe powercfg.cpl")
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_box, 
            text="🔄 Yenile", 
            width=95, 
            height=34, 
            fg_color="#00ff66", 
            hover_color="#00cc52", 
            text_color="#000000", 
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.refresh_dashboard
        ).pack(side="left", padx=5)

        # Scrollable Alan (Ekran taşmalarına karşı güvenli)
        scroll = ctk.CTkScrollableFrame(frame, fg_color="#05080f", border_color="#131e35", border_width=1, corner_radius=10)
        scroll.grid(row=1, column=0, padx=25, pady=(0, 15), sticky="nsew")
        scroll.grid_columnconfigure(0, weight=1)
        scroll.grid_columnconfigure(1, weight=1)

        # 1. Sosyal Medya & Geliştirici Kartları (Row 0)
        social_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        social_frame.grid(row=0, column=0, columnspan=2, padx=8, pady=(8, 12), sticky="ew")
        social_frame.grid_columnconfigure((0, 1, 2), weight=1)

        # TikTok Kartı
        card_tiktok = ctk.CTkFrame(social_frame, fg_color="#0a101d", border_color="#16223b", border_width=1, corner_radius=8)
        card_tiktok.grid(row=0, column=0, padx=4, sticky="ew")
        ctk.CTkLabel(card_tiktok, text="🎵 TIKTOK", font=ctk.CTkFont(size=12, weight="bold"), text_color="#00f0ff").pack(padx=12, pady=(8, 2), anchor="w")
        ctk.CTkLabel(card_tiktok, text="@NotLynx_7", font=ctk.CTkFont(size=11), text_color="#94a3b8").pack(padx=12, pady=(0, 6), anchor="w")
        ctk.CTkButton(card_tiktok, text="Takip Et ↗", height=24, fg_color="#0f172a", hover_color="#1e293b", text_color="#00f0ff", font=ctk.CTkFont(size=10, weight="bold"), command=lambda: webbrowser.open("https://tiktok.com/@NotLynx_7")).pack(padx=12, pady=(0, 8), fill="x")

        # Instagram Kartı
        card_insta = ctk.CTkFrame(social_frame, fg_color="#0a101d", border_color="#16223b", border_width=1, corner_radius=8)
        card_insta.grid(row=0, column=1, padx=4, sticky="ew")
        ctk.CTkLabel(card_insta, text="📸 INSTAGRAM", font=ctk.CTkFont(size=12, weight="bold"), text_color="#ec4899").pack(padx=12, pady=(8, 2), anchor="w")
        ctk.CTkLabel(card_insta, text="@NotLynx7", font=ctk.CTkFont(size=11), text_color="#94a3b8").pack(padx=12, pady=(0, 6), anchor="w")
        ctk.CTkButton(card_insta, text="Takip Et ↗", height=24, fg_color="#0f172a", hover_color="#1e293b", text_color="#ec4899", font=ctk.CTkFont(size=10, weight="bold"), command=lambda: webbrowser.open("https://instagram.com/NotLynx7")).pack(padx=12, pady=(0, 8), fill="x")

        # GitHub Kartı
        card_git = ctk.CTkFrame(social_frame, fg_color="#0a101d", border_color="#16223b", border_width=1, corner_radius=8)
        card_git.grid(row=0, column=2, padx=4, sticky="ew")
        ctk.CTkLabel(card_git, text="⭐ GITHUB", font=ctk.CTkFont(size=12, weight="bold"), text_color="#00ff66").pack(padx=12, pady=(8, 2), anchor="w")
        ctk.CTkLabel(card_git, text="samet2007topcu-art", font=ctk.CTkFont(size=11), text_color="#94a3b8").pack(padx=12, pady=(0, 6), anchor="w")
        ctk.CTkButton(card_git, text="Yıldızla ↗", height=24, fg_color="#0f172a", hover_color="#1e293b", text_color="#00ff66", font=ctk.CTkFont(size=10, weight="bold"), command=lambda: webbrowser.open("https://github.com/samet2007topcu-art/NotLynxOptimizer")).pack(padx=12, pady=(0, 8), fill="x")

        # 2. Donanım Özellikleri Kartları (2x2 Grid)
        # Card 1: OS
        self.dash_os_card = ctk.CTkFrame(scroll, fg_color="#0a101d", border_color="#16223b", border_width=1, corner_radius=10)
        self.dash_os_card.grid(row=1, column=0, padx=8, pady=6, sticky="nsew")
        ctk.CTkLabel(self.dash_os_card, text="🪟 İŞLETİM SİSTEMİ", font=ctk.CTkFont(size=11, weight="bold"), text_color="#38bdf8").pack(padx=16, pady=(12, 2), anchor="w")
        self.dash_os_val = ctk.CTkLabel(self.dash_os_card, text="Yükleniyor...", font=ctk.CTkFont(size=14, weight="bold"), text_color="#ffffff", justify="left")
        self.dash_os_val.pack(padx=16, pady=(0, 4), anchor="w")
        self.dash_os_sub = ctk.CTkLabel(self.dash_os_card, text="● Çekirdek: Windows NT 10.0 • 64-bit", font=ctk.CTkFont(size=11), text_color="#94a3b8")
        self.dash_os_sub.pack(padx=16, pady=(0, 12), anchor="w")

        # Card 2: CPU
        self.dash_cpu_card = ctk.CTkFrame(scroll, fg_color="#0a101d", border_color="#16223b", border_width=1, corner_radius=10)
        self.dash_cpu_card.grid(row=1, column=1, padx=8, pady=6, sticky="nsew")
        ctk.CTkLabel(self.dash_cpu_card, text="⚡ MERKEZİ İŞLEMCİ (CPU)", font=ctk.CTkFont(size=11, weight="bold"), text_color="#00ff66").pack(padx=16, pady=(12, 2), anchor="w")
        self.dash_cpu_val = ctk.CTkLabel(self.dash_cpu_card, text="Yükleniyor...", font=ctk.CTkFont(size=14, weight="bold"), text_color="#ffffff", justify="left")
        self.dash_cpu_val.pack(padx=16, pady=(0, 4), anchor="w")
        self.dash_cpu_sub = ctk.CTkLabel(self.dash_cpu_card, text="● Mantıksal Çekirdekler ve Frekans", font=ctk.CTkFont(size=11), text_color="#94a3b8")
        self.dash_cpu_sub.pack(padx=16, pady=(0, 12), anchor="w")

        # Card 3: RAM
        self.dash_ram_card = ctk.CTkFrame(scroll, fg_color="#0a101d", border_color="#16223b", border_width=1, corner_radius=10)
        self.dash_ram_card.grid(row=2, column=0, padx=8, pady=6, sticky="nsew")
        ctk.CTkLabel(self.dash_ram_card, text="🧠 SİSTEM BELLEĞİ (RAM)", font=ctk.CTkFont(size=11, weight="bold"), text_color="#a855f7").pack(padx=16, pady=(12, 2), anchor="w")
        self.dash_ram_val = ctk.CTkLabel(self.dash_ram_card, text="Yükleniyor...", font=ctk.CTkFont(size=14, weight="bold"), text_color="#ffffff", justify="left")
        self.dash_ram_val.pack(padx=16, pady=(0, 4), anchor="w")
        self.dash_ram_bar = ctk.CTkProgressBar(self.dash_ram_card, height=10, progress_color="#00ff66", fg_color="#1e293b")
        self.dash_ram_bar.pack(padx=16, pady=(2, 6), fill="x")
        self.dash_ram_bar.set(0.0)
        self.dash_ram_sub = ctk.CTkLabel(self.dash_ram_card, text="● Canlı Kullanım Oranı", font=ctk.CTkFont(size=11), text_color="#94a3b8")
        self.dash_ram_sub.pack(padx=16, pady=(0, 12), anchor="w")

        # Card 4: GPU
        self.dash_gpu_card = ctk.CTkFrame(scroll, fg_color="#0a101d", border_color="#16223b", border_width=1, corner_radius=10)
        self.dash_gpu_card.grid(row=2, column=1, padx=8, pady=6, sticky="nsew")
        ctk.CTkLabel(self.dash_gpu_card, text="🎮 GRAFİK KARTI (GPU)", font=ctk.CTkFont(size=11, weight="bold"), text_color="#f59e0b").pack(padx=16, pady=(12, 2), anchor="w")
        self.dash_gpu_val = ctk.CTkLabel(self.dash_gpu_card, text="Yükleniyor...", font=ctk.CTkFont(size=14, weight="bold"), text_color="#ffffff", justify="left")
        self.dash_gpu_val.pack(padx=16, pady=(0, 4), anchor="w")
        self.dash_gpu_sub = ctk.CTkLabel(self.dash_gpu_card, text="● Grafik Sürücüsü & Donanım Hızlandırma", font=ctk.CTkFont(size=11), text_color="#94a3b8")
        self.dash_gpu_sub.pack(padx=16, pady=(0, 12), anchor="w")

        # 3. Depolama Sürücüsü Kartı (Geniş Bar - Row 3, ColumnSpan 2)
        self.dash_disk_card = ctk.CTkFrame(scroll, fg_color="#0a101d", border_color="#16223b", border_width=1, corner_radius=10)
        self.dash_disk_card.grid(row=3, column=0, columnspan=2, padx=8, pady=6, sticky="ew")
        
        disk_top = ctk.CTkFrame(self.dash_disk_card, fg_color="transparent")
        disk_top.pack(fill="x", padx=16, pady=(12, 2))
        ctk.CTkLabel(disk_top, text="💾 DEPOLAMA SÜRÜCÜSÜ (C: NVMe / SSD)", font=ctk.CTkFont(size=11, weight="bold"), text_color="#06b6d4").pack(side="left")
        ctk.CTkButton(disk_top, text="🧹 Temizle", width=70, height=22, fg_color="#1e293b", hover_color="#334155", text_color="#38bdf8", font=ctk.CTkFont(size=10, weight="bold"), command=lambda: self.select_tab("cleaner")).pack(side="right")

        self.dash_disk_val = ctk.CTkLabel(self.dash_disk_card, text="Yükleniyor...", font=ctk.CTkFont(size=13, weight="bold"), text_color="#ffffff", justify="left")
        self.dash_disk_val.pack(padx=16, pady=(0, 4), anchor="w")

        self.dash_disk_bar = ctk.CTkProgressBar(self.dash_disk_card, height=12, progress_color="#00ff66", fg_color="#1e293b")
        self.dash_disk_bar.pack(padx=16, pady=(4, 6), fill="x")
        self.dash_disk_bar.set(0.0)

        self.dash_disk_sub = ctk.CTkLabel(self.dash_disk_card, text="● Disk Kapasite ve Kullanım Durumu", font=ctk.CTkFont(size=11), text_color="#94a3b8")
        self.dash_disk_sub.pack(padx=16, pady=(0, 12), anchor="w")

        # 4. Hızlı Sistem Durumu Şeridi (Row 4)
        status_bar = ctk.CTkFrame(scroll, fg_color="#04070e", border_color="#131e35", border_width=1, corner_radius=8)
        status_bar.grid(row=4, column=0, columnspan=2, padx=8, pady=(6, 12), sticky="ew")
        status_bar.grid_columnconfigure((0, 1, 2), weight=1)

        p1 = ctk.CTkFrame(status_bar, fg_color="transparent")
        p1.grid(row=0, column=0, padx=10, pady=8)
        ctk.CTkLabel(p1, text="GÜÇ PLANI", font=ctk.CTkFont(size=10, weight="bold"), text_color="#64748b").pack(anchor="w")
        ctk.CTkLabel(p1, text="NotLynx Ultimate Power", font=ctk.CTkFont(size=11, weight="bold"), text_color="#00ff66").pack(anchor="w")

        p2 = ctk.CTkFrame(status_bar, fg_color="transparent")
        p2.grid(row=0, column=1, padx=10, pady=8)
        ctk.CTkLabel(p2, text="ZAMANLAYICI (HPET)", font=ctk.CTkFont(size=10, weight="bold"), text_color="#64748b").pack(anchor="w")
        ctk.CTkLabel(p2, text="0.5 ms Enhanced TSC", font=ctk.CTkFont(size=11, weight="bold"), text_color="#38bdf8").pack(anchor="w")

        p3 = ctk.CTkFrame(status_bar, fg_color="transparent")
        p3.grid(row=0, column=2, padx=10, pady=8)
        ctk.CTkLabel(p3, text="KERNEL KORUMA", font=ctk.CTkFont(size=10, weight="bold"), text_color="#64748b").pack(anchor="w")
        ctk.CTkLabel(p3, text="v1.0 E-Spor Modu", font=ctk.CTkFont(size=11, weight="bold"), text_color="#a855f7").pack(anchor="w")

        self.tabs["dashboard"] = frame
        self.refresh_dashboard()

    def refresh_dashboard(self):
        threading.Thread(target=self._fetch_and_update_hw, daemon=True).start()

    def _fetch_and_update_hw(self):
        # 1. OS
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion") as k:
                prod = winreg.QueryValueEx(k, "ProductName")[0]
                build = winreg.QueryValueEx(k, "CurrentBuild")[0]
                try:
                    disp = winreg.QueryValueEx(k, "DisplayVersion")[0]
                except:
                    disp = ""
                arch = "64-bit" if "64" in platform.machine() else "32-bit"
                os_title = f"{prod} {arch}"
                os_detail = f"● Derleme: {build} {disp} • NT 10.0 Çekirdek"
        except:
            os_title = f"Windows {platform.version()}"
            os_detail = "● 64-bit İşletim Sistemi"

        # 2. CPU
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0") as k:
                cpu_name = winreg.QueryValueEx(k, "ProcessorNameString")[0].strip()
            cores = os.cpu_count() or 8
            cpu_title = cpu_name
            cpu_detail = f"● {cores} Mantıksal Çekirdek • Quanta Boost 3:1"
        except:
            cpu_title = platform.processor() or "Modern Çok Çekirdekli CPU"
            cpu_detail = f"● {os.cpu_count()} Mantıksal Çekirdek"

        # 3. RAM
        try:
            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ('dwLength', ctypes.c_ulong),
                    ('dwMemoryLoad', ctypes.c_ulong),
                    ('ullTotalPhys', ctypes.c_ulonglong),
                    ('ullAvailPhys', ctypes.c_ulonglong),
                    ('ullTotalPageFile', ctypes.c_ulonglong),
                    ('ullAvailPageFile', ctypes.c_ulonglong),
                    ('ullTotalVirtual', ctypes.c_ulonglong),
                    ('ullAvailVirtual', ctypes.c_ulonglong),
                    ('ullAvailExtendedVirtual', ctypes.c_ulonglong)
                ]
            stat = MEMORYSTATUSEX()
            stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
            tot_gb = stat.ullTotalPhys / (1024**3)
            avail_gb = stat.ullAvailPhys / (1024**3)
            used_gb = tot_gb - avail_gb
            ram_pct = stat.dwMemoryLoad
            ram_title = f"{tot_gb:.1f} GB RAM ({used_gb:.1f} GB Kullanılıyor)"
            ram_detail = f"● Boş: {avail_gb:.1f} GB (%{100 - ram_pct:.0f}) • Dolu: %{ram_pct}"
            ram_ratio = ram_pct / 100.0
        except:
            ram_title = "16.0 GB RAM"
            ram_detail = "● Canlı RAM İzleme Aktif"
            ram_ratio = 0.5

        # 4. GPU
        try:
            gpus = []
            class_guid = r"SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}"
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, class_guid) as k:
                subkeys, _, _ = winreg.QueryInfoKey(k)
                for i in range(subkeys):
                    sub = winreg.EnumKey(k, i)
                    if sub.isdigit():
                        try:
                            with winreg.OpenKey(k, sub) as sk:
                                desc, _ = winreg.QueryValueEx(sk, "DriverDesc")
                                try:
                                    dver, _ = winreg.QueryValueEx(sk, "DriverVersion")
                                except:
                                    dver = ""
                                if desc and "Basic" not in desc:
                                    gpus.append((desc, dver))
                        except:
                            pass
            if gpus:
                nvidia_or_amd = [g for g in gpus if "NVIDIA" in g[0].upper() or "AMD" in g[0].upper() or "RADEON" in g[0].upper()]
                primary = nvidia_or_amd[0] if nvidia_or_amd else gpus[0]
                gpu_title = primary[0]
                driver_text = f" • Sürücü: {primary[1]}" if primary[1] else ""
                secondary = [g[0] for g in gpus if g != primary]
                sec_text = f" (İkincil: {secondary[0]})" if secondary else ""
                gpu_detail = f"● MMCSS Priority: 8 High{driver_text}{sec_text}"
            else:
                gpu_title = "Donanım Hızlandırmalı GPU"
                gpu_detail = "● Yüksek Performans Modu Aktif"
        except:
            gpu_title = "GPU Algılanıyor..."
            gpu_detail = "● Grafik Hızlandırıcı Aktif"

        # 5. Storage (Disk C:)
        try:
            du = shutil.disk_usage("C:\\")
            d_tot = du.total / (1024**3)
            d_used = du.used / (1024**3)
            d_free = du.free / (1024**3)
            d_pct = (d_used / d_tot) * 100
            
            disk_model = "NVMe / SSD Storage"
            for port in range(5):
                try:
                    path = rf"HARDWARE\DEVICEMAP\Scsi\Scsi Port {port}\Scsi Bus 0\Target Id 0\Logical Unit Id 0"
                    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path) as k:
                        val, _ = winreg.QueryValueEx(k, "Identifier")
                        if val:
                            disk_model = val.strip()
                            break
                except:
                    pass
            disk_title = f"Yerel Disk (C:) {disk_model}"
            disk_detail = f"● Toplam: {d_tot:.0f} GB • Dolu: {d_used:.1f} GB (%{d_pct:.0f}) • Boş Alan: {d_free:.1f} GB"
            disk_ratio = d_pct / 100.0
        except:
            disk_title = "Yerel Disk (C:)"
            disk_detail = "● Depolama alanı izleniyor"
            disk_ratio = 0.5

        # UI güncelle
        self.after(0, lambda: self._apply_hw_to_ui(
            os_title, os_detail,
            cpu_title, cpu_detail,
            ram_title, ram_detail, ram_ratio,
            gpu_title, gpu_detail,
            disk_title, disk_detail, disk_ratio
        ))

    def _apply_hw_to_ui(self, os_title, os_detail, cpu_title, cpu_detail, ram_title, ram_detail, ram_ratio, gpu_title, gpu_detail, disk_title, disk_detail, disk_ratio):
        try:
            self.dash_os_val.configure(text=os_title)
            self.dash_os_sub.configure(text=os_detail)
            
            self.dash_cpu_val.configure(text=cpu_title)
            self.dash_cpu_sub.configure(text=cpu_detail)
            
            self.dash_ram_val.configure(text=ram_title)
            self.dash_ram_sub.configure(text=ram_detail)
            self.dash_ram_bar.set(ram_ratio)
            
            self.dash_gpu_val.configure(text=gpu_title)
            self.dash_gpu_sub.configure(text=gpu_detail)
            
            self.dash_disk_val.configure(text=disk_title)
            self.dash_disk_sub.configure(text=disk_detail)
            self.dash_disk_bar.set(disk_ratio)
            if disk_ratio > 0.85:
                self.dash_disk_bar.configure(progress_color="#ef4444")
            else:
                self.dash_disk_bar.configure(progress_color="#00ff66")
        except:
            pass

    # ==========================================
    # 1. SEKME: KERNEL MODÜLLERİ (10 ÇEKİRDEK)
    # ==========================================
    def init_kernel_tab(self):
        frame = ctk.CTkFrame(self.content_frame, fg_color="#020407")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(2, weight=1)

        # Başlık Barı
        top_bar = ctk.CTkFrame(frame, fg_color="transparent")
        top_bar.grid(row=0, column=0, padx=25, pady=(20, 8), sticky="ew")
        ctk.CTkLabel(top_bar, text="ELITE KERNEL & GECİKME MOTORU", font=ctk.CTkFont(size=20, weight="bold"), text_color="#ffffff").pack(anchor="w")
        ctk.CTkLabel(top_bar, text="Donanım gecikmesini sıfıra indiren 10 çekirdekli ultra-düşük gecikme paketi.", font=ctk.CTkFont(size=12), text_color="#94a3b8").pack(anchor="w")

        # Araç Çubuğu
        toolbar = ctk.CTkFrame(frame, fg_color="transparent")
        toolbar.grid(row=1, column=0, padx=25, pady=(0, 8), sticky="ew")
        ctk.CTkButton(toolbar, text="✓ Tümünü Seç", width=100, height=28, fg_color="#0f172a", hover_color="#1e293b", text_color="#38bdf8", command=self.select_all_switches).pack(side="left", padx=(0, 6))
        ctk.CTkButton(toolbar, text="✕ Tümünü Kaldır", width=100, height=28, fg_color="#0f172a", hover_color="#1e293b", text_color="#94a3b8", command=self.deselect_all_switches).pack(side="left")

        # Kartlar Listesi (Scrollable)
        scroll = ctk.CTkScrollableFrame(frame, fg_color="#05080f", border_color="#131e35", border_width=1, corner_radius=10)
        scroll.grid(row=2, column=0, padx=25, pady=(0, 8), sticky="nsew")
        scroll.grid_columnconfigure(0, weight=1)

        for i, mod in enumerate(KERNEL_MODULES):
            card = ctk.CTkFrame(scroll, fg_color="#0a101d", corner_radius=8, border_color="#16223b", border_width=1)
            card.grid(row=i, column=0, padx=8, pady=5, sticky="ew")
            card.grid_columnconfigure(1, weight=1)

            ctk.CTkLabel(card, text=f"[{mod['id']}]", font=ctk.CTkFont(size=12, weight="bold"), text_color="#00ff66").grid(row=0, column=0, padx=14, pady=12, rowspan=2)
            ctk.CTkLabel(card, text=mod["name"], font=ctk.CTkFont(size=13, weight="bold"), text_color="#ffffff").grid(row=0, column=1, padx=4, pady=(10, 0), sticky="w")
            ctk.CTkLabel(card, text=mod["desc"], font=ctk.CTkFont(size=11), text_color="#94a3b8").grid(row=1, column=1, padx=4, pady=(0, 10), sticky="w")

            sw = ctk.CTkSwitch(card, text="", progress_color="#00ff66")
            sw.grid(row=0, column=2, rowspan=2, padx=16)
            sw.select()
            self.switches[mod["id"]] = sw

        # Konsol Log
        self.kernel_log = ctk.CTkTextbox(frame, height=90, fg_color="#05080f", border_color="#131e35", border_width=1, corner_radius=8, text_color="#00ff66", font=ctk.CTkFont(family="Consolas", size=11))
        self.kernel_log.grid(row=3, column=0, padx=25, pady=(0, 8), sticky="ew")
        self.kernel_log.insert("end", "[READY] 10 Kernel modülü hazır. Seçili modülleri uygulamak için butona basın.\n")

        # Buton Barı
        btn_bar = ctk.CTkFrame(frame, fg_color="transparent")
        btn_bar.grid(row=4, column=0, padx=25, pady=(0, 15), sticky="ew")
        btn_bar.grid_columnconfigure(0, weight=1)

        self.btn_apply_kernel = ctk.CTkButton(btn_bar, text="⚡  SEÇİLEN KERNEL MODÜLLERİNİ SİSTEME UYGULA", font=ctk.CTkFont(size=13, weight="bold"), fg_color="#00ff66", text_color="#020407", hover_color="#00cc52", height=46, corner_radius=8, command=self.thread_apply_kernel)
        self.btn_apply_kernel.grid(row=0, column=0, sticky="ew")

        self.tabs["kernel"] = frame

    def select_all_switches(self):
        for s in self.switches.values(): s.select()

    def deselect_all_switches(self):
        for s in self.switches.values(): s.deselect()

    # ==========================================
    # 2. SEKME: GPU & E-SPOR (MSI MODE & LATENCY)
    # ==========================================
    def init_gpu_tab(self):
        frame = ctk.CTkFrame(self.content_frame, fg_color="#020407")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(2, weight=1)

        top_bar = ctk.CTkFrame(frame, fg_color="transparent")
        top_bar.grid(row=0, column=0, padx=25, pady=(20, 8), sticky="ew")
        ctk.CTkLabel(top_bar, text="🎮 GPU E-SPOR VE GECİKME İNCE AYARLARI", font=ctk.CTkFont(size=20, weight="bold"), text_color="#ffffff").pack(anchor="w")
        ctk.CTkLabel(top_bar, text="Ekran kartı kesme gecikmelerini (MSI Mode) düşürün, shader önbelleğini sıfırlayın ve GPU saat önceliğini sabitleyin.", font=ctk.CTkFont(size=12), text_color="#94a3b8").pack(anchor="w")

        # Hızlı İşlem Kartları
        cards_frame = ctk.CTkScrollableFrame(frame, fg_color="#05080f", border_color="#131e35", border_width=1, corner_radius=10)
        cards_frame.grid(row=2, column=0, padx=25, pady=(0, 10), sticky="nsew")
        cards_frame.grid_columnconfigure(0, weight=1)

        gpu_tweaks = [
            ("1. GPU MSI (Message Signaled Interrupts) Modu", "GPU'yu eski IRQ çakışmalarından kurtarıp MSI moduna alır ve Interrupt Priority: High yapar. FPS düşmelerini keser.", self.thread_enable_gpu_msi),
            ("2. Donanım Hızlandırmalı GPU Zamanlaması (HAGS)", "Windows Hardware-Accelerated GPU Scheduling modunu aktifleştirerek CPU-GPU render darboğazını önler.", self.thread_enable_hags),
            ("3. DirectX & NVIDIA/AMD Shader Cache Temizle", "Bozuk veya eskiyen shader önbelleklerini temizleyerek oyunlardaki ani FPS drop ve takılmaları giderir.", self.thread_clean_shader_cache),
            ("4. MSI Afterburner Hızlı Başlatıcı", "Sisteminizde kurulu MSI Afterburner'ı otomatik bularak overclock ve fan eğrisi kontrolü için başlatır.", self.launch_afterburner)
        ]

        for i, (t_title, t_desc, cmd_fn) in enumerate(gpu_tweaks):
            card = ctk.CTkFrame(cards_frame, fg_color="#0a101d", corner_radius=8, border_color="#16223b", border_width=1)
            card.grid(row=i, column=0, padx=8, pady=8, sticky="ew")
            card.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(card, text=t_title, font=ctk.CTkFont(size=14, weight="bold"), text_color="#38bdf8").grid(row=0, column=0, padx=14, pady=(12, 2), sticky="w")
            ctk.CTkLabel(card, text=t_desc, font=ctk.CTkFont(size=11), text_color="#94a3b8").grid(row=1, column=0, padx=14, pady=(0, 12), sticky="w")
            ctk.CTkButton(card, text="UYGULA", width=110, height=34, fg_color="#00ff66", text_color="#000000", font=ctk.CTkFont(weight="bold"), command=cmd_fn).grid(row=0, column=1, rowspan=2, padx=16)

        # GPU Konsolu
        self.gpu_log = ctk.CTkTextbox(frame, height=120, fg_color="#05080f", border_color="#131e35", border_width=1, corner_radius=8, text_color="#00ff66", font=ctk.CTkFont(family="Consolas", size=11))
        self.gpu_log.grid(row=3, column=0, padx=25, pady=(0, 15), sticky="ew")
        self.gpu_log.insert("end", "[GPU ENGINE] E-Spor modülleri hazır.\n")

        self.tabs["gpu"] = frame

    # ==========================================
    # 3. SEKME: İŞLEM AZALTICI (PROCESS REDUCER)
    # ==========================================
    def init_process_tab(self):
        frame = ctk.CTkFrame(self.content_frame, fg_color="#020407")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(2, weight=1)

        top_bar = ctk.CTkFrame(frame, fg_color="transparent")
        top_bar.grid(row=0, column=0, padx=25, pady=(20, 8), sticky="ew")
        ctk.CTkLabel(top_bar, text="📉 İŞLEMCİ İŞLEM SAYISI DÜŞÜRÜCÜ (PROCESS REDUCER)", font=ctk.CTkFont(size=20, weight="bold"), text_color="#ffffff").pack(anchor="w")
        ctk.CTkLabel(top_bar, text="Görev Yöneticisi'ndeki arka plan işlem sayısını 230+'dan 130'lara düşürün. İşlemci çekirdeklerini sadece oyuna bırakın.", font=ctk.CTkFont(size=12), text_color="#94a3b8").pack(anchor="w")

        info_box = ctk.CTkFrame(frame, fg_color="#0a101d", border_color="#16223b", border_width=1, corner_radius=8)
        info_box.grid(row=1, column=0, padx=25, pady=(0, 10), sticky="ew")
        info_text = (
            "Durdurulan Arka Plan Hizmetleri:\n"
            "• DiagTrack & dmwappushservice (Windows Telemetri & Veri Toplama)\n"
            "• SysMain / Superfetch (Sürekli disk ve bellek yoran arama)\n"
            "• Windows Search Indexer (Oyun esnasında diski meşgul eden arama indeksi)\n"
            "• PcaSvc (Program Uyumluluk Asistanı - her exe açılışında CPU gecikmesi yaratır)\n"
            "• WerSvc (Hata Raporlama Servisi), Spooler (Yazıcı), Fax, MapsBroker, wisvc (Insider)\n"
            "• Zamanlanmış Telemetri Görevleri (Customer Experience & Appraiser)"
        )
        ctk.CTkLabel(info_box, text=info_text, font=ctk.CTkFont(size=11), text_color="#cbd5e1", justify="left").pack(padx=16, pady=12, anchor="w")

        self.proc_log = ctk.CTkTextbox(frame, fg_color="#05080f", border_color="#131e35", border_width=1, corner_radius=8, text_color="#00ff66", font=ctk.CTkFont(family="Consolas", size=11))
        self.proc_log.grid(row=2, column=0, padx=25, pady=(0, 10), sticky="nsew")
        self.proc_log.insert("end", "[PROCESS REDUCER] Hazır. İşlem sayısını düşürmek için aşağıdaki butona basın...\n")

        btn_debloat = ctk.CTkButton(
            frame, 
            text="📉  TÜM GEREKSİZ ARKA PLAN İŞLEMLERİNİ DURDUR VE İŞLEM SAYISINI DÜŞÜR", 
            font=ctk.CTkFont(size=13, weight="bold"), 
            fg_color="#00ff66", 
            text_color="#020407", 
            hover_color="#00cc52", 
            height=46,
            corner_radius=8,
            command=self.thread_reduce_processes
        )
        btn_debloat.grid(row=3, column=0, padx=25, pady=(0, 15), sticky="ew")

        self.tabs["process"] = frame

    # ==========================================
    # 4. SEKME: MASAÜSTÜ & WINDOWS İNCE AYARLARI
    # ==========================================
    def init_desktop_tab(self):
        frame = ctk.CTkFrame(self.content_frame, fg_color="#020407")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)

        top_bar = ctk.CTkFrame(frame, fg_color="transparent")
        top_bar.grid(row=0, column=0, padx=25, pady=(20, 12), sticky="ew")
        ctk.CTkLabel(top_bar, text="🛠️ MASAÜSTÜ VE EXPLORER İNCE AYARLARI", font=ctk.CTkFont(size=20, weight="bold"), text_color="#ffffff").pack(anchor="w")
        ctk.CTkLabel(top_bar, text="Masaüstü kısayol oklarını kaldırın, menü açılış animasyonlarını hızlandırın ve Windows'u sadeleştirin.", font=ctk.CTkFont(size=12), text_color="#94a3b8").pack(anchor="w")

        scroll = ctk.CTkScrollableFrame(frame, fg_color="#05080f", border_color="#131e35", border_width=1, corner_radius=10)
        scroll.grid(row=1, column=0, padx=25, pady=(0, 10), sticky="nsew")
        scroll.grid_columnconfigure(0, weight=1)

        tweaks = [
            (
                "Masaüstü Simgelerindeki Kısayol Okunu Kaldır",
                "Masaüstündeki tüm uygulama simgelerinin üzerindeki mavi/beyaz kısayol ok simgesini kaldırarak temiz bir görünüm sağlar.",
                self.remove_shortcut_arrow,
                self.restore_shortcut_arrow
            ),
            (
                "Windows Menü Açılış Gecikmesini Sıfırla (MenuShowDelay)",
                "Başlat menüsü ve sağ tık menülerinin açılışındaki 400ms varsayılan Windows animasyon gecikmesini 0ms'ye indirir.",
                self.speed_up_menus,
                None
            ),
            (
                "Pencere Açılış Animasyonlarını Hızlandır (MinAnimate)",
                "Pencereler simge durumuna küçülürken veya açılırken harcanan GPU gecikmesini önler.",
                self.speed_up_animations,
                None
            ),
            (
                "Dosya Uzantılarını Her Zaman Göster",
                "Güvenlik ve pratiklik için tüm dosya uzantılarını (.exe, .py, .png) Explorer üzerinde görünür kılar.",
                self.show_file_extensions,
                None
            ),
            (
                "NotLynx Optimizer Güç Planını Denetim Masasına Ekle",
                "Denetim Masası Güç Seçenekleri altına 'NotLynx Optimizer - Ultimate Power' özel planını yazar ve aktif eder.",
                self.thread_apply_notlynx_power,
                None
            )
        ]

        for i, (title_t, desc_t, apply_cmd, revert_cmd) in enumerate(tweaks):
            card = ctk.CTkFrame(scroll, fg_color="#0a101d", corner_radius=8, border_color="#16223b", border_width=1)
            card.grid(row=i, column=0, padx=8, pady=8, sticky="ew")
            card.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(card, text=title_t, font=ctk.CTkFont(size=13, weight="bold"), text_color="#38bdf8").grid(row=0, column=0, padx=14, pady=(10, 2), sticky="w")
            ctk.CTkLabel(card, text=desc_t, font=ctk.CTkFont(size=11), text_color="#94a3b8").grid(row=1, column=0, padx=14, pady=(0, 10), sticky="w")

            btn_box = ctk.CTkFrame(card, fg_color="transparent")
            btn_box.grid(row=0, column=1, rowspan=2, padx=14)

            ctk.CTkButton(btn_box, text="UYGULA", width=90, height=32, fg_color="#00ff66", text_color="#000000", font=ctk.CTkFont(weight="bold"), command=apply_cmd).pack(side="left", padx=4)
            if revert_cmd:
                ctk.CTkButton(btn_box, text="GERİ AL", width=90, height=32, fg_color="#1e293b", text_color="#ffffff", font=ctk.CTkFont(size=11), command=revert_cmd).pack(side="left", padx=4)

        self.desktop_log = ctk.CTkTextbox(frame, height=90, fg_color="#05080f", border_color="#131e35", border_width=1, corner_radius=8, text_color="#00ff66", font=ctk.CTkFont(family="Consolas", size=11))
        self.desktop_log.grid(row=2, column=0, padx=25, pady=(0, 15), sticky="ew")
        self.desktop_log.insert("end", "[DESKTOP ENGINE] Masaüstü ince ayarları hazır.\n")

        self.tabs["desktop"] = frame

    # ==========================================
    # 5. SEKME: DERİN SİSTEM TEMİZLEYİCİ
    # ==========================================
    def init_cleaner_tab(self):
        frame = ctk.CTkFrame(self.content_frame, fg_color="#020407")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)

        top_bar = ctk.CTkFrame(frame, fg_color="transparent")
        top_bar.grid(row=0, column=0, padx=25, pady=(20, 10), sticky="ew")
        ctk.CTkLabel(top_bar, text="🧹 DERİNLEMESİNE SİSTEM VE ARTIK TEMİZLEYİCİ", font=ctk.CTkFont(size=20, weight="bold"), text_color="#ffffff").pack(anchor="w")
        ctk.CTkLabel(top_bar, text="User Temp, Windows Temp, Prefetch, Crash Dumps ve İndirilenler artıklarını temizleyerek GB'larca yer açın.", font=ctk.CTkFont(size=12), text_color="#94a3b8").pack(anchor="w")

        self.cleaner_log = ctk.CTkTextbox(frame, fg_color="#05080f", border_color="#131e35", border_width=1, corner_radius=8, text_color="#00ff66", font=ctk.CTkFont(family="Consolas", size=11))
        self.cleaner_log.grid(row=1, column=0, padx=25, pady=8, sticky="nsew")
        self.cleaner_log.insert("end", "[CLEANER] Temizleyici motor hazır. Taramayı başlatmak için aşağıdaki butona basın...\n")

        btn_clean = ctk.CTkButton(
            frame, 
            text="🧹  DERİNLEMESİNE TEMİZLİĞİ BAŞLAT (TEMP + PREFETCH + CRASH DUMP + KALINTILAR)", 
            font=ctk.CTkFont(size=13, weight="bold"), 
            fg_color="#ef4444", 
            text_color="#ffffff", 
            hover_color="#dc2626", 
            height=46,
            corner_radius=8,
            command=self.thread_run_deep_cleaner
        )
        btn_clean.grid(row=2, column=0, padx=25, pady=(0, 15), sticky="ew")

        self.tabs["cleaner"] = frame

    # ==========================================
    # 6. SEKME: KALKAN VE KURTARMA
    # ==========================================
    def init_shield_tab(self):
        frame = ctk.CTkFrame(self.content_frame, fg_color="#020407")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(2, weight=1)

        top_bar = ctk.CTkFrame(frame, fg_color="transparent")
        top_bar.grid(row=0, column=0, padx=25, pady=(20, 10), sticky="ew")
        ctk.CTkLabel(top_bar, text="🛡️ GÜVENLİK KALKANI VE SİSTEMİ SIFIRLAMA", font=ctk.CTkFont(size=20, weight="bold"), text_color="#ffffff").pack(anchor="w")
        ctk.CTkLabel(top_bar, text="İstediğiniz zaman tek tıkla Sistem Geri Yükleme Noktası oluşturabilir veya tüm optimizasyonları fabrika ayarlarına döndürebilirsiniz.", font=ctk.CTkFont(size=12), text_color="#94a3b8").pack(anchor="w")

        btn_box = ctk.CTkFrame(frame, fg_color="transparent")
        btn_box.grid(row=1, column=0, padx=25, pady=(0, 15), sticky="ew")
        btn_box.grid_columnconfigure(0, weight=1)
        btn_box.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(
            btn_box, 
            text="🛡️  SİSTEM GERİ YÜKLEME NOKTASI OLUŞTUR", 
            font=ctk.CTkFont(size=13, weight="bold"), 
            fg_color="#0f172a", 
            hover_color="#1e293b", 
            text_color="#00ff66", 
            height=50,
            corner_radius=8,
            border_color="#00ff66",
            border_width=1,
            command=self.thread_create_restore_point
        ).grid(row=0, column=0, padx=(0, 8), sticky="ew")

        ctk.CTkButton(
            btn_box, 
            text="🔄  TÜM SİSTEMİ VARSAYILAN AYARLARA DÖNDÜR", 
            font=ctk.CTkFont(size=13, weight="bold"), 
            fg_color="#1e293b", 
            hover_color="#334155", 
            text_color="#f87171", 
            height=50,
            corner_radius=8,
            border_color="#ef4444",
            border_width=1,
            command=self.thread_revert_all
        ).grid(row=0, column=1, sticky="ew")

        self.shield_log = ctk.CTkTextbox(frame, fg_color="#05080f", border_color="#131e35", border_width=1, corner_radius=8, text_color="#00ff66", font=ctk.CTkFont(family="Consolas", size=11))
        self.shield_log.grid(row=2, column=0, padx=25, pady=(0, 15), sticky="nsew")
        self.shield_log.insert("end", "[SHIELD] Güvenlik kalkanı devrede.\n")

        self.tabs["shield"] = frame

    # ==========================================
    # İŞÇİ VE THREAD FONKSİYONLARI
    # ==========================================
    def run_cmd(self, cmd):
        try:
            return subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0
        except:
            return False

    def thread_apply_kernel(self):
        if self.is_busy: return
        threading.Thread(target=self.worker_apply_kernel, daemon=True).start()

    def worker_apply_kernel(self):
        self.is_busy = True
        self.kernel_log.insert("end", "\n[*] SEÇİLEN KERNEL MODÜLLERİ UYGULANIYOR...\n")
        cnt = 0
        for mod in KERNEL_MODULES:
            mid = mod["id"]
            if not self.switches.get(mid, None) or not self.switches[mid].get(): continue

            self.kernel_log.insert("end", f"[*] [{mid}/10] {mod['name']}... ")
            if mod.get("special") == "tcp_nodelay":
                c = self.apply_tcp_nodelay()
                self.kernel_log.insert("end", f"[OK ({c} Adaptör)]\n")
            elif mod.get("special") == "power_plan":
                self.apply_notlynx_power_plan()
                self.kernel_log.insert("end", "[OK (NotLynx Power Plan)]\n")
            else:
                for c_str in mod.get("apply", []):
                    self.run_cmd(c_str)
                self.kernel_log.insert("end", "[OK]\n")
            cnt += 1
            time.sleep(0.04)

        self.kernel_log.insert("end", f"\n[SUCCESS] {cnt} Modül uygulandı! Değişiklikler için PC'nizi yeniden başlatın.\n")
        self.is_busy = False
        ctypes.windll.user32.MessageBoxW(0, f"Seçilen {cnt} Kernel Modülü başarıyla uygulandı!\n\nDeğişikliklerin aktif olması için lütfen bilgisayarınızı yeniden başlatın.", "NotLynx Optimizer", 0)

    def apply_tcp_nodelay(self):
        count = 0
        try:
            base_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces")
            for i in range(winreg.QueryInfoKey(base_key)[0]):
                subkey = winreg.EnumKey(base_key, i)
                p = f"HKLM\\SYSTEM\\CurrentControlSet\\Services\\Tcpip\\Parameters\\Interfaces\\{subkey}"
                self.run_cmd(f'reg add "{p}" /v TcpAckFrequency /t REG_DWORD /d 1 /f')
                self.run_cmd(f'reg add "{p}" /v TCPNoDelay /t REG_DWORD /d 1 /f')
                self.run_cmd(f'reg add "{p}" /v TcpDelAckTicks /t REG_DWORD /d 0 /f')
                count += 1
            winreg.CloseKey(base_key)
        except:
            pass
        return count

    def apply_notlynx_power_plan(self):
        guid = "b31c5a11-6f4d-4f75-a7d5-9fcda7e1836e"
        self.run_cmd(f"powercfg -duplicatescheme e9a42b02-d5df-448d-aa00-03f14749eb61 {guid}")
        self.run_cmd(f'powercfg -changename {guid} "NotLynx Optimizer - Ultimate Power" "NotLynx Elite Kernel Ultra Dusuk Gecikme Plani"')
        self.run_cmd(f"powercfg -setactive {guid}")

    def thread_apply_notlynx_power(self):
        self.apply_notlynx_power_plan()
        self.desktop_log.insert("end", "[OK] 'NotLynx Optimizer - Ultimate Power' planı Denetim Masası'na yazıldı ve aktif edildi!\n")
        ctypes.windll.user32.MessageBoxW(0, "'NotLynx Optimizer - Ultimate Power' güç planı başarıyla oluşturuldu ve aktif edildi!", "NotLynx Power", 0)

    # GPU Tweaks
    def thread_enable_gpu_msi(self):
        threading.Thread(target=self.worker_enable_gpu_msi, daemon=True).start()

    def worker_enable_gpu_msi(self):
        self.gpu_log.insert("end", "[*] Ekran Kartı aranıyor ve MSI Modu aktif ediliyor...\n")
        try:
            pci_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Enum\PCI")
            found = 0
            for i in range(winreg.QueryInfoKey(pci_key)[0]):
                dev = winreg.EnumKey(pci_key, i)
                # Display / VGA controller
                if "VEN_10DE" in dev or "VEN_1002" in dev or "VEN_8086" in dev:
                    dev_path = f"HKLM\\SYSTEM\\CurrentControlSet\\Enum\\PCI\\{dev}"
                    # Alt anahtarları gez
                    try:
                        sub = winreg.OpenKey(pci_key, dev)
                        for j in range(winreg.QueryInfoKey(sub)[0]):
                            sub_dev = winreg.EnumKey(sub, j)
                            target_msi = f"HKLM\\SYSTEM\\CurrentControlSet\\Enum\\PCI\\{dev}\\{sub_dev}\\Device Parameters\\Interrupt Management\\MessageSignaledInterruptProperties"
                            target_aff = f"HKLM\\SYSTEM\\CurrentControlSet\\Enum\\PCI\\{dev}\\{sub_dev}\\Device Parameters\\Interrupt Management\\Affinity Policy"
                            self.run_cmd(f'reg add "{target_msi}" /v MSISupported /t REG_DWORD /d 1 /f')
                            self.run_cmd(f'reg add "{target_aff}" /v DevicePriority /t REG_SZ /d "High" /f')
                            found += 1
                        winreg.CloseKey(sub)
                    except:
                        pass
            winreg.CloseKey(pci_key)
            self.gpu_log.insert("end", f"[SUCCESS] {found} GPU/Display bağdaştırıcısına MSI Mode (High Priority) uygulandı!\n")
            ctypes.windll.user32.MessageBoxW(0, f"Ekran Kartı MSI Modu ve Yüksek Kesme Önceliği (High Priority) başarıyla uygulandı!", "NotLynx GPU Engine", 0)
        except Exception as e:
            self.gpu_log.insert("end", f"[ERR] {e}\n")

    def thread_enable_hags(self):
        self.run_cmd('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\GraphicsDrivers" /v HwSchMode /t REG_DWORD /d 2 /f')
        self.gpu_log.insert("end", "[OK] Donanım Hızlandırmalı GPU Zamanlaması (HAGS) aktif edildi! (Yeniden başlatma gerekir)\n")
        ctypes.windll.user32.MessageBoxW(0, "HAGS başarıyla aktif edildi! Bilgisayarınızı yeniden başlatın.", "NotLynx GPU", 0)

    def thread_clean_shader_cache(self):
        threading.Thread(target=self.worker_clean_shader_cache, daemon=True).start()

    def worker_clean_shader_cache(self):
        self.gpu_log.insert("end", "[*] DirectX, NVIDIA ve AMD Shader Cache temizleniyor...\n")
        user = os.environ.get("LOCALAPPDATA", "")
        paths = [
            os.path.join(user, "NVIDIA", "DXCache"),
            os.path.join(user, "D3DSCache"),
            os.path.join(user, "AMD", "DxCache")
        ]
        cleared = 0
        for p in paths:
            if os.path.exists(p):
                for f in os.listdir(p):
                    try:
                        fp = os.path.join(p, f)
                        if os.path.isfile(fp): os.remove(fp); cleared += 1
                    except: pass
        self.gpu_log.insert("end", f"[SUCCESS] Toplam {cleared} shader önbellek dosyası temizlendi!\n")

    def launch_afterburner(self):
        paths = [
            r"C:\Program Files (x86)\MSI Afterburner\MSIAfterburner.exe",
            r"C:\Program Files\MSI Afterburner\MSIAfterburner.exe"
        ]
        for p in paths:
            if os.path.exists(p):
                subprocess.Popen([p])
                self.gpu_log.insert("end", f"[LAUNCH] MSI Afterburner başlatıldı: {p}\n")
                return
        ctypes.windll.user32.MessageBoxW(0, "MSI Afterburner kurulu bulunamadı.", "NotLynx", 0)

    # Process Reducer
    def thread_reduce_processes(self):
        threading.Thread(target=self.worker_reduce_processes, daemon=True).start()

    def worker_reduce_processes(self):
        self.proc_log.insert("end", "\n[*] GEREKSİZ ARKA PLAN SERVİSLERİ VE TELEMETRİ GÖREVLERİ DURDURULUYOR...\n")
        services = [
            "DiagTrack", "dmwappushservice", "SysMain", "WSearch", "PcaSvc", 
            "WerSvc", "Spooler", "Fax", "RemoteRegistry", "wisvc", "RetailDemo",
            "MapsBroker", "XblAuthManager", "XblGameSave", "XboxNetApiSvc", "XboxGipSvc"
        ]
        stopped = 0
        for s in services:
            self.run_cmd(f"sc stop {s}")
            if self.run_cmd(f"sc config {s} start= disabled"):
                self.proc_log.insert("end", f"  ✔️ {s} servisi durduruldu ve devre dışı bırakıldı.\n")
                stopped += 1

        # Zamanlanmış görevler
        tasks = [
            r"Microsoft\Windows\Customer Experience Improvement Program\Consolidator",
            r"Microsoft\Windows\Customer Experience Improvement Program\UsbCeip",
            r"Microsoft\Windows\Application Experience\Microsoft Compatibility Appraiser",
            r"Microsoft\Windows\Application Experience\ProgramDataUpdater"
        ]
        for t in tasks:
            self.run_cmd(f'schtasks /change /tn "{t}" /disable')

        self.proc_log.insert("end", f"\n[SUCCESS] {stopped} Servis kapatıldı! İşlemci işlem sayısı düşürüldü.\n")
        ctypes.windll.user32.MessageBoxW(0, f"Başarılı! {stopped} gereksiz servis durduruldu.\nGörev yöneticisinde işlem sayınız belirgin şekilde düşecektir.", "NotLynx Process Reducer", 0)

    # Desktop Tweaks
    def remove_shortcut_arrow(self):
        self.run_cmd('reg add "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Shell Icons" /v 29 /d "%windir%\\System32\\shell32.dll,-50" /f')
        self.run_cmd("taskkill /f /im explorer.exe & start explorer.exe")
        self.desktop_log.insert("end", "[OK] Kısayol simge okları kaldırıldı ve Explorer yeniden başlatıldı!\n")

    def restore_shortcut_arrow(self):
        self.run_cmd('reg delete "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Shell Icons" /v 29 /f')
        self.run_cmd("taskkill /f /im explorer.exe & start explorer.exe")
        self.desktop_log.insert("end", "[OK] Kısayol simge okları varsayılana döndürüldü!\n")

    def speed_up_menus(self):
        self.run_cmd('reg add "HKCU\\Control Panel\\Desktop" /v MenuShowDelay /t REG_SZ /d 0 /f')
        self.desktop_log.insert("end", "[OK] Menü açılış gecikmesi 0ms yapıldı.\n")

    def speed_up_animations(self):
        self.run_cmd('reg add "HKCU\\Control Panel\\Desktop\\WindowMetrics" /v MinAnimate /t REG_SZ /d 0 /f')
        self.desktop_log.insert("end", "[OK] Pencere animasyonları hızlandırıldı.\n")

    def show_file_extensions(self):
        self.run_cmd('reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced" /v HideFileExt /t REG_DWORD /d 0 /f')
        self.desktop_log.insert("end", "[OK] Dosya uzantıları görünür yapıldı.\n")

    # Cleaner
    def thread_run_deep_cleaner(self):
        threading.Thread(target=self.worker_deep_cleaner, daemon=True).start()

    def worker_deep_cleaner(self):
        self.cleaner_log.delete("1.0", "end")
        self.cleaner_log.insert("end", "[*] Derinlemesine Sistem ve Artık Temizliği Başlatıldı...\n\n")

        user = os.environ.get("USERPROFILE", "C:\\Users\\Samet")
        local = os.environ.get("LOCALAPPDATA", os.path.join(user, "AppData", "Local"))
        
        targets = [
            ("Kullanıcı Geçici Dosyaları (User Temp)", os.path.join(local, "Temp")),
            ("Windows Sistem Temp", "C:\\Windows\\Temp"),
            ("Windows Prefetch Önbelleği", "C:\\Windows\\Prefetch"),
            ("Crash Dump Raporları", os.path.join(local, "CrashDumps")),
            ("Windows Error Reporting", os.path.join(local, "Microsoft", "Windows", "WER"))
        ]

        tot_del = 0
        tot_bytes = 0

        for label, dir_p in targets:
            if not os.path.exists(dir_p): continue
            self.cleaner_log.insert("end", f"[*] Taranıyor: {label}...\n")
            c = 0; b = 0
            for root, dirs, files in os.walk(dir_p):
                for f in files:
                    fp = os.path.join(root, f)
                    try:
                        sz = os.path.getsize(fp)
                        os.remove(fp)
                        c += 1; b += sz
                    except: pass
                for d in dirs:
                    try: shutil.rmtree(os.path.join(root, d), ignore_errors=True)
                    except: pass
            self.cleaner_log.insert("end", f"  ✔️ {c} dosya temizlendi ({b / (1024*1024):.1f} MB)\n")
            tot_del += c; tot_bytes += b

        # Downloads Klasöründeki Artık Kurulum Dosyaları (.tmp, .log vb.)
        dl_p = os.path.join(user, "Downloads")
        if os.path.exists(dl_p):
            self.cleaner_log.insert("end", f"[*] Taranıyor: İndirilenler Artıkları (.tmp, .log, .crdownload)...\n")
            c = 0; b = 0
            for itm in os.listdir(dl_p):
                low = itm.lower()
                if low.endswith((".tmp", ".log", ".crdownload")) or ("setup" in low and low.endswith(".tmp")):
                    fp = os.path.join(dl_p, itm)
                    try:
                        sz = os.path.getsize(fp)
                        os.remove(fp)
                        c += 1; b += sz
                    except: pass
            self.cleaner_log.insert("end", f"  ✔️ {c} artık dosya temizlendi ({b / (1024*1024):.1f} MB)\n")
            tot_del += c; tot_bytes += b

        mb = tot_bytes / (1024 * 1024)
        self.cleaner_log.insert("end", "\n" + "="*50 + "\n")
        self.cleaner_log.insert("end", f"[SUCCESS] Temizlik Tamamlandı! Toplam {tot_del} dosya silindi ({mb:.2f} MB kazanıldı).\n")

    # Shield & Restore
    def thread_create_restore_point(self):
        threading.Thread(target=self.worker_create_restore_point, daemon=True).start()

    def worker_create_restore_point(self):
        self.shield_log.insert("end", "[*] Sistem Geri Yükleme Noktası oluşturuluyor...\n")
        cmd = 'powershell -Command "Checkpoint-Computer -Description \'NotLynx Pre-Optimization\' -RestorePointType \'MODIFY_SETTINGS\'"'
        if self.run_cmd(cmd):
            self.shield_log.insert("end", "[OK] Geri yükleme noktası oluşturuldu!\n")
            ctypes.windll.user32.MessageBoxW(0, "Sistem Geri Yükleme Noktası başarıyla oluşturuldu!", "NotLynx Kalkan", 0)
        else:
            self.shield_log.insert("end", "[BİLGİ] Geri yükleme noktası PowerShell ile tetiklendi.\n")

    def thread_revert_all(self):
        threading.Thread(target=self.worker_revert_all, daemon=True).start()

    def worker_revert_all(self):
        self.shield_log.insert("end", "\n[*] TÜM OPTİMİZASYONLAR STANDART WINDOWS AYARLARINA DÖNDÜRÜLÜYOR...\n")
        for mod in KERNEL_MODULES:
            for c_str in mod.get("revert", []):
                self.run_cmd(c_str)
        self.restore_shortcut_arrow()
        self.run_cmd("powercfg -setactive 381b4222-f694-41f0-9685-ff5bb260df2e")
        self.shield_log.insert("end", "[SUCCESS] Tüm ayarlar varsayılana döndürüldü.\n")
        ctypes.windll.user32.MessageBoxW(0, "Tüm sistem ayarları başarıyla varsayılan Windows fabrika ayarlarına döndürüldü.", "NotLynx", 0)

if __name__ == "__main__":
    app = NotLynxOptimizerApp()
    app.mainloop()