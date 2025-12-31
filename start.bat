@echo off
REM ====================================================================
REM POP3 to Gmail Importer - Windows Startup Script
REM Automatically sets up virtual environment and starts the importer
REM ====================================================================

setlocal enabledelayedexpansion

echo ====================================================================
echo POP3 to Gmail Importer - Starting...
echo ====================================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.9 or higher from https://www.python.org/
    pause
    exit /b 1
)

REM Get Python version and check if it's 3.9 or higher
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Found Python version: %PYTHON_VERSION%

REM Extract major and minor version numbers
for /f "tokens=1,2 delims=." %%a in ("%PYTHON_VERSION%") do (
    set PYTHON_MAJOR=%%a
    set PYTHON_MINOR=%%b
)

REM Check version requirement (Python 3.9+)
if %PYTHON_MAJOR% lss 3 (
    echo ERROR: Python 3.9 or higher is required
    echo Current version: %PYTHON_VERSION%
    pause
    exit /b 1
)
if %PYTHON_MAJOR% equ 3 if %PYTHON_MINOR% lss 9 (
    echo ERROR: Python 3.9 or higher is required
    echo Current version: %PYTHON_VERSION%
    pause
    exit /b 1
)
echo [OK] Python version check passed
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo Virtual environment not found. Creating...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created
    echo.
) else (
    echo [OK] Virtual environment found
    echo.
)

REM Activate virtual environment
echo Activating virtual environment...
if not exist "venv\Scripts\activate.bat" (
    echo ERROR: venv\Scripts\activate.bat not found
    echo The virtual environment may be corrupted. Please delete the 'venv' folder and try again.
    pause
    exit /b 1
)
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)
echo [OK] Virtual environment activated
echo.

REM Install/update dependencies
echo Installing dependencies from requirements.txt...
pip install -r requirements.txt --quiet
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo [OK] Dependencies installed
echo.

REM Check if .env file exists
if not exist ".env" (
    echo ERROR: .env file not found!
    echo.
    echo Please create a .env file based on .env.example:
    echo   1. Copy .env.example to .env
    echo   2. Edit .env with your email account settings
    echo.
    pause
    exit /b 1
)
echo [OK] .env file found
echo.

REM Run connection test first
echo ====================================================================
echo Running connection test...
echo ====================================================================
echo.
python test_connection.py
if %errorlevel% neq 0 (
    echo.
    echo WARNING: Connection test failed or has warnings
    echo Please review the errors above before running the forwarder
    echo.
    echo Press any key to continue anyway, or Ctrl+C to cancel...
    pause >nul
)

REM Start main program
echo.
echo ====================================================================
echo Starting POP3 to Gmail Importer...
echo ====================================================================
echo.
echo To stop the program, press Ctrl+C
echo.

python main.py

REM Handle exit
echo.
echo ====================================================================
echo POP3 to Gmail Importer stopped
echo ====================================================================
pause
