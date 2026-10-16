# ⚡ NotLynx Optimizer v2.5 Elite Cyberpunk Suite

<p align="center">
  <img src="logo.png" alt="NotLynx Optimizer Logo" width="480"/>
</p>

<p align="center">
  <strong>Elite Kernel, Windows Latency Engine & Esports Performance Suite</strong><br>
  <em>Engineered by NotLynx</em>
</p>

<p align="center">
  <a href="https://github.com/samet2007topcu-art/NotLynxOptimizer/releases"><img src="https://img.shields.io/badge/Release-v2.5%20Elite-00ff66.svg?style=for-the-badge&logo=windows" alt="Release"/></a>
  <img src="https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-blue.svg?style=for-the-badge&logo=windows" alt="Platform"/>
  <img src="https://img.shields.io/badge/Python-3.10+-yellow.svg?style=for-the-badge&logo=python" alt="Python"/>
  <img src="https://img.shields.io/badge/UI-CustomTkinter%20Cyberpunk-purple.svg?style=for-the-badge" alt="UI"/>
  <img src="https://img.shields.io/badge/License-MIT-red.svg?style=for-the-badge" alt="License"/>
</p>

---

## 🚀 Proje Hakkında

**NotLynx Optimizer v2.5**, rekabetçi e-spor oyuncuları ve performans tutkunları için geliştirilmiş açık kaynaklı bir Windows çekirdek ve sistem optimizasyon merkezidir. 

Standart optimizasyon araçlarından farklı olarak **NotLynx Optimizer**, sistem kaynaklarını tüketen arka plan kancalarını doğrudan çekirdek seviyesinde yönetir, Görev Yöneticisi işlem sayısını 230+'lardan 130 seviyelerine indirir ve ekran kartı kesme gecikmelerini (MSI Mode) e-spor standartlarına taşır.

---

## ✨ Öne Çıkan Özellikler

### 1. ⚡ 10 Çekirdekli Kernel & Gecikme Motoru
1. **Sistem Zamanlayıcısı (BCDedit):** HPET kapatılır, Dynamic Tick devre dışı bırakılır, TSC senkronizasyonu (`Enhanced`) açılır.
2. **Network Throttling Bypass:** Ağ bant genişliği kısıtlaması kaldırılır, sistem tepkiselliği %100'e kilitlenir.
3. **TCP No Delay (Nagle Bypass):** Sistemdeki tüm aktif ağ kartı GUID'leri tek tek taranarak TCP paket gecikmesi ve ping sıçramaları sıfırlanır.
4. **RAM & DisablePagingExecutive:** Çekirdek sürücüler fiziksel RAM'de kilitlenerek disk sayfalama gecikmesi (DPC Latency) sıfırlanır.
5. **CPU Ön Plan Önceliği:** `Win32PrioritySeparation = 38` (Short Quanta, 3:1 Boost) ile işlemci çevrimleri doğrudan oyuna verilir.
6. **GPU MMCSS Önceliği:** Ekran kartı görev önceliği maksimum seviyeye (`GPU Priority: 8, Scheduling: High`) çıkarılır.
7. **USB Raw Input:** Fare ivmelenmesi sıfırlanır, 1:1 e-spor aim hassasiyeti sağlanır.
8. **Telemetry & SysMain Shield:** DiagTrack, SysMain (Superfetch) ve diski yoran Windows Search servisleri kapatılır.
9. **Xbox Game DVR Shield:** Arka planda FPS drop yaratan tüm ekran kayıt ve GameBar kancaları kaldırılır.
10. **NotLynx Optimizer Güç Planı:** Windows Denetim Masasında doğrudan **"NotLynx Optimizer - Ultimate Power"** adıyla özel güç profili aktif edilir.

---

### 2. 🎮 GPU & E-Spor İnce Ayarları
* **GPU MSI (Message Signaled Interrupts) Modu:** Ekran kartını eski IRQ çakışmalarından kurtarıp MSI moduna alır ve `DevicePriority = High` yaparak %1 Low FPS dalgalanmalarını önler.
* **HAGS (Hardware-Accelerated GPU Scheduling):** Donanım hızlandırmalı GPU zamanlamasını tek tıkla aktif eder.
* **DirectX & Shader Cache Temizleyici:** Bozuk veya birikmiş NVIDIA/AMD/DirectX shader önbelleğini sıfırlayarak harita yüklemelerindeki ani takılmaları çözer.
* **MSI Afterburner Entegrasyonu:** Kurulu MSI Afterburner'ı otomatik algılar ve hız aşırtma (overclock) için tek tıkla başlatır.

---

### 3. 📉 İşlemci İşlem Sayısı Düşürücü (Process Reducer)
* Görev Yöneticisinde 230+'dan fazla çalışan gereksiz Windows telemetri, tanılama, hata raporlama ve indeksleme hizmetlerini (`DiagTrack`, `dmwappushservice`, `SysMain`, `WSearch`, `PcaSvc`, `WerSvc`, `Spooler`, `MapsBroker` vb.) durdurur.
* Canlı telemetri paneli ile anlık işlem sayısını gösterir.

---

### 4. 🛠️ Masaüstü & Windows İnce Ayarları
* **Masaüstü Simgelerindeki Kısayol Okunu Kaldırma:** Masaüstündeki tüm uygulama simgelerinin üzerindeki mavi/beyaz kısayol okunu tek tıkla kaldırır ve dilediğinizde geri yükler.
* **Hızlı Menüler:** Windows sağ tık ve Başlat menüsü açılışındaki 400ms animasyon gecikmesini 0ms yapar.
* **Dosya Uzantılarını Gösterme:** Tüm dosya uzantılarını görünür kılar.

---

### 5. 🧹 Akıllı & Derin Sistem Temizleyici
* **User Temp (`%LOCALAPPDATA%\Temp`)**
* **Windows Temp (`C:\Windows\Temp`)**
* **Windows Prefetch Önbelleği (`C:\Windows\Prefetch`)**
* **Crash Dump & WER Raporları**
* **İndirilenler klasöründeki gereksiz kalıntı kurulum dosyaları**
* Temizlenen dosya sayısını ve kazanılan disk alanını (MB/GB) anlık canlı konsola yansıtır.

---

### 6. 🛡️ Güvenlik Kalkanı & Geri Alınabilirlik
* **Sistem Geri Yükleme Noktası:** Tek tıkla `Checkpoint-Computer` çağrısı yaparak değişiklik öncesi geri yükleme noktası oluşturur.
* **Varsayılana Dönüş:** İstenildiği an tüm 10 modülü ve sistem ayarlarını fabrika varsayılanlarına sıfırlayan geri alma mekanizması sunar.

---

## 📊 Performans Kıyaslaması (Benchmarks)

| Parametre | Standart Windows 10/11 | NotLynx Optimizer v2.5 Sonrası |
| :--- | :---: | :---: |
| **Arka Plan İşlem Sayısı** | ~230 - 250 İşlem | **~120 - 140 İşlem** |
| **DPC Gecikmesi (LatencyMon)** | 850 µs - 1200 µs | **< 150 µs** |
| **%1 Low FPS Stabilitesi** | Dalgalı (Micro-stutter) | **Ultra Kararlı** |
| **Ağ Paket Gecikmesi** | Nagle Gecikmeli | **0ms Anlık İletim** |
| **GPU Kesme Önceliği** | Normal IRQ (Paylaşımlı) | **MSI Mode (High Priority)** |

---

## 💻 Kurulum & Kullanım

1. [Releases](https://github.com/samet2007topcu-art/NotLynxOptimizer/releases) sayfasından en güncel `NotLynxOptimizer_GUI.exe` dosyasını indirin.
2. Dosyayı çalıştırın (UAC Yönetici İzni otomatik istenir).
3. İstediğiniz modülleri ve ayarları seçip **UYGULA** butonuna tıklayın.
4. Ayarların tam performansla devreye girmesi için bilgisayarınızı **yeniden başlatın**.

---

## 📝 Kaynaktan Derleme (Build from Source)

```bash
git clone https://github.com/samet2007topcu-art/NotLynxOptimizer.git
cd NotLynxOptimizer
pip install -r requirements.txt
python -m PyInstaller --onefile --noconsole --uac-admin --icon=app.ico --name="NotLynxOptimizer_GUI" --clean NotLynxOptimizer_GUI.py
```
*Veya doğrudan `build.bat` dosyasını çalıştırarak tek tıkla derleyebilirsiniz.*

---

## 🔗 Sosyal Medya & İletişim

* **TikTok:** [@notlynx_7](https://www.tiktok.com/@notlynx_7)
* **Instagram:** [@notlynx7](https://www.instagram.com/notlynx7)
* **GitHub:** [samet2007topcu-art/NotLynxOptimizer](https://github.com/samet2007topcu-art/NotLynxOptimizer)

© 2026 NotLynx Team. All rights reserved.
