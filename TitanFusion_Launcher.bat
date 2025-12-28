@echo off
chcp 65001 >nul
title TITAN FUSION QUANTUM v1.3.1 (ANTIGRAVITY ENGINE)
color 0A
cls
echo =======================================================
echo    TITAN FUSION QUANTUM - ANTIGRAVITY ENGINE v3.0
echo                   Version 1.3.1
echo =======================================================
echo.
echo  [1] Verifying system integrity...
if exist "quantum_brain.py" (
    echo  [OK] Brain detected.
) else (
    echo  [ERROR] quantum_brain.py not found!
    pause
    exit
)

echo.
echo  [2] Checking/Installing requirements...
pip install -r requirements.txt -q --disable-pip-version-check
if %ERRORLEVEL% EQU 0 (
    echo  [OK] Dependencies ready.
) else (
    echo  [WARN] Some dependencies may be missing. Continuing...
)

echo.
echo  Choose mode:
echo  [1] Start Trading Engine (quantum_brain.py)
echo  [2] Validate Signals (signal_validator.py)
echo  [3] Start Both (Engine + Auto-Validate)
echo.
set /p mode="Enter choice (1/2/3): "

if "%mode%"=="1" goto engine
if "%mode%"=="2" goto validator
if "%mode%"=="3" goto both
goto engine

:engine
echo.
echo  [3] Starting Antigravity Engine...
echo  [AI Throttle: 1 call per minute]
echo.
python quantum_brain.py
pause
exit

:validator
echo.
echo  [3] Running Signal Validator...
echo.
python signal_validator.py
pause
exit

:both
echo.
echo  [3] Starting Antigravity Engine in background...
start "Titan Quantum" cmd /c python quantum_brain.py
echo  [4] Running Signal Validator...
echo.
timeout /t 5 >nul
python signal_validator.py
pause
exit
