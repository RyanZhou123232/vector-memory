@echo off
set PYTHONUTF8=1
"%~dp0.venv\Scripts\python.exe" "%~dp0app.py"
if errorlevel 1 pause
