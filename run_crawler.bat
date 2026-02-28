@echo off
REM Supermarket Price Crawler - Windows Batch Runner
REM This script provides easy command-line access to the crawler

cd /d "%~dp0"

echo ========================================
echo Supermarket Price Crawler
echo ========================================
echo.

REM Check if Python script exists
if exist "Supermarket Price Crawler.py" (
    echo Running Python script...
    python "Supermarket Price Crawler.py" %*
    goto :end
)

REM Check if executable exists in subdirectory
if exist "Supermarket Price Crawler\Supermarket Price Crawler.exe" (
    echo Running executable...
    cd "Supermarket Price Crawler"
    "Supermarket Price Crawler.exe" %*
    goto :end
)

REM Check if executable exists in current directory
if exist "Supermarket Price Crawler.exe" (
    echo Running executable...
    "Supermarket Price Crawler.exe" %*
    goto :end
)

REM Try wrapper script
if exist "run_crawler.py" (
    echo Running wrapper script...
    python run_crawler.py %*
    goto :end
)

echo Error: Cannot find crawler script or executable
echo Please ensure one of the following exists:
echo   - Supermarket Price Crawler.py
echo   - Supermarket Price Crawler\Supermarket Price Crawler.exe
echo   - Supermarket Price Crawler.exe
echo   - run_crawler.py
pause
exit /b 1

:end
if errorlevel 1 (
    echo.
    echo ========================================
    echo Error occurred during execution
    echo Check FIX_INSTRUCTIONS.md for troubleshooting
    echo ========================================
    pause
)
exit /b %errorlevel%






