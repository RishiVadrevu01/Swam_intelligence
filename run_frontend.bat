@echo off
title Emergency Corridor Frontend Dashboard
cd /d "%~dp0frontend"
echo Starting React Vite Dashboard on http://localhost:5173 ...
call npm.cmd run dev
pause

