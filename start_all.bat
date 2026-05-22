@echo off
cd /d "%~dp0"

if not exist ".env" (
  copy ".env.example" ".env" >nul
)

start "HRIS Backend" cmd /k ""%~dp0start_backend.bat""
timeout /t 3 /nobreak >nul
start "HRIS Frontend" cmd /k ""%~dp0start_frontend.bat""

echo HRIS local servers are starting.
echo Backend:  http://127.0.0.1:5000
echo Frontend: http://localhost:5173
pause
