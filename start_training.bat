@echo off
chcp 65001 >nul

cd /d "%~dp0"

echo ===================================================
echo 🧠 IDTG Projekt - AI Modell Tanitas
echo ===================================================
echo.

if not exist "venv\Scripts\activate.bat" (
    echo ❌ Hiba: Nem talalhato a virtualis kornyezet.
    pause
    exit /b
)

echo 🔄 Virtualis kornyezet aktivalasa...
call venv\Scripts\activate.bat

echo 🚀 Tanito szkript inditasa...
echo ---------------------------------------------------
python train_qg_eval.py
echo ---------------------------------------------------

echo.
echo ✅ A tanitas befejezodott.
pause