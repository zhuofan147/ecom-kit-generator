@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if %errorlevel%==0 (
  py start_lan.py
) else (
  python start_lan.py
)
