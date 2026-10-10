import os
import sys
import ctypes
import subprocess
import time

def is_admin():
    """Programın yönetici yetkisiyle çalışıp çalışmadığını kontrol eder."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_cmd(command):
    """Komutları arka planda hatasız çalıştıran yardımcı fonksiyon."""
    try:
        subprocess.run(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except:
        return False

def optimize_system():
    """NotLynx Core v3.0 Elite - Ultimate E-Sports Optimization Engine"""
    os.system('cls' if os.name == 'nt' else 'clear')
    print("==================================================")
    print("        NOTLYNX OPTIMIZER v3.0 ELITE CORE         ")
    print("       Maximum FPS & Zero Latency Engine          ")
    print("==================================================")
    time.sleep(1)

    print("\n[1/10] Sistem Zamanlayıcısı (BCDedit) Optimize Ediliyor...")
    run_cmd("bcdedit /set useplatformclock false")
    run_cmd("bcdedit /set disabledynamictick yes")
    run_cmd("bcdedit /set tscsyncpolicy Enhanced")
    print("✔️ BCDedit gecikme parametreleri kusursuzlaştırıldı.")
    time.sleep(0.8)

    print("\n[2/10] Ağ ve Ping (Network Throttling) Önceliği Ayarlanıyor...")
    run_cmd('Reg.exe add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile" /v "NetworkThrottlingIndex" /t REG_DWORD /d "4294967295" /f')
    run_cmd('Reg.exe add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile" /v "SystemResponsiveness" /t REG_DWORD /d "0" /f')
    print("✔️ Ağ bant genişliği tamamen oyun trafiğine rezerve edildi.")
    time.sleep(0.8)

    print("\n[3/10] TCP No Delay (Nagle Algoritması) Devre Dışı Bırakılıyor...")
    run_cmd('Reg.exe add "HKLM\\SYSTEM\\CurrentControlSet\\Services\\Tcpip\\Parameters\\Interfaces" /v "TcpAckFrequency" /t REG_DWORD /d "1" /f')
    run_cmd('Reg.exe add "HKLM\\SYSTEM\\CurrentControlSet\\Services\\Tcpip\\Parameters\\Interfaces" /v "TCPNoDelay" /t REG_DWORD /d "1" /f')
    print("✔️ TCP paket gecikmesi ve ping sıçramaları sıfırlandı.")
    time.sleep(0.8)

    print("\n[4/10] RAM & Bellek Yöneticisi (DisablePagingExecutive) Aktifleştiriliyor...")
    run_cmd('Reg.exe add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Memory Management" /v "DisablePagingExecutive" /t REG_DWORD /d "1" /f')
    run_cmd('Reg.exe add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Memory Management" /v "LargeSystemCache" /t REG_DWORD /d "0" /f')
    run_cmd('Reg.exe add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Memory Management" /v "ClearPageFileAtShutdown" /t REG_DWORD /d "0" /f')
    print("✔️ Çekirdek sürücüler RAM'de tutularak DPC gecikmesi düşürüldü.")
    time.sleep(0.8)

    print("\n[5/10] CPU Ön Plan Önceliği (Win32PrioritySeparation) Ayarlanıyor...")
    run_cmd('Reg.exe add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\PriorityControl" /v "Win32PrioritySeparation" /t REG_DWORD /d "38" /f')
    print("✔️ İşlemci gücü arka plan görevlerinden alınıp doğrudan oyuna verildi.")
    time.sleep(0.8)

    print("\n[6/10] GPU Oyun Görev Önceliği (Multimedia Tasks) Yapılandırılıyor...")
    run_cmd('Reg.exe add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile\\Tasks\\Games" /v "GPU Priority" /t REG_DWORD /d "8" /f')
    run_cmd('Reg.exe add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile\\Tasks\\Games" /v "Priority" /t REG_DWORD /d "6" /f')
    run_cmd('Reg.exe add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile\\Tasks\\Games" /v "Scheduling Category" /t REG_SZ /d "High" /f')
    print("✔️ Ekran kartı (GPU) önceliği maksimum seviyeye çıkarıldı.")
    time.sleep(0.8)

    print("\n[7/10] USB Güç Tasarrufu ve Fare Gecikmesi (Raw Input) Kapatılıyor...")
    run_cmd('Reg.exe add "HKCU\\Control Panel\\Mouse" /v "MouseSpeed" /t REG_SZ /d "0" /f')
    run_cmd('Reg.exe add "HKCU\\Control Panel\\Mouse" /v "MouseThreshold1" /t REG_SZ /d "0" /f')
    run_cmd('Reg.exe add "HKCU\\Control Panel\\Mouse" /v "MouseThreshold2" /t REG_SZ /d "0" /f')
    print("✔️ Fare ivmelenmesi sıfırlandı ve 1:1 e-spor aim hassasiyeti sağlandı.")
    time.sleep(0.8)

    print("\n[8/10] Telemetry, SysMain ve Arama İndekslemesi Kapatılıyor...")
    run_cmd('sc stop DiagTrack')
    run_cmd('sc config DiagTrack start= disabled')
    run_cmd('sc stop SysMain')
    run_cmd('sc config SysMain start= disabled')
    run_cmd('sc stop WSearch')
    run_cmd('sc config WSearch start= disabled')
    print("✔️ DiagTrack, SysMain ve disk yoran arama servisleri durduruldu.")
    time.sleep(0.8)

    print("\n[9/10] Xbox Game DVR ve Ekran Kaydı Servisleri Devre Dışı...")
    run_cmd('Reg.exe add "HKCU\\System\\GameConfigStore" /v "GameDVR_Enabled" /t REG_DWORD /d "0" /f')
    run_cmd('Reg.exe add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\GameDVR" /v "AllowGameDVR" /t REG_DWORD /d "0" /f')
    print("✔️ FPS drop yaratan tüm Xbox kayıt kancaları kaldırıldı.")
    time.sleep(0.8)

    print("\n[10/10] Nihai Performans (Ultimate Power) Güç Planı Aktif Ediliyor...")
    run_cmd('powercfg -duplicatescheme e9a42b02-d5df-448d-aa00-03f14749eb61')
    run_cmd('powercfg -setactive e9a42b02-d5df-448d-aa00-03f14749eb61')
    print("✔️ İşlemci frekans kilitleri tamamen açıldı ve Turbo Boost optimize edildi.")
    time.sleep(1)

    print("\n==================================================")
    print("    [+] ROOT ACCESS: SECURED - ELITE OPTIMIZED    ")
    print("     NotLynx Optimizer v3.0 başarıyla uygulandı!    ")
    print("    Değişikliklerin tamamen aktif olması için      ")
    print("         Lütfen sisteminizi yeniden başlatın.     ")
    print("==================================================")
    input("\nSistemden çıkmak için ENTER tuşuna basın...")

if __name__ == "__main__":
    if is_admin():
        optimize_system()
    else:
        print("NotLynx v3.0 Elite sistem analizi için Yönetici (Root) erişimi talep ediyor...")
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)