# -*- coding: utf-8 -*-
"""NotLynx Optimizer ek modülleri.

DebloatPage : gereksiz Windows uygulamalarını (yalnızca izin verilen listeden) kaldırır.
NvidiaPage  : NVIDIA GPU durumu (nvidia-smi), MSI modu, uygulama başına yüksek performanslı GPU,
              shader önbelleği temizleme.

Mantık (saf fonksiyonlar) arayüzden ayrıdır ve Windows dışında test edilebilir.
Hiçbir komut shell=True ile çalıştırılmaz; paket adları izin listesiyle ve desenle doğrulanır.
Kayıt defteri değişikliklerinde önceki değer %LOCALAPPDATA%\\NotLynx\\backup.json içine kaydedilir.
"""
import csv
import io
import json
import os
import re
import shutil
import subprocess
import sys
import threading

try:
    import winreg
except ImportError:  # Windows dışı: testler sahte winreg yerleştirir
    winreg = None

import customtkinter as ctk

BG, CARD, BORDER = "#020407", "#0a101d", "#16223b"
GREEN, CYAN, MUTED, WHITE = "#00ff66", "#38bdf8", "#94a3b8", "#ffffff"
WARN, RED = "#f59e0b", "#ef4444"

NO_WINDOW = 0x08000000 if sys.platform == "win32" else 0  # CREATE_NO_WINDOW: konsol penceresi çakmasın


# ======================================================================================
# Ortak yardımcılar
# ======================================================================================
def _popen_kwargs():
    return {"creationflags": NO_WINDOW} if NO_WINDOW else {}


def is_admin():
    try:
        import ctypes
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


_PS_ARGS = ["powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command"]
_PS_HEADER = "$OutputEncoding = [Console]::OutputEncoding = New-Object System.Text.UTF8Encoding $false; "


def _decode(raw):
    return (raw or b"").decode("utf-8", "replace").lstrip("\ufeff")


def run_ps(script, timeout=180):
    """PowerShell betiği çalıştırır -> (returncode, stdout, stderr). Hata olursa (-1, '', mesaj)."""
    try:
        res = subprocess.run(_PS_ARGS + [_PS_HEADER + script], capture_output=True, timeout=timeout, **_popen_kwargs())
    except Exception as exc:  # zaman aşımı, powershell yok vb.
        return -1, "", str(exc)
    return res.returncode, _decode(res.stdout), _decode(res.stderr)


def stream_ps(script, on_line, timeout=900):
    """PowerShell çıktısını satır satır iletir; çıkış kodunu döndürür (hata: -1)."""
    try:
        proc = subprocess.Popen(_PS_ARGS + [_PS_HEADER + script], stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, **_popen_kwargs())
    except Exception as exc:
        on_line("FAIL|-|" + str(exc))
        return -1
    try:
        for raw in iter(proc.stdout.readline, b""):
            line = _decode(raw).strip()
            if line:
                on_line(line)
        return proc.wait(timeout=timeout)
    except Exception as exc:
        proc.kill()
        on_line("FAIL|-|" + str(exc))
        return -1


# ======================================================================================
# 1) Gereksiz Windows uygulamaları
# ======================================================================================
# (paket adı, görünen ad, varsayılan işaretli mi)
APPS = [
    ("Microsoft.BingNews", "Haberler (Microsoft News)", True),
    ("Microsoft.GetHelp", "Yardım Al", True),
    ("Microsoft.Getstarted", "İpuçları", True),
    ("Microsoft.MicrosoftOfficeHub", "Office tanıtım uygulaması", True),
    ("Microsoft.MicrosoftSolitaireCollection", "Solitaire Collection", True),
    ("Microsoft.MixedReality.Portal", "Karma Gerçeklik Portalı", True),
    ("Microsoft.Microsoft3DViewer", "3D Görüntüleyici", True),
    ("Microsoft.MSPaint", "Paint 3D", True),
    ("Microsoft.Print3D", "3D Yazdır", True),
    ("Microsoft.SkypeApp", "Skype", True),
    ("Microsoft.People", "Kişiler", True),
    ("Microsoft.WindowsFeedbackHub", "Geri Bildirim Merkezi", True),
    ("Microsoft.WindowsMaps", "Haritalar", True),
    ("Microsoft.ZuneMusic", "Groove Müzik / Medya Oynatıcı", True),
    ("Microsoft.ZuneVideo", "Filmler ve TV", True),
    ("Microsoft.OneConnect", "Mobil Planlar", True),
    ("Microsoft.Wallet", "Microsoft Pay", True),
    ("Microsoft.549981C3F5F10", "Cortana", True),
    ("Clipchamp.Clipchamp", "Clipchamp video düzenleyici", True),
    ("MicrosoftTeams", "Microsoft Teams (kişisel)", True),
    ("king.com.CandyCrushSaga", "Candy Crush Saga", True),
    ("king.com.CandyCrushSodaSaga", "Candy Crush Soda Saga", True),
    ("Microsoft.BingWeather", "Hava Durumu", False),
    ("Microsoft.YourPhone", "Telefonunuz (Phone Link)", False),
    ("Microsoft.windowscommunicationsapps", "Posta ve Takvim", False),
    ("Microsoft.Todos", "Microsoft To Do", False),
    ("Microsoft.PowerAutomateDesktop", "Power Automate", False),
    ("Microsoft.MicrosoftStickyNotes", "Yapışkan Notlar", False),
    ("Microsoft.Office.OneNote", "OneNote (Store sürümü)", False),
]

# Hiçbir koşulda kaldırılmaz (sistem, Store, güvenlik, Xbox/oyun, sürücü paketleri).
PROTECTED_PREFIXES = (
    "Microsoft.WindowsStore", "Microsoft.StorePurchaseApp", "Microsoft.DesktopAppInstaller",
    "Microsoft.Windows.", "Microsoft.SecHealthUI", "Microsoft.WindowsCalculator", "Microsoft.WindowsCamera",
    "Microsoft.WindowsTerminal", "Microsoft.VCLibs", "Microsoft.NET", "Microsoft.UI.Xaml",
    "Microsoft.Services.Store", "Microsoft.MicrosoftEdge", "Microsoft.Edge", "Microsoft.LockApp",
    "Microsoft.AAD", "Microsoft.AccountsControl", "Microsoft.BioEnrollment", "Microsoft.CredDialogHost",
    "Microsoft.Xbox", "Microsoft.GamingApp", "Microsoft.GamingServices",
    "NVIDIA", "Realtek", "Intel", "AMD", "Lenovo",
)


def is_protected(name):
    return (name or "").lower().startswith(tuple(p.lower() for p in PROTECTED_PREFIXES))


def valid_pkg_name(name):
    return bool(re.fullmatch(r"[A-Za-z0-9._-]+", name or ""))


def parse_installed(text):
    """Get-AppxPackage çıktısındaki (satır başına bir) paket adlarından küçük harfli küme."""
    return {ln.strip().lower() for ln in (text or "").splitlines() if valid_pkg_name(ln.strip())}


def scan_installed():
    """Yüklü paket adları (küçük harf). Yönetici değilse yalnızca geçerli kullanıcıyı tarar."""
    _, out, _ = run_ps("Get-AppxPackage -AllUsers | ForEach-Object { $_.Name }")
    names = parse_installed(out)
    if not names:
        _, out, _ = run_ps("Get-AppxPackage | ForEach-Object { $_.Name }")
        names = parse_installed(out)
    return names


def build_remove_script(names, provisioned=False):
    """Seçilen paketleri kaldıran PowerShell betiği. Her paket için OK|SKIP|FAIL satırı yazar."""
    safe = []
    for n in names:
        if not valid_pkg_name(n):
            raise ValueError("Geçersiz paket adı: %r" % (n,))
        if is_protected(n):
            raise ValueError("Korumalı paket kaldırılamaz: %s" % n)
        safe.append(n)
    arr = ",".join("'%s'" % n for n in safe)
    prov = ("Get-AppxProvisionedPackage -Online | Where-Object { $_.DisplayName -eq $n } | "
            "ForEach-Object { Remove-AppxProvisionedPackage -Online -PackageName $_.PackageName | Out-Null }; "
            if provisioned else "")
    return ("$ErrorActionPreference = 'Stop'; $names = @(%s); "
            "foreach ($n in $names) { try { "
            "$pk = @(Get-AppxPackage -AllUsers -Name $n); "
            "if ($pk.Count -eq 0) { Write-Output ('SKIP|' + $n + '|none'); continue }; "
            "$pk | Remove-AppxPackage -AllUsers; %s"
            "Write-Output ('OK|' + $n) "
            "} catch { Write-Output ('FAIL|' + $n + '|' + (($_.Exception.Message) -replace '[\\r\\n]+', ' ')) } }"
            ) % (arr, prov)


def parse_result_line(line):
    """'OK|ad', 'SKIP|ad|none', 'FAIL|ad|mesaj' -> (durum, ad, mesaj); başka satırlar için None."""
    parts = (line or "").split("|", 2)
    if len(parts) >= 2 and parts[0] in ("OK", "SKIP", "FAIL"):
        return parts[0], parts[1], (parts[2] if len(parts) > 2 else "")
    return None


def remove_apps(names, provisioned, on_event):
    """Paketleri kaldırır. on_event(durum, ad, mesaj). (ok, atlanan, hata, çıkış_kodu) döndürür."""
    script = build_remove_script(names, provisioned)
    counts = {"OK": 0, "SKIP": 0, "FAIL": 0}

    def handle(line):
        res = parse_result_line(line)
        if res:
            counts[res[0]] += 1
            on_event(*res)

    rc = stream_ps(script, handle)
    return counts["OK"], counts["SKIP"], counts["FAIL"], rc


# ======================================================================================
# 2) NVIDIA / GPU
# ======================================================================================
SMI_FIELDS = ("name", "driver_version", "temperature.gpu", "power.draw", "power.limit", "clocks.sm",
              "clocks.max.sm", "clocks.mem", "clocks.max.mem", "utilization.gpu", "memory.used",
              "memory.total", "pstate")


def find_nvidia_smi():
    candidates = [shutil.which("nvidia-smi"),
                  os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "System32", "nvidia-smi.exe"),
                  os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"), "NVIDIA Corporation", "NVSMI", "nvidia-smi.exe")]
    for c in candidates:
        if c and os.path.isfile(c):
            return c
    return None


def parse_smi_csv(text):
    """nvidia-smi --format=csv,noheader,nounits çıktısının ilk satırı -> sözlük ([N/A] -> None)."""
    rows = list(csv.reader(io.StringIO((text or "").strip()), skipinitialspace=True))
    if not rows or len(rows[0]) < len(SMI_FIELDS):
        return None
    vals = []
    for v in rows[0][:len(SMI_FIELDS)]:
        v = v.strip()
        vals.append(None if (not v or v.startswith("[")) else v)
    return dict(zip(SMI_FIELDS, vals))


def query_gpu():
    exe = find_nvidia_smi()
    if not exe:
        return None
    try:
        res = subprocess.run([exe, "--query-gpu=" + ",".join(SMI_FIELDS), "--format=csv,noheader,nounits"],
                             capture_output=True, timeout=10, **_popen_kwargs())
    except Exception:
        return None
    if res.returncode != 0:
        return None
    return parse_smi_csv(_decode(res.stdout))


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def format_gpu(info):
    """Arayüzde gösterilecek metinler (anahtar -> metin). info None ise boş sözlük."""
    if not info:
        return {}

    def pair(a, b, unit, fmt):
        x, y = _num(a), _num(b)
        if x is None:
            return "—"
        return (fmt % x) + ((" / " + fmt % y) if y is not None else "") + " " + unit

    temp, util = _num(info.get("temperature.gpu")), _num(info.get("utilization.gpu"))
    used, total = _num(info.get("memory.used")), _num(info.get("memory.total"))
    return {
        "name": info.get("name") or "—",
        "driver": info.get("driver_version") or "—",
        "temp": ("%.0f °C" % temp) if temp is not None else "—",
        "power": pair(info.get("power.draw"), info.get("power.limit"), "W", "%.1f"),
        "sm": pair(info.get("clocks.sm"), info.get("clocks.max.sm"), "MHz", "%.0f"),
        "mem": pair(info.get("clocks.mem"), info.get("clocks.max.mem"), "MHz", "%.0f"),
        "util": ("%.0f%%" % util) if util is not None else "—",
        "vram": (("%.0f / %.0f MB" % (used, total)) if used is not None and total is not None else "—"),
        "pstate": info.get("pstate") or "—",
    }


# ---- kayıt defteri yardımcıları ------------------------------------------------------
def reg_read(root, path, name):
    """(var_mı, değer). Anahtar ya da değer yoksa (False, None)."""
    try:
        with winreg.OpenKey(root, path, 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as key:
            value, _ = winreg.QueryValueEx(key, name)
            return True, value
    except OSError:
        return False, None


def reg_write(root, path, name, value, reg_type):
    with winreg.CreateKeyEx(root, path, 0, winreg.KEY_SET_VALUE | winreg.KEY_WOW64_64KEY) as key:
        winreg.SetValueEx(key, name, 0, reg_type, value)


def reg_delete(root, path, name):
    try:
        with winreg.OpenKey(root, path, 0, winreg.KEY_SET_VALUE | winreg.KEY_WOW64_64KEY) as key:
            winreg.DeleteValue(key, name)
        return True
    except OSError:
        return False


def _enum_subkeys(key):
    i = 0
    while True:
        try:
            yield winreg.EnumKey(key, i)
        except OSError:
            return
        i += 1


# ---- yedek dosyası: değiştirmeden önceki değer saklanır, geri alma buradan yapılır ---------
def backup_path():
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    return os.path.join(base, "NotLynx", "backup.json")


def load_backup():
    try:
        with open(backup_path(), "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def save_backup(data):
    path = backup_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def remember(section, key, existed, value):
    """İlk değişiklikte önceki durumu saklar; sonrakilerde üzerine yazmaz (orijinal korunur)."""
    data = load_backup()
    sec = data.setdefault(section, {})
    if key not in sec:
        sec[key] = {"existed": bool(existed), "value": value}
        save_backup(data)


def forget(section, key):
    data = load_backup()
    if data.get(section, {}).pop(key, None) is not None:
        save_backup(data)


# ---- MSI modu ------------------------------------------------------------------------
PCI_ENUM = r"SYSTEM\CurrentControlSet\Enum\PCI"
MSI_SUB = r"Device Parameters\Interrupt Management\MessageSignaledInterruptProperties"


def find_nvidia_display_devices():
    """VEN_10DE ve sınıfı Display olan PCI aygıtları: [{path, hw, desc, msi}]. msi: 1/0/None (ayarsız)."""
    devices = []
    try:
        pci = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, PCI_ENUM, 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY)
    except OSError:
        return devices
    with pci:
        for hw in _enum_subkeys(pci):
            if not hw.upper().startswith("VEN_10DE"):
                continue
            try:
                hw_key = winreg.OpenKey(pci, hw, 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY)
            except OSError:
                continue
            with hw_key:
                for inst in _enum_subkeys(hw_key):
                    path = PCI_ENUM + "\\" + hw + "\\" + inst
                    ok, cls = reg_read(winreg.HKEY_LOCAL_MACHINE, path, "Class")
                    if not ok or str(cls).lower() != "display":
                        continue
                    _, desc = reg_read(winreg.HKEY_LOCAL_MACHINE, path, "DeviceDesc")
                    msi_ok, msi = reg_read(winreg.HKEY_LOCAL_MACHINE, path + "\\" + MSI_SUB, "MSISupported")
                    devices.append({"path": path, "hw": hw, "desc": str(desc or hw).split(";")[-1],
                                    "msi": int(msi) if msi_ok else None})
    return devices


def set_msi(dev_path, enabled=True):
    full = dev_path + "\\" + MSI_SUB
    existed, old = reg_read(winreg.HKEY_LOCAL_MACHINE, full, "MSISupported")
    remember("msi", dev_path, existed, old)
    reg_write(winreg.HKEY_LOCAL_MACHINE, full, "MSISupported", 1 if enabled else 0, winreg.REG_DWORD)


def restore_msi(dev_path):
    """Yedekteki önceki değeri geri yazar. Yedek yoksa False."""
    entry = load_backup().get("msi", {}).get(dev_path)
    if not entry:
        return False
    full = dev_path + "\\" + MSI_SUB
    if entry.get("existed"):
        reg_write(winreg.HKEY_LOCAL_MACHINE, full, "MSISupported", int(entry["value"]), winreg.REG_DWORD)
    else:
        reg_delete(winreg.HKEY_LOCAL_MACHINE, full, "MSISupported")
    forget("msi", dev_path)
    return True


# ---- uygulama başına GPU tercihi (Windows Grafik Ayarları) -----------------------------
GPU_PREF_KEY = r"Software\Microsoft\DirectX\UserGpuPreferences"
GPU_PREF_NAMES = {0: "Sistem varsayılanı", 1: "Güç tasarrufu", 2: "Yüksek performans (NVIDIA)"}


def merge_gpu_pref(existing, pref=2):
    """Var olan 'a=b;c=d;' değerini koruyup GpuPreference ekler/günceller."""
    kept = [p for p in (existing or "").split(";") if p.strip() and not p.strip().lower().startswith("gpupreference=")]
    kept.append("GpuPreference=%d" % pref)
    return ";".join(kept) + ";"


def strip_gpu_pref(existing):
    """GpuPreference'ı çıkarır; geriye başka ayar kalmazsa boş metin döner."""
    kept = [p for p in (existing or "").split(";") if p.strip() and not p.strip().lower().startswith("gpupreference=")]
    return (";".join(kept) + ";") if kept else ""


def list_gpu_prefs():
    """{exe yolu: tercih (0/1/2 ya da None)}"""
    out = {}
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, GPU_PREF_KEY, 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as key:
            i = 0
            while True:
                try:
                    name, value, _ = winreg.EnumValue(key, i)
                except OSError:
                    break
                i += 1
                m = re.search(r"GpuPreference=(\d)", str(value))
                out[name] = int(m.group(1)) if m else None
    except OSError:
        pass
    return out


def set_gpu_pref(exe_path, pref=2):
    path = os.path.normpath(exe_path)
    if not path.lower().endswith(".exe"):
        raise ValueError("Yalnızca .exe dosyaları seçilebilir.")
    if not os.path.isfile(path):
        raise ValueError("Dosya bulunamadı: " + path)
    existed, old = reg_read(winreg.HKEY_CURRENT_USER, GPU_PREF_KEY, path)
    remember("gpu_pref", path, existed, old)
    reg_write(winreg.HKEY_CURRENT_USER, GPU_PREF_KEY, path, merge_gpu_pref(old if existed else "", pref), winreg.REG_SZ)
    return path


def remove_gpu_pref(path):
    """Yedek varsa önceki değeri geri yazar; yoksa yalnızca GpuPreference ayarını kaldırır."""
    entry = load_backup().get("gpu_pref", {}).get(path)
    if entry:
        if entry.get("existed") and entry.get("value"):
            reg_write(winreg.HKEY_CURRENT_USER, GPU_PREF_KEY, path, entry["value"], winreg.REG_SZ)
        else:
            reg_delete(winreg.HKEY_CURRENT_USER, GPU_PREF_KEY, path)
        forget("gpu_pref", path)
        return
    existed, old = reg_read(winreg.HKEY_CURRENT_USER, GPU_PREF_KEY, path)
    if not existed:
        return
    rest = strip_gpu_pref(old)
    if rest:
        reg_write(winreg.HKEY_CURRENT_USER, GPU_PREF_KEY, path, rest, winreg.REG_SZ)
    else:
        reg_delete(winreg.HKEY_CURRENT_USER, GPU_PREF_KEY, path)


# ---- shader önbelleği ----------------------------------------------------------------
SHADER_CACHE_NAMES = ("DXCache", "GLCache", "D3DSCache", "NV_Cache")


def shader_cache_dirs():
    local, prog = os.environ.get("LOCALAPPDATA", ""), os.environ.get("ProgramData", "")
    dirs = []
    if local:
        dirs += [os.path.join(local, "NVIDIA", "DXCache"), os.path.join(local, "NVIDIA", "GLCache"),
                 os.path.join(local, "D3DSCache")]
    if prog:
        dirs.append(os.path.join(prog, "NVIDIA Corporation", "NV_Cache"))
    return dirs


def clean_dir_contents(path):
    """Klasörün içini boşaltır (klasörün kendisi kalır). (silinen dosya, bayt)"""
    files = size = 0
    for root, dirs, names in os.walk(path, topdown=False):
        for f in names:
            fp = os.path.join(root, f)
            try:
                sz = os.path.getsize(fp)
                os.remove(fp)
                files += 1
                size += sz
            except OSError:
                pass
        for d in dirs:
            try:
                os.rmdir(os.path.join(root, d))
            except OSError:
                pass
    return files, size


def clean_shader_cache(on_line=lambda s: None):
    total_files = total_bytes = 0
    for d in shader_cache_dirs():
        if os.path.basename(d) not in SHADER_CACHE_NAMES:  # güvenlik: yalnızca bilinen önbellek klasörleri
            continue
        if not os.path.isdir(d):
            on_line("  - %s: yok" % d)
            continue
        files, size = clean_dir_contents(d)
        total_files += files
        total_bytes += size
        on_line("  ✔ %s: %d dosya (%.1f MB)" % (d, files, size / (1024 * 1024)))
    return total_files, total_bytes


# ======================================================================================
# Arayüz
# ======================================================================================
def _ask_yes_no(title, text):
    from tkinter import messagebox
    return bool(messagebox.askyesno(title, text, icon="warning"))


class _Page(ctk.CTkFrame):
    """Ortak iskelet: başlık, log kutusu, meşgul durumu (ana pencereyle paylaşılır)."""

    def __init__(self, master, host=None):
        super().__init__(master, fg_color=BG)
        self.host = host
        self._busy = False
        self._buttons = []
        self._shown = False
        self.grid_columnconfigure(0, weight=1)

    def _title(self, row, title, subtitle):
        box = ctk.CTkFrame(self, fg_color="transparent")
        box.grid(row=row, column=0, padx=30, pady=(25, 10), sticky="ew")
        ctk.CTkLabel(box, text=title, font=ctk.CTkFont(size=22, weight="bold"), text_color=WHITE).pack(anchor="w")
        ctk.CTkLabel(box, text=subtitle, font=ctk.CTkFont(size=13), text_color=MUTED,
                     wraplength=860, anchor="w").pack(anchor="w", pady=(4, 0))

    def _button(self, parent, text, command, kind="ghost", width=140, height=34):
        colors = {"primary": (GREEN, "#00cc52", "#020407"), "ghost": ("#0f172a", "#1e293b", CYAN),
                  "danger": (RED, "#dc2626", WHITE)}[kind]
        btn = ctk.CTkButton(parent, text=text, command=command, width=width, height=height, fg_color=colors[0],
                            hover_color=colors[1], text_color=colors[2], corner_radius=8,
                            font=ctk.CTkFont(size=13, weight="bold"))
        self._buttons.append(btn)
        return btn

    def _make_log(self, row, height=130):
        self.log_box = ctk.CTkTextbox(self, height=height, fg_color="#05080f", border_color="#131e35",
                                      border_width=1, corner_radius=8, text_color=GREEN,
                                      font=ctk.CTkFont(family="Consolas", size=12))
        self.log_box.grid(row=row, column=0, padx=30, pady=(0, 10), sticky="ew")

    def log(self, text):
        """Her iş parçacığından güvenle çağrılabilir."""
        self.after(0, self._log_now, text)

    def _log_now(self, text):
        self.log_box.insert("end", text)
        self.log_box.see("end")

    def _set_host_busy(self, state):
        """Ana pencerenin meşgul durumunu günceller (set_busy yoksa is_busy alanını doğrudan yazar)."""
        if self.host is None:
            return
        setter = getattr(self.host, "set_busy", None)
        if callable(setter):
            setter(state)
        else:
            self.host.is_busy = state

    def _begin(self):
        host_busy = bool(self.host is not None and getattr(self.host, "is_busy", False))
        if self._busy or host_busy:
            self.log("[!] Başka bir işlem sürüyor, bitmesini bekleyin.\n")
            return False
        self._busy = True
        self._set_host_busy(True)
        for b in self._buttons:
            b.configure(state="disabled")
        return True

    def _end(self):
        def done():
            self._busy = False
            self._set_host_busy(False)
            for b in self._buttons:
                b.configure(state="normal")
        self.after(0, done)

    def on_show(self):
        """Sayfa ilk açıldığında bir kez çağrılır."""
        if not self._shown:
            self._shown = True
            self.first_show()

    def first_show(self):
        pass


# --------------------------------------------------------------------------------------
class DebloatPage(_Page):
    def __init__(self, master, host=None):
        super().__init__(master, host)
        self.grid_rowconfigure(3, weight=1)
        self.rows = {}          # paket -> (onay kutusu, durum etiketi, varsayılan)
        self._installed = set()
        self._title(0, "GEREKSİZ WINDOWS UYGULAMALARINI KALDIR",
                    "Windows ile gelen ve çoğu kullanıcının açmadığı uygulamaları kaldırır. Yalnızca aşağıdaki liste işlenir; "
                    "sistem uygulamaları ve Xbox/oyun bileşenleri listede yoktur.")

        warn = ctk.CTkFrame(self, fg_color="#1a1202", border_color=WARN, border_width=1, corner_radius=8)
        warn.grid(row=1, column=0, padx=30, pady=(0, 8), sticky="ew")
        ctk.CTkLabel(warn, text="Kaldırılan uygulamalar geri alınamaz; Microsoft Store'dan yeniden kurulabilir. "
                                "Önce Kernel Modülleri sayfasından bir geri yükleme noktası oluşturmanız önerilir.",
                     font=ctk.CTkFont(size=13, weight="bold"), text_color=WARN, wraplength=900,
                     anchor="w").pack(padx=14, pady=10, anchor="w")

        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.grid(row=2, column=0, padx=30, pady=(0, 8), sticky="ew")
        self._button(bar, "↻ Taramayı Yenile", self.scan, width=150).pack(side="left", padx=(0, 8))
        self._button(bar, "✓ Önerilenleri Seç", self.select_recommended, width=150).pack(side="left", padx=(0, 8))
        self._button(bar, "✕ Seçimi Temizle", self.clear_selection, width=140).pack(side="left", padx=(0, 8))
        self.chk_prov = ctk.CTkCheckBox(bar, text="Yeni kullanıcı profillerinden de kaldır",
                                        font=ctk.CTkFont(size=13), text_color=MUTED, fg_color=GREEN,
                                        hover_color="#00cc52", border_color="#334155", checkmark_color="#020407")
        self.chk_prov.pack(side="right")

        scroll = ctk.CTkScrollableFrame(self, fg_color="#05080f", border_color="#131e35", border_width=1, corner_radius=12)
        scroll.grid(row=3, column=0, padx=30, pady=(0, 8), sticky="nsew")
        scroll.grid_columnconfigure(0, weight=1)
        r = 0
        for heading, flag in (("ÖNERİLEN (varsayılan işaretli)", True), ("İSTEĞE BAĞLI (varsayılan işaretsiz)", False)):
            ctk.CTkLabel(scroll, text=heading, font=ctk.CTkFont(size=13, weight="bold"), text_color=CYAN,
                         anchor="w").grid(row=r, column=0, padx=14, pady=(10, 4), sticky="w")
            r += 1
            for pkg, title, default in APPS:
                if default != flag:
                    continue
                row = ctk.CTkFrame(scroll, fg_color=CARD, corner_radius=8, border_color=BORDER, border_width=1)
                row.grid(row=r, column=0, padx=8, pady=3, sticky="ew")
                row.grid_columnconfigure(0, weight=1)
                cb = ctk.CTkCheckBox(row, text=title, font=ctk.CTkFont(size=14, weight="bold"), text_color=WHITE,
                                     fg_color=GREEN, hover_color="#00cc52", border_color="#334155",
                                     checkmark_color="#020407")
                cb.grid(row=0, column=0, padx=14, pady=(10, 0), sticky="w")
                st = ctk.CTkLabel(row, text=pkg + "  •  taranmadı", font=ctk.CTkFont(size=12), text_color=MUTED, anchor="w")
                st.grid(row=1, column=0, padx=44, pady=(0, 8), sticky="w")
                self.rows[pkg] = (cb, st, default)
                r += 1

        self._make_log(4, height=120)
        self.btn_remove = self._button(self, "🗑️  SEÇİLİ UYGULAMALARI KALDIR", self.apply, kind="danger", height=48)
        self.btn_remove.configure(font=ctk.CTkFont(size=14, weight="bold"))
        self.btn_remove.grid(row=5, column=0, padx=30, pady=(0, 22), sticky="ew")
        self.log("[SİSTEM] Uygulama listesi hazır. Önce tarama yapılır; yalnızca yüklü uygulamalar seçilebilir.\n")

    # ---- seçim
    def first_show(self):
        self.scan()

    def select_recommended(self):
        for pkg, (cb, st, default) in self.rows.items():
            if pkg.lower() in self._installed and default:
                cb.select()
            else:
                cb.deselect()

    def clear_selection(self):
        for cb, st, default in self.rows.values():
            cb.deselect()

    # ---- tarama
    def scan(self):
        if not self._begin():
            return
        self.log("[*] Yüklü uygulamalar taranıyor...\n")
        threading.Thread(target=self._scan_worker, daemon=True).start()

    def _scan_worker(self):
        try:
            self.after(0, self._apply_scan, scan_installed())
        except Exception as exc:
            self.log("[HATA] Tarama başarısız: %s\n" % exc)
        finally:
            self._end()

    def _apply_scan(self, names):
        self._installed = set(names)
        found = 0
        for pkg, (cb, st, default) in self.rows.items():
            if pkg.lower() in self._installed:
                found += 1
                cb.configure(state="normal")
                (cb.select if default else cb.deselect)()
                st.configure(text=pkg + "  •  yüklü", text_color=GREEN)
            else:
                cb.deselect()
                cb.configure(state="disabled")
                st.configure(text=pkg + "  •  yüklü değil", text_color=MUTED)
        if not names:
            self.log("[!] Tarama sonuç vermedi (PowerShell çalışmadı ya da yönetici izni yok).\n")
        else:
            self.log("[OK] Listedeki uygulamalardan %d tanesi yüklü.\n" % found)

    # ---- kaldırma
    def apply(self):
        if not is_admin():
            self.log("[!] Uygulama kaldırmak için yönetici izni gerekir (uygulamayı 'Yönetici olarak çalıştır' ile açın).\n")
            return
        chosen = [pkg for pkg, (cb, st, d) in self.rows.items() if cb.get() == 1 and pkg.lower() in self._installed]
        if not chosen:
            self.log("[!] Kaldırılacak uygulama seçilmedi.\n")
            return
        titles = {p: t for p, t, d in APPS}
        text = "%d uygulama kaldırılacak:\n\n%s\n\nBu işlem geri alınamaz (Microsoft Store'dan yeniden kurulabilir). Devam edilsin mi?" % (
            len(chosen), "\n".join("• " + titles[p] for p in chosen))
        if not _ask_yes_no("NotLynx - Uygulama Kaldırma", text):
            self.log("[*] Vazgeçildi.\n")
            return
        if not self._begin():
            return
        prov = self.chk_prov.get() == 1
        threading.Thread(target=self._remove_worker, args=(chosen, prov), daemon=True).start()

    def _remove_worker(self, chosen, provisioned):
        titles = {p: t for p, t, d in APPS}
        try:
            self.log("\n" + "=" * 50 + "\n[*] %d uygulama kaldırılıyor...\n" % len(chosen))

            def on_event(status, name, msg):
                title = titles.get(name, name)
                if status == "OK":
                    self.log("  ✔ %s kaldırıldı\n" % title)
                elif status == "SKIP":
                    self.log("  - %s: yüklü değil\n" % title)
                else:
                    self.log("  ✖ %s: %s\n" % (title, msg or "kaldırılamadı"))

            ok, skipped, failed, rc = remove_apps(chosen, provisioned, on_event)
            self.log("[SONUÇ] Kaldırılan: %d, atlanan: %d, başarısız: %d\n" % (ok, skipped, failed))
            if rc != 0 and not (ok or skipped or failed):
                self.log("[HATA] PowerShell çalışmadı (çıkış kodu %s).\n" % rc)
            self.after(0, self._apply_scan, scan_installed())
        except Exception as exc:
            self.log("[HATA] Kaldırma işlemi beklenmedik biçimde durdu: %s\n" % exc)
        finally:
            self._end()


# --------------------------------------------------------------------------------------
class NvidiaPage(_Page):
    INFO_ROWS = (("name", "Model"), ("driver", "Sürücü"), ("temp", "Sıcaklık"), ("power", "Güç (anlık / sınır)"),
                 ("sm", "Çekirdek saati (anlık / azami)"), ("mem", "Bellek saati (anlık / azami)"),
                 ("util", "GPU kullanımı"), ("vram", "Video belleği (kullanılan / toplam)"),
                 ("pstate", "Güç durumu (P-state)"))

    def __init__(self, master, host=None):
        super().__init__(master, host)
        self.grid_rowconfigure(1, weight=1)
        self._status_busy = False
        self._laptop = False
        self._title(0, "NVIDIA & GPU AYARLARI",
                    "GPU durumunu canlı izleyin, MSI modunu denetleyin, oyunları NVIDIA GPU'ya yönlendirin ve "
                    "shader önbelleğini temizleyin. Her değişiklikte önceki değer yedeklenir.")
        scroll = ctk.CTkScrollableFrame(self, fg_color="#05080f", border_color="#131e35", border_width=1, corner_radius=12)
        scroll.grid(row=1, column=0, padx=30, pady=(0, 8), sticky="nsew")
        scroll.grid_columnconfigure(0, weight=1)

        # 1) durum
        card = self._card(scroll, 0, "GPU DURUMU (nvidia-smi)")
        grid = ctk.CTkFrame(card, fg_color="transparent")
        grid.grid(row=1, column=0, padx=16, pady=(0, 6), sticky="ew")
        self.info = {}
        for i, (key, label) in enumerate(self.INFO_ROWS):
            ctk.CTkLabel(grid, text=label, font=ctk.CTkFont(size=13), text_color=MUTED, anchor="w").grid(
                row=i, column=0, padx=(0, 22), pady=2, sticky="w")
            val = ctk.CTkLabel(grid, text="—", font=ctk.CTkFont(size=13, weight="bold"), text_color=WHITE, anchor="w")
            val.grid(row=i, column=1, pady=2, sticky="w")
            self.info[key] = val
        bar = ctk.CTkFrame(card, fg_color="transparent")
        bar.grid(row=2, column=0, padx=16, pady=(4, 14), sticky="ew")
        self._button(bar, "↻ Yenile", self.refresh_status, width=110).pack(side="left", padx=(0, 14))
        self.live = ctk.CTkSwitch(bar, text="Canlı izle (2 sn)", font=ctk.CTkFont(size=13), text_color=MUTED,
                                  progress_color=GREEN, command=self._on_live)
        self.live.pack(side="left")

        # 2) MSI
        card = self._card(scroll, 1, "MSI MODU (MESAJ TABANLI KESME)")
        self._note(card, 1, "MSI, GPU'nun kesme isteklerini daha düşük gecikmeyle ileten Windows kesme türüdür. "
                            "Çoğu RTX kartında zaten açıktır; gerçek durum aşağıda kayıt defterinden okunur. "
                            "Değişiklik yönetici izni ve yeniden başlatma gerektirir.")
        self.msi_label = ctk.CTkLabel(card, text="Durum okunmadı", font=ctk.CTkFont(size=13, weight="bold"),
                                      text_color=WHITE, anchor="w", wraplength=820)
        self.msi_label.grid(row=2, column=0, padx=16, pady=(0, 6), sticky="w")
        bar = ctk.CTkFrame(card, fg_color="transparent")
        bar.grid(row=3, column=0, padx=16, pady=(0, 14), sticky="ew")
        self._button(bar, "MSI modunu aç", self.apply_msi, kind="primary", width=150).pack(side="left", padx=(0, 8))
        self._button(bar, "Önceki değere dön", self.restore_msi_ui, width=160).pack(side="left", padx=(0, 8))
        self._button(bar, "↻ Durumu yenile", self.refresh_msi, width=140).pack(side="left")

        # 3) uygulama başına GPU tercihi
        card = self._card(scroll, 2, "OYUN / UYGULAMA İÇİN YÜKSEK PERFORMANSLI GPU")
        self._note(card, 1, "Hibrit (Optimus) dizüstülerde bir uygulamanın hangi GPU'yu kullanacağını Windows belirler. "
                            "Seçtiğiniz .exe, Windows Grafik Ayarları'nda 'Yüksek performans' (NVIDIA GPU) olarak işaretlenir.")
        bar = ctk.CTkFrame(card, fg_color="transparent")
        bar.grid(row=2, column=0, padx=16, pady=(0, 6), sticky="ew")
        self._button(bar, "Uygulama seç ve ayarla…", self.choose_app, kind="primary", width=210).pack(side="left", padx=(0, 8))
        self._button(bar, "↻ Listeyi yenile", self.refresh_prefs, width=140).pack(side="left")
        self.pref_box = ctk.CTkFrame(card, fg_color="transparent")
        self.pref_box.grid(row=3, column=0, padx=16, pady=(0, 14), sticky="ew")
        self.pref_box.grid_columnconfigure(0, weight=1)

        # 4) shader önbelleği
        card = self._card(scroll, 3, "SHADER ÖNBELLEĞİ")
        self._note(card, 1, "DirectX ve NVIDIA shader önbelleklerini temizler. Bozuk ya da eski önbellek takılmalara yol açabilir; "
                            "önbellek oyunlar açıldıkça yeniden oluşur (ilk açılış biraz yavaş olabilir).")
        bar = ctk.CTkFrame(card, fg_color="transparent")
        bar.grid(row=2, column=0, padx=16, pady=(0, 14), sticky="ew")
        self._button(bar, "Önbelleği temizle", self.clean_cache, width=170).pack(side="left")

        # 5) not
        card = self._card(scroll, 4, "BİLİNÇLİ OLARAK DEĞİŞTİRİLMEYENLER")
        self.note_label = self._note(card, 1, "Güç yönetimi (PowerMizer) kilitleme ve Dynamic Boost ayarları otomatik değiştirilmez: "
                                             "dizüstülerde ısınmayı ve pil tüketimini artırabilir, soğutma düzenini bozabilir. "
                                             "Gerekirse NVIDIA Denetim Masası > 3D ayarlarını yönet > Güç yönetimi modu "
                                             "üzerinden oyun bazında ayarlayın.")
        self._make_log(2, height=120)
        self.log("[SİSTEM] NVIDIA sayfası hazır.\n")

    # ---- küçük yardımcılar
    def _card(self, parent, row, title):
        card = ctk.CTkFrame(parent, fg_color=CARD, corner_radius=10, border_color=BORDER, border_width=1)
        card.grid(row=row, column=0, padx=10, pady=6, sticky="ew")
        card.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=13, weight="bold"), text_color=CYAN, anchor="w").grid(
            row=0, column=0, padx=16, pady=(12, 6), sticky="w")
        return card

    def _note(self, card, row, text):
        lbl = ctk.CTkLabel(card, text=text, font=ctk.CTkFont(size=13), text_color=MUTED, wraplength=820, anchor="w")
        lbl.grid(row=row, column=0, padx=16, pady=(0, 8), sticky="w")
        return lbl

    def first_show(self):
        self.refresh_status()
        self.refresh_msi()
        self.refresh_prefs()

    # ---- GPU durumu
    def refresh_status(self):
        if self._status_busy:
            return
        self._status_busy = True
        threading.Thread(target=self._status_worker, daemon=True).start()

    def _status_worker(self):
        info = query_gpu()
        self.after(0, self._show_status, info)

    def _show_status(self, info):
        self._status_busy = False
        data = format_gpu(info)
        if not data:
            for key, lbl in self.info.items():
                lbl.configure(text="—")
            self.info["name"].configure(text="nvidia-smi bulunamadı ya da GPU okunamadı")
            return
        for key, lbl in self.info.items():
            lbl.configure(text=data.get(key, "—"))
        self._laptop = "laptop" in data["name"].lower()

    def _on_live(self):
        if self.live.get() == 1:
            self._live_tick()

    def _live_tick(self):
        if self.live.get() != 1:
            return
        if self.winfo_ismapped():
            self.refresh_status()
        self.after(2000, self._live_tick)

    # ---- MSI
    def refresh_msi(self):
        self._msi_devices = find_nvidia_display_devices()
        if not self._msi_devices:
            self.msi_label.configure(text="NVIDIA ekran aygıtı bulunamadı.", text_color=WARN)
            return
        names = {1: "AÇIK (MSISupported=1)", 0: "KAPALI (MSISupported=0)", None: "ayarlanmamış (Windows/sürücü varsayılanı)"}
        lines = ["%s: %s" % (d["desc"], names[d["msi"]]) for d in self._msi_devices]
        self.msi_label.configure(text="\n".join(lines), text_color=GREEN if all(d["msi"] == 1 for d in self._msi_devices) else WHITE)

    def apply_msi(self):
        if not is_admin():
            self.log("[!] MSI ayarı için yönetici izni gerekir.\n")
            return
        self.refresh_msi()
        changed = 0
        for d in self._msi_devices:
            if d["msi"] == 1:
                self.log("[OK] %s: MSI zaten açık, değişiklik yapılmadı.\n" % d["desc"])
                continue
            try:
                set_msi(d["path"], True)
                changed += 1
                self.log("[OK] %s: MSI açıldı (önceki değer yedeklendi).\n" % d["desc"])
            except OSError as exc:
                self.log("[HATA] %s: %s\n" % (d["desc"], exc))
        self.refresh_msi()
        if changed:
            self.log("[ÖNEMLİ] Değişikliğin geçerli olması için bilgisayarı yeniden başlatın.\n")

    def restore_msi_ui(self):
        if not is_admin():
            self.log("[!] Geri alma için yönetici izni gerekir.\n")
            return
        self.refresh_msi()
        restored = 0
        for d in self._msi_devices:
            try:
                if restore_msi(d["path"]):
                    restored += 1
                    self.log("[OK] %s: önceki değer geri yüklendi.\n" % d["desc"])
            except OSError as exc:
                self.log("[HATA] %s: %s\n" % (d["desc"], exc))
        if not restored:
            self.log("[BİLGİ] Geri yüklenecek yedek yok (bu uygulama MSI ayarını değiştirmemiş).\n")
        self.refresh_msi()

    # ---- uygulama başına GPU tercihi
    def refresh_prefs(self):
        for w in self.pref_box.winfo_children():
            w.destroy()
        prefs = {p: v for p, v in list_gpu_prefs().items() if v is not None}
        if not prefs:
            ctk.CTkLabel(self.pref_box, text="Henüz uygulama başına GPU tercihi yok.", font=ctk.CTkFont(size=13),
                         text_color=MUTED, anchor="w").grid(row=0, column=0, sticky="w")
            return
        for i, (path, pref) in enumerate(sorted(prefs.items())):
            row = ctk.CTkFrame(self.pref_box, fg_color="#070b14", corner_radius=8, border_color="#131e35", border_width=1)
            row.grid(row=i, column=0, pady=3, sticky="ew")
            row.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(row, text=os.path.basename(path) + "  •  " + GPU_PREF_NAMES.get(pref, "ayarsız"),
                         font=ctk.CTkFont(size=13, weight="bold"), text_color=WHITE, anchor="w").grid(
                row=0, column=0, padx=12, pady=(8, 0), sticky="w")
            ctk.CTkLabel(row, text=path, font=ctk.CTkFont(size=12), text_color=MUTED, anchor="w").grid(
                row=1, column=0, padx=12, pady=(0, 8), sticky="w")
            ctk.CTkButton(row, text="Kaldır", width=80, height=30, fg_color="#1e293b", hover_color="#334155",
                          text_color=WHITE, corner_radius=6, font=ctk.CTkFont(size=12, weight="bold"),
                          command=lambda p=path: self.remove_pref(p)).grid(row=0, column=1, rowspan=2, padx=12)

    def choose_app(self):
        from tkinter import filedialog
        path = filedialog.askopenfilename(title="Oyun veya uygulama (.exe) seçin", filetypes=[("Uygulama", "*.exe")])
        if not path:
            return
        try:
            saved = set_gpu_pref(path, 2)
            self.log("[OK] %s -> Yüksek performans (NVIDIA GPU). Uygulama yeniden başlatılınca geçerli olur.\n" % saved)
        except (ValueError, OSError) as exc:
            self.log("[HATA] %s\n" % exc)
        self.refresh_prefs()

    def remove_pref(self, path):
        try:
            remove_gpu_pref(path)
            self.log("[OK] %s: GPU tercihi kaldırıldı/önceki değere döndü.\n" % path)
        except OSError as exc:
            self.log("[HATA] %s\n" % exc)
        self.refresh_prefs()

    # ---- shader önbelleği
    def clean_cache(self):
        if not self._begin():
            return
        threading.Thread(target=self._clean_worker, daemon=True).start()

    def _clean_worker(self):
        try:
            self.log("\n[*] Shader önbelleği temizleniyor...\n")
            files, size = clean_shader_cache(lambda s: self.log(s + "\n"))
            self.log("[SONUÇ] %d dosya silindi, %.1f MB yer açıldı.\n" % (files, size / (1024 * 1024)))
        except Exception as exc:
            self.log("[HATA] Temizlik durdu: %s\n" % exc)
        finally:
            self._end()
