@echo off
chcp 65001
title TITAN FUSION QUANTUM v1.0.0 (ANTIGRAVITY ENGINE)
color 0A
cls
echo =======================================================
echo    TITAN FUSION QUANTUM - ANTIGRAVITY ENGINE v3.0
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
echo  [2] Starting Antigravity Engine...
echo.
python quantum_brain.py
pause
