@echo off
title Vyoma Offline Medical AI Assistant - Laptop Mode
echo ========================================================================
echo    Vyoma Offline Medical AI Assistant - Laptop Testing Mode
echo ========================================================================
echo Running in Windowed Mode (1024x600 Waveshare emulation)...
echo 100%% Offline - Zero runtime cloud calls
echo.

set FULLSCREEN=false
set UI_WIDTH=1024
set UI_HEIGHT=600
set DEBUG=true

python main.py
pause
