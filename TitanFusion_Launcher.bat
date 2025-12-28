@echo off
chcp 65001
title TITAN FUSION QUANTUM v1.0.0 (ANTIGRAVITY ENGINE)
color 0A
cls
echo =======================================================
echo    TITAN FUSION QUANTUM - ANTIGRAVITY ENGINE v3.0
echo =======================================================
echo.
echo  [1] Verificando integridade do sistema...
if exist "quantum_brain.py" (
    echo  [OK] Cérebro detectado.
) else (
    echo  [ERRO] quantum_brain.py não encontrado!
    pause
    exit
)
echo.
echo  [2] Iniciando Antigravity Engine...
echo.
python quantum_brain.py
pause
