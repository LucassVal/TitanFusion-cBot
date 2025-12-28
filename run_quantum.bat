@echo off
title QUANTUM BRAIN - MULTI SYMBOL
color 0A
echo ===================================================
echo   TITAN FUSION QUANTUM - AI TRADING BRAIN
echo ===================================================
echo.
echo [1] Limpando cache Python...
del /S /Q *.pyc >nul 2>&1
rmdir /S /Q __pycache__ >nul 2>&1

echo [2] Iniciando Quantum Brain...
echo.
python quantum_brain.py
pause
