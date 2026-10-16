# NotLynx Optimizer - Project Instructions for Claude Code

## ⚡ Project Overview
**NotLynx Optimizer v2.0** is an open-source, high-performance Windows kernel latency and system optimization suite designed for competitive gamers and power users. It eliminates micro-stutters, minimizes DPC and input latency, reserves bandwidth for game traffic, and provides deep system cleaning.

- **Author / Lead**: NotLynx (@notlynx_7 on TikTok, @notlynx7 on Instagram)
- **Primary Repository**: `https://github.com/samet2007topcu-art/NotLynxOptimizer.git`
- **Location**: `C:/Users/Samet/source/repos/NotlynxOptimizer`

---

## 🏗️ Architecture & Tech Stack
1. **Desktop GUI (`NotLynxOptimizer_GUI.py`)**:
   - Built with **CustomTkinter** (`Dark` theme, custom `#00ff66` cyberpunk neon accents, obsidian black `#040609` background).
   - Fully multithreaded: All kernel tweaks and deep cleaning operations run in background worker threads (`threading.Thread`) with real-time UI logging and zero interface freezing.
   - UAC elevation detection (`ctypes.windll.shell32.IsUserAnAdmin()`) and one-click self-elevation via `ShellExecuteW(..., 'runas')`.
   - Reversibility: Every single module has both an `apply` and a `revert` implementation to restore factory defaults.
   - Safety: Integrated Windows System Restore Point creation (`Checkpoint-Computer`).

2. **10 Kernel Modules**:
   - `[01] Sistem Zamanlayıcısı (BCDedit)`: `useplatformclock false`, `disabledynamictick yes`, `tscsyncpolicy Enhanced`.
   - `[02] Network Throttling & Yanıt Süresi`: `NetworkThrottlingIndex = 0xFFFFFFFF`, `SystemResponsiveness = 0`.
   - `[03] TCP No Delay (Nagle Algoritması)`: Iterates over all active adapter GUIDs in `HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces\{GUID}` and sets `TcpAckFrequency=1`, `TCPNoDelay=1`, `TcpDelAckTicks=0`.
   - `[04] RAM & DisablePagingExecutive`: Keeps kernel drivers in RAM (`DisablePagingExecutive=1`), `LargeSystemCache=0`.
   - `[05] CPU Ön Plan Önceliği (Win32PrioritySeparation)`: Sets quanta to `38` (decimal, 0x26) for 3:1 foreground game priority.
   - `[06] GPU Oyun Görev Önceliği (MMCSS)`: Boosts GPU priority in `SystemProfile\Tasks\Games` to `GPU Priority = 8`, `Priority = 6`, `Scheduling Category = High`.
   - `[07] USB Raw Input (Fare İvmesi Sıfırlama)`: Eliminates pointer acceleration (`MouseSpeed=0`, `MouseThreshold1=0`, `MouseThreshold2=0`) for 1:1 esports precision.
   - `[08] Telemetry, SysMain & Arama Servisleri`: Disables background disk-heavy services: `DiagTrack`, `SysMain` (Superfetch), `WSearch`.
   - `[09] FPS Drop Kayıt Kancaları (Xbox DVR)`: Completely removes background recording hooks in `GameConfigStore` and `GameDVR`.
   - `[10] Nihai Performans Modu (Ultimate Power)`: Unlocks and activates the hidden Windows Ultimate Performance scheme (`e9a42b02-d5df-448d-aa00-03f14749eb61`).

3. **Smart Cleaner (`cleaner_worker`)**:
   - Deep cleans User Temp (`%LOCALAPPDATA%\Temp`), Windows Temp (`C:\Windows\Temp`), Prefetch (`C:\Windows\Prefetch`), and Downloads installer residue safely while reporting freed disk space in MB.

4. **Web Landing Page (`index.html`)**:
   - Cyberpunk interactive showcase built with Tailwind CSS, neon glow effects, and interactive UI component cards.

---

## 🛠️ Build & Development Commands

```bash
# Run GUI directly
python NotLynxOptimizer_GUI.py

# Compile single-file executable with UAC Admin manifest
python -m PyInstaller --onefile --noconsole --uac-admin --icon=app.ico --name="NotLynxOptimizer_GUI" --clean NotLynxOptimizer_GUI.py

# Or run the one-click build script:
build.bat
```

---

## 🤖 Recommended Agency Agents Personas
When working on this repository, Claude should activate and leverage the following Agency personas from `~/.claude/agents/`:
- **`engineering-python-developer.md`**: For Python code enhancements, CustomTkinter widgets, and threading design.
- **`engineering-windows-internals-specialist.md`** / **`engineering-systems-programmer.md`**: For deep Windows registry, DPC latency, MMCSS, and timer resolutions.
- **`design-ui-designer.md`**: For enhancing the Cyberpunk neon dark aesthetic, contrast, and layout.
- **`testing-reality-checker.md`**: To verify that all registry paths, elevated commands, and rollback procedures are reliable and safe.
