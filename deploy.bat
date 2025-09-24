@echo off
setlocal enabledelayedexpansion

REM AI Voice Chatbot - Docker Deployment Script for Windows
REM This script helps you deploy the voice chatbot using Docker on Windows

set APP_NAME=voice-chatbot
set PORT=8501
set COMPOSE_FILE=docker-compose.yml

echo === AI Voice Chatbot - Docker Deployment (Browser Audio) ===
echo [INFO] This version uses browser-based audio for full Docker compatibility
echo.

REM Get command (default to start)
set COMMAND=%1
if "%COMMAND%"=="" set COMMAND=start

goto %COMMAND% 2>nul || goto unknown_command

:start
    echo [INFO] Starting deployment process...
    call :check_docker
    call :check_docker_compose
    call :check_env_file
    call :build_image
    call :start_app
    goto end

:stop
    echo [INFO] Stopping application...
    call :check_docker_compose
    call :stop_app
    goto end

:restart
    echo [INFO] Restarting application...
    call :check_docker_compose
    call :stop_app
    call :start_app
    goto end

:status
    echo [INFO] Checking application status...
    call :check_docker_compose
    call :show_status
    goto end

:logs
    echo [INFO] Showing application logs...
    call :check_docker_compose
    call :show_logs
    goto end

:update
    echo [INFO] Updating application...
    call :check_docker
    call :check_docker_compose
    call :update_app
    goto end

:build
    echo [INFO] Building Docker image...
    call :check_docker
    call :check_docker_compose
    call :build_image
    goto end

:help
    call :show_help
    goto end

:unknown_command
    echo [ERROR] Unknown command: %1
    echo.
    call :show_help
    exit /b 1

REM Function definitions

:check_docker
    docker --version >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] Docker is not installed. Please install Docker Desktop first.
        exit /b 1
    )
    
    docker info >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] Docker is not running. Please start Docker Desktop first.
        exit /b 1
    )
    
    echo [SUCCESS] Docker is installed and running
    exit /b 0

:check_docker_compose
    docker-compose --version >nul 2>&1
    if not errorlevel 1 (
        set COMPOSE_CMD=docker-compose
        echo [SUCCESS] Docker Compose is available
        exit /b 0
    )
    
    docker compose version >nul 2>&1
    if not errorlevel 1 (
        set COMPOSE_CMD=docker compose
        echo [SUCCESS] Docker Compose is available
        exit /b 0
    )
    
    echo [ERROR] Docker Compose is not available. Please install it.
    exit /b 1

:check_env_file
    if not exist ".env" (
        echo [WARNING] .env file not found. Creating from example...
        if exist ".env.example" (
            copy ".env.example" ".env" >nul
            echo [WARNING] Please edit .env file and add your OpenAI API key
            echo [WARNING] You can get your API key from: https://platform.openai.com/api-keys
            pause
        ) else (
            echo OPENAI_API_KEY=your_openai_api_key_here > .env
            echo [WARNING] Please edit .env file and add your OpenAI API key
            pause
        )
    )
    
    findstr /C:"your_openai_api_key_here" .env >nul
    if not errorlevel 1 (
        echo [WARNING] Please update your OpenAI API key in the .env file
        echo [WARNING] Current .env file still contains placeholder
        set /p "continue=Continue anyway? (y/N): "
        if /i not "!continue!"=="y" exit /b 1
    )
    
    echo [SUCCESS] .env file is configured
    exit /b 0

:build_image
    echo [INFO] Building Docker image...
    %COMPOSE_CMD% build
    if errorlevel 1 (
        echo [ERROR] Failed to build Docker image
        exit /b 1
    )
    echo [SUCCESS] Docker image built successfully
    exit /b 0

:start_app
    echo [INFO] Starting the voice chatbot application...
    %COMPOSE_CMD% up -d
    if errorlevel 1 (
        echo [ERROR] Failed to start application
        exit /b 1
    )
    echo [SUCCESS] Application started successfully
    echo [SUCCESS] Voice Chatbot is now running at: http://localhost:%PORT%
    echo [INFO] To view logs: %COMPOSE_CMD% logs -f
    echo [INFO] To stop: %COMPOSE_CMD% down
    exit /b 0

:stop_app
    echo [INFO] Stopping the voice chatbot application...
    %COMPOSE_CMD% down
    if errorlevel 1 (
        echo [ERROR] Failed to stop application
        exit /b 1
    )
    echo [SUCCESS] Application stopped successfully
    exit /b 0

:show_status
    echo [INFO] Application status:
    %COMPOSE_CMD% ps
    echo.
    echo [INFO] Application logs (last 20 lines):
    %COMPOSE_CMD% logs --tail=20
    exit /b 0

:show_logs
    echo [INFO] Following application logs (Ctrl+C to exit):
    %COMPOSE_CMD% logs -f
    exit /b 0

:update_app
    echo [INFO] Updating application...
    
    if exist ".git" (
        echo [INFO] Pulling latest changes from git...
        git pull
    )
    
    echo [INFO] Rebuilding and restarting application...
    %COMPOSE_CMD% down
    %COMPOSE_CMD% build --no-cache
    %COMPOSE_CMD% up -d
    
    echo [SUCCESS] Application updated successfully
    exit /b 0

:show_help
    echo AI Voice Chatbot - Docker Deployment Script for Windows
    echo.
    echo Usage: %0 [command]
    echo.
    echo Commands:
    echo   start     - Build and start the application (default)
    echo   stop      - Stop the application
    echo   restart   - Restart the application
    echo   status    - Show application status and recent logs
    echo   logs      - Follow application logs
    echo   update    - Update and restart the application
    echo   build     - Build the Docker image only
    echo   help      - Show this help message
    echo.
    echo Examples:
    echo   %0              # Start the application
    echo   %0 start        # Start the application
    echo   %0 logs         # View live logs
    echo   %0 stop         # Stop the application
    exit /b 0

:end
echo.
echo Deployment script completed.
pause