@echo off
setlocal
cd /d "%~dp0"

if not exist ".env" (
  echo [frontend] Creating .env from .env.example...
  copy ".env.example" ".env" >nul
)

if not exist "node_modules" (
  echo [frontend] Installing npm dependencies...
  npm install
  if errorlevel 1 goto :error
)

echo [frontend] Starting Vite frontend at http://localhost:5173 ...
npm run dev -- --host localhost --port 5173 --strictPort
goto :eof

:error
echo.
echo [frontend] Failed. Check that Node.js and npm are installed.
pause
exit /b 1
