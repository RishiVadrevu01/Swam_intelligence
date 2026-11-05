@echo off
title Emergency Corridor Coordination Platform Launcher
echo Launching Emergency Corridor Backend and Frontend...
start "Emergency Corridor Backend" cmd /c "%~dp0run_backend.bat"
start "Emergency Corridor Frontend" cmd /c "%~dp0run_frontend.bat"
echo.
echo ========================================================
echo Backend will be available at: http://127.0.0.1:8000
echo Swagger API docs at:         http://127.0.0.1:8000/docs
echo Frontend Dashboard at:       http://localhost:5173
echo ========================================================
echo.
pause

