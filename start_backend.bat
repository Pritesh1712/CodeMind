@echo off
echo ================================================
echo  CodeMind — Backend Startup
echo ================================================
echo.

:: Check if .env exists
if not exist ".env" (
    echo ERROR: .env file not found!
    echo Please copy .env.example to .env and add your GROQ_API_KEY
    echo.
    pause
    exit /b 1
)

:: Activate virtual environment
if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found!
    echo Please run: python -m venv venv ^&^& venv\Scripts\pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

echo Starting CodeMind backend on http://localhost:8000
echo API docs at http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop
echo.

uvicorn main:app --reload --port 8000

pause
