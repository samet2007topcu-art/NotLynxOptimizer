@echo off
setlocal
title NotLynx Optimizer - Derleme
cd /d "%~dp0"

echo.
echo [1/4] Gerekli dosyalar kontrol ediliyor...
for %%F in (NotLynxOptimizer_GUI.py NotLynxOptimizer_GUI.spec requirements.txt logo.png app.ico) do (
    if not exist "%%F" (
        echo HATA: %%F bulunamadi. build.bat dosyasini proje klasorunden calistirin.
        goto :fail
    )
)

echo [2/4] Python ve paketler kontrol ediliyor...
set "PY_CMD=python"
if exist "%LOCALAPPDATA%\Programs\Python\Python310\python.exe" (
    set "PY_CMD=%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
)
%PY_CMD% --version >nul 2>&1
if errorlevel 1 (
    echo HATA: Python bulunamadi. python.org adresinden kurup "Add to PATH" secenegini isaretleyin.
    goto :fail
)
%PY_CMD% -m pip install -r requirements.txt --quiet --disable-pip-version-check
if errorlevel 1 goto :fail

echo [3/4] Derleniyor (PyInstaller) - bu islem 1-2 dakika surebilir...
%PY_CMD% -m PyInstaller --clean --noconfirm NotLynxOptimizer_GUI.spec
if errorlevel 1 goto :fail

echo [4/4] Sonuc kontrol ediliyor...
if not exist "dist\NotLynxOptimizer_GUI.exe" (
    echo HATA: dist\NotLynxOptimizer_GUI.exe uretilemedi.
    goto :fail
)

echo.
echo TAMAM: dist\NotLynxOptimizer_GUI.exe
for %%A in ("dist\NotLynxOptimizer_GUI.exe") do echo Boyut: %%~zA bayt
certutil -hashfile "dist\NotLynxOptimizer_GUI.exe" SHA256
echo.
echo GitHub Release'e yuklenecek dosya budur. Dosya adini DEGISTIRMEYIN:
echo siteteki indirme baglantisi tam olarak bu adi bekler.
echo.
pause
exit /b 0

:fail
echo.
echo Derleme basarisiz oldu. Yukaridaki hata mesajini kontrol edin.
echo.
pause
exit /b 1
