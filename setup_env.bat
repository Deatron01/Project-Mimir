@echo off
:: Beallitjuk a terminal kodolasat UTF-8-ra az emojikhoz!
chcp 65001 >nul
:: Kényszerített projekt mappa
cd /d "%~dp0"
echo ===================================================
echo 🚀 IDTG Projekt - AI Kornyezet Telepito
echo ===================================================
echo.

:: 1. Virtualis kornyezet letrehozasa
echo [1/4] 📦 Virtualis kornyezet (venv) letrehozasa...
python -m venv venv
if %errorlevel% neq 0 (
    echo ❌ Hiba a venv letrehozasakor! Ellenorizd, hogy a Python telepitve van-e.
    pause
    exit /b %errorlevel%
)

:: 2. Kornyezet aktivalasa es pip frissitese
echo [2/4] 🔄 Pip frissitese...
call venv\Scripts\activate
python -m pip install --upgrade pip >nul

:: 3. GPU-s PyTorch telepitese (Ez a legfontosabb a 3070 Ti es 3090 kartyakhoz!)
echo [3/4] ⚙️ GPU-s PyTorch (CUDA 12.1) telepitese... (Ez eltarthat egy darabig)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

:: 4. Tobbi csomag telepitese a requirements.txt-bol
echo [4/4] 📚 Tovabbi fuggosegek telepitese a requirements.txt alapjan...
pip install -r requirements.txt

echo.
echo ===================================================
echo 🎉 TELEPITES SIKERESEN BEFEJEZODOTT!
echo ===================================================
echo A kornyezet aktivalasahoz ird be a terminalba:
echo venv\Scripts\activate
echo.
pause