@echo off
echo ================================================
echo  CodeMind — Frontend Startup
echo ================================================
echo.

:: Check if node_modules exists
if not exist "node_modules" (
    echo Installing dependencies...
    npm install
)

echo Starting CodeMind frontend on http://localhost:5173
echo.
echo Press Ctrl+C to stop
echo.

npm run dev

pause
