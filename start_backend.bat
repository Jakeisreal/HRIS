@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo [backend] Creating Python virtual environment...
  python -m venv .venv
  if errorlevel 1 goto :error
)

echo [backend] Installing Python dependencies...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto :error

if "%HRIS_CORS_ORIGIN%"=="" set HRIS_CORS_ORIGIN=http://localhost:5173

echo [backend] Starting Flask API at http://127.0.0.1:5000
".venv\Scripts\python.exe" -m backend.app
goto :eof

:error
echo.
echo [backend] Failed. Check that Python is installed and available as "python".
pause
exit /b 1
