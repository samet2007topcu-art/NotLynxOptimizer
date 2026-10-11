# ⚡ NotLynx Optimizer v1.0

<p align="center">
  <img src="app.ico" alt="NotLynx Logo" width="128"/>
</p>

> **Elite Kernel & Windows Latency Optimization Engine**  
> *Engineered by NotLynx*

---

## 🚀 Proje Hakkında

**NotLynx Optimizer v1.0**, Windows 10/11 işletim sistemlerinde oyun içi **maksimum FPS**, **sıfır micro-stutter (takılma)** ve **en düşük sistem gecikmesini (input lag)** sağlamak üzere geliştirilmiş açık kaynaklı bir optimizasyon aracıdır.

---

## 🛠️ Entegre 10 Kernel Modülü

1. **Sistem Zamanlayıcısı (BCDedit):** HPET kapatılır, Dynamic Tick devre dışı bırakılır.
2. **Network Throttling Bypass:** Ağ bant genişliği tamamen oyun trafiğine rezerve edilir.
3. **TCP No Delay (Nagle Algoritması):** TCP paket gecikmesi ve ping sıçramaları sıfırlanır.
4. **RAM & Bellek Yöneticisi:** `DisablePagingExecutive` aktif edilerek DPC latency düşürülür.
5. **CPU Scheduler:** `Win32PrioritySeparation` ayarı ile işlemci önceliği oyuna verilir.
6. **GPU MMCSS Önceliği:** Ekran kartı görev önceliği maksimum seviyeye çıkarılır.
7. **USB Raw Input & Güç:** USB güç tasarrufu kapatılır, 1:1 e-spor fare tepkiselliği sağlanır.
8. **Telemetry & Services Shield:** DiagTrack, SysMain ve arama servisleri durdurulur.
9. **Xbox Game DVR Shield:** FPS drop yaratan arka plan kayıt kancaları kaldırılır.
10. **Ultimate Power Plan:** İşlemci frekans kilitleri açılır ve Turbo Boost optimize edilir.

---

## 💻 Kurulum & Kullanım

1. Güncel `NotlynxOptimizer.exe` dosyasını indirin.
2. Dosyaya sağ tıklayıp **Yönetici Olarak Çalıştır** (Run as Administrator) seçeneğini tıklayın.
3. Optimizasyon tamamlandıktan sonra değişikliklerin aktif olması için **bilgisayarınızı yeniden başlatın**.

---

## 📝 Kaynaktan Derleme (Build from Source)

```bash
git clone https://github.com/samet2007topcu-art/NotLynxOptimizer.git
cd NotLynxOptimizer
pip install Pillow PyInstaller
python make_icon.py
python -m PyInstaller --onefile --uac-admin --icon=app.ico NotLynxOptimizer.py
```
## 🔗 Sosyal Medya & İletişim
-**TikTok**: @notlynx_7

-**Instagram**: @notlynx7

© 2026 NotLynx Team. All rights reserved.
