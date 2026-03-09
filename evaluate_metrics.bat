@echo off
chcp 65001 >nul
:: Kényszerített projekt mappa
cd /d "%~dp0"
echo ===================================================
echo 📈 IDTG Projekt - Eredmenyek Kiertekelese
echo ===================================================
echo.

if not exist "venv\Scripts\activate.bat" (
    echo ❌ Hiba: Nem talalhato a virtualis kornyezet!
    pause
    exit /b
)

call venv\Scripts\activate

echo 📊 Kiertekelo szkript inditasa...
echo ---------------------------------------------------
python evaluate_metrics.py
echo ---------------------------------------------------

echo.
echo ✅ Diagramok es statisztikak legeneralva!
pause