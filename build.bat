@echo off
chcp 65001 > nul
title NotLynx Optimizer - PyInstaller Derleme Aracı
color 0A

echo ====================================================
echo      NOTLYNX OPTIMIZER v1.0 ELITE - DERLEME ARACI
echo ====================================================
echo.

set PYTHON_EXE=C:\Users\Samet\AppData\Local\Programs\Python\Python310\python.exe

if not exist "%PYTHON_EXE%" (
    set PYTHON_EXE=python
)

echo [*] Gerekli Python kütüphaneleri kontrol ediliyor...
"%PYTHON_EXE%" -m pip install -r requirements.txt

echo.
echo [*] NotLynxOptimizer_GUI.exe derleniyor (UAC Admin, Varlıklar ve Tek Dosya)...
"%PYTHON_EXE%" -m PyInstaller --onefile --noconsole --uac-admin --icon=app.ico --add-data "app.ico;." --add-data "logo.png;." --name="NotLynxOptimizer_GUI" --clean NotLynxOptimizer_GUI.py

echo.
if exist "dist\NotLynxOptimizer_GUI.exe" (
    echo ====================================================
    echo [SUCCESS] Derleme başarıyla tamamlandı!
    echo Çalıştırılabilir dosya: dist\NotLynxOptimizer_GUI.exe
    echo ====================================================
    copy /Y "dist\NotLynxOptimizer_GUI.exe" "C:\Users\Samet\Downloads\NotLynxOptimizer_GUI.exe" > nul
    echo [OK] Güncel .exe doğrudan İndirilenler klasörünüze kopyalandı!
) else (
    echo [ERROR] Derleme sırasında hata oluştu.
)
pause
