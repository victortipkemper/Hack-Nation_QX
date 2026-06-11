@echo off
cd /d "%~dp0"
echo.
echo  PUSH Autocomply -> GitHub (ersetzt Remote-Inhalt)
echo  =================================================
echo.

git add -A
git status --short

git commit -m "Replace repo with golden-calibrated Autocomply checklist engine." -m "Deterministic PDF analysis, white-box checklist, upload UI, calibrated against Hackathon Loesungsschluessel."

if errorlevel 1 (
    echo.
    echo  Nichts zu committen oder Commit fehlgeschlagen.
    echo  Pruefe ob Aenderungen vorhanden sind.
    pause
    exit /b 1
)

echo.
echo  Force-Push nach origin main ...
git push --force origin main

if errorlevel 1 (
    echo.
    echo  PUSH FEHLGESCHLAGEN - gh login oder Git-Credentials pruefen.
    pause
    exit /b 1
)

echo.
echo  FERTIG: https://github.com/victortipkemper/Hack-Nation_QX
echo.
pause
