@echo off
chcp 65001 >nul

cd /d "%~dp0"

echo ===================================================
echo 🧪 IDTG Projekt - Legujabb Modell Tesztelese
echo ===================================================
echo.

if not exist "venv\Scripts\activate.bat" (
    echo ❌ Hiba: Nem talalhato a virtualis kornyezet.
    pause
    exit /b
)

echo 🔄 Virtualis kornyezet aktivalasa...
call venv\Scripts\activate.bat

echo 🔎 Tesztelo szkript inditasa...
echo ---------------------------------------------------
python test_model.py
echo ---------------------------------------------------

echo.
echo ✅ A program befejezte a futast.
pause