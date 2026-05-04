@echo off
setlocal
cd /d "%~dp0"

REM ---- 1) Opprett virtuelt miljø første gang ----
if not exist ".venv\Scripts\python.exe" (
    echo Oppretter virtuelt miljoe ^(.venv^) ...
    py -3 -m venv .venv 2>nul
    if errorlevel 1 python -m venv .venv
    if errorlevel 1 (
        echo.
        echo FEIL: Klarte ikke aa opprette virtuelt miljoe.
        echo Sjekk at Python 3 er installert ^(py --version^).
        pause
        exit /b 1
    )
)

REM ---- 2) Installer / oppdater avhengigheter ----
echo Sjekker avhengigheter...
".venv\Scripts\python.exe" -m pip install --quiet --disable-pip-version-check -r requirements.txt
if errorlevel 1 (
    echo.
    echo FEIL: pip install feilet.
    pause
    exit /b 1
)

REM ---- 3) Aapne nettleser etter ca. 2 sek ^(naar serveren er klar^) ----
start "" /min cmd /c "timeout /t 2 /nobreak > nul & start http://127.0.0.1:5000"

REM ---- 4) Start serveren ^(denne blokkerer; CTRL+C for aa stoppe^) ----
echo.
echo ============================================================
echo  Treningsplanleggern starter...
echo  Nettleseren aapnes automatisk paa http://127.0.0.1:5000
echo  Stopp med CTRL+C
echo ============================================================
echo.
".venv\Scripts\python.exe" app.py

pause
