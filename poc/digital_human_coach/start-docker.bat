@echo off
REM Quick start script for Digital Human App with Docker (Windows)

echo ================================================
echo Digital Human App - Docker Quick Start
echo ================================================
echo.

REM Check if Docker is installed
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker is not installed. Please install Docker Desktop first.
    echo Download: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

REM Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker is not running. Please start Docker Desktop.
    pause
    exit /b 1
)

echo OK: Docker is installed and running
echo.

REM Check if .env file exists
if not exist .env (
    echo WARNING: .env file not found. Creating from .env.example...
    copy .env.example .env
    echo OK: .env file created. Please edit it with your API keys.
    echo.
    echo Required steps:
    echo    1. Open .env file in a text editor
    echo    2. Add your API keys (OPENAI_API_KEY, etc.)
    echo    3. Run this script again
    echo.
    pause
    exit /b 0
)

echo OK: .env file found
echo.

REM Menu
echo Choose an action:
echo 1) Start services (first time / rebuild)
echo 2) Start services (quick start)
echo 3) Stop services
echo 4) View logs
echo 5) Restart services
echo 6) Clean up everything
echo.
set /p choice="Enter choice [1-6]: "

if "%choice%"=="1" goto build
if "%choice%"=="2" goto start
if "%choice%"=="3" goto stop
if "%choice%"=="4" goto logs
if "%choice%"=="5" goto restart
if "%choice%"=="6" goto cleanup
goto invalid

:build
echo.
echo Building and starting services...
docker-compose up --build -d
goto status

:start
echo.
echo Starting services...
docker-compose up -d
goto status

:stop
echo.
echo Stopping services...
docker-compose down
goto end

:logs
echo.
echo Viewing logs (Ctrl+C to exit)...
docker-compose logs -f
goto end

:restart
echo.
echo Restarting services...
docker-compose restart
goto status

:cleanup
echo.
set /p confirm="WARNING: This will remove all containers, volumes, and data. Continue? [y/N]: "
if /i "%confirm%"=="y" (
    echo Cleaning up...
    docker-compose down -v --rmi all
    echo OK: Cleanup complete
) else (
    echo Cancelled
)
goto end

:invalid
echo ERROR: Invalid choice
pause
exit /b 1

:status
echo.
echo Waiting for services to be ready...
timeout /t 5 /nobreak >nul

echo.
echo ================================================
echo Services Status:
echo ================================================
docker-compose ps

echo.
echo ================================================
echo Access Points:
echo ================================================
echo    Frontend UI:  http://localhost:8501
echo    Backend API:  http://localhost:8000
echo    API Docs:     http://localhost:8000/docs
echo.
echo    View logs:     docker-compose logs -f
echo    Stop services: docker-compose down
echo ================================================
echo.

:end
pause
