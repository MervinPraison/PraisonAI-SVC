@echo off
REM Setup Script for API Contract Generator Service (Windows)

echo ======================================
echo API Contract Generator - Setup
echo ======================================
echo.

REM Check Python version
echo 1. Checking Python version...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed
    exit /b 1
)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo OK: Python %PYTHON_VERSION% found
echo.

REM Install dependencies
echo 2. Installing dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies
    exit /b 1
)
echo OK: Dependencies installed
echo.

REM Check if .env exists
echo 3. Checking environment configuration...
if not exist .env (
    if exist .env.local (
        echo Copying .env.local to .env...
        copy .env.local .env >nul
        echo OK: Environment file created
    ) else (
        echo Creating default .env file...
        (
            echo PRAISONAI_AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;QueueEndpoint=http://127.0.0.1:10001/devstoreaccount1;TableEndpoint=http://127.0.0.1:10002/devstoreaccount1;
        ) > .env
        echo OK: Default environment file created
    )
) else (
    echo OK: Environment file exists
)
echo.

echo ======================================
echo Setup Complete!
echo ======================================
echo.
echo Next steps:
echo.
echo 1. Start Azurite (in a separate terminal^):
echo    azurite --silent
echo.
echo 2. Run the service:
echo    python app.py
echo.
echo 3. Test the service:
echo    python quick-test.py
echo.
pause

