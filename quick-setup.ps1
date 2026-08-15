# Deviant Quick Setup Script for Windows PowerShell
# Run this script to set up the project automatically

Write-Host "==================================" -ForegroundColor Cyan
Write-Host "Deviant Phase 1 MVP - Quick Setup" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

# Check if running in correct directory
if (-Not (Test-Path "docker-compose.yml")) {
    Write-Host "ERROR: Please run this script from the Deviant root directory" -ForegroundColor Red
    Write-Host "Current directory: $PWD" -ForegroundColor Yellow
    Write-Host "Expected: ...\Domains\02-shoman-saas-domain\apps\Deviant" -ForegroundColor Yellow
    exit 1
}

Write-Host "Step 1/7: Checking prerequisites..." -ForegroundColor Green

# Check Docker
Write-Host "  Checking Docker..." -NoNewline
try {
    $dockerVersion = docker --version 2>$null
    if ($dockerVersion) {
        Write-Host " OK" -ForegroundColor Green
        Write-Host "    $dockerVersion" -ForegroundColor Gray
    } else {
        throw "Docker not found"
    }
} catch {
    Write-Host " FAILED" -ForegroundColor Red
    Write-Host "    Docker is not installed or not running" -ForegroundColor Red
    Write-Host "    Download from: https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
    exit 1
}

# Check Docker Compose
Write-Host "  Checking Docker Compose..." -NoNewline
try {
    $composeVersion = docker-compose --version 2>$null
    if ($composeVersion) {
        Write-Host " OK" -ForegroundColor Green
        Write-Host "    $composeVersion" -ForegroundColor Gray
    } else {
        throw "Docker Compose not found"
    }
} catch {
    Write-Host " FAILED" -ForegroundColor Red
    Write-Host "    Docker Compose is not installed" -ForegroundColor Red
    exit 1
}

# Check Python
Write-Host "  Checking Python..." -NoNewline
try {
    $pythonVersion = python --version 2>$null
    if ($pythonVersion -match "Python 3\.(1[1-9]|[2-9]\d)") {
        Write-Host " OK" -ForegroundColor Green
        Write-Host "    $pythonVersion" -ForegroundColor Gray
    } else {
        throw "Python 3.11+ required"
    }
} catch {
    Write-Host " FAILED" -ForegroundColor Red
    Write-Host "    Python 3.11+ is required" -ForegroundColor Red
    Write-Host "    Download from: https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "Step 2/7: Setting up environment file..." -ForegroundColor Green

if (-Not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "  Created .env file from template" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  IMPORTANT: You need to edit .env file!" -ForegroundColor Yellow
    Write-Host "  1. Add your ANTHROPIC_API_KEY (required)" -ForegroundColor Yellow
    Write-Host "  2. Set a secure DB_PASSWORD" -ForegroundColor Yellow
    Write-Host ""
    $editNow = Read-Host "  Open .env in Notepad now? (y/n)"
    if ($editNow -eq 'y') {
        notepad .env
        Write-Host "  Waiting for you to save and close Notepad..." -ForegroundColor Cyan
        Write-Host "  Press Enter when done..." -ForegroundColor Cyan
        Read-Host
    }
} else {
    Write-Host "  .env file already exists" -ForegroundColor Gray
}

# Check if API key is set
$envContent = Get-Content ".env" -Raw
if ($envContent -match "ANTHROPIC_API_KEY=sk-ant-") {
    Write-Host "  Anthropic API key found" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "  WARNING: ANTHROPIC_API_KEY not set in .env" -ForegroundColor Red
    Write-Host "  Get your API key from: https://console.anthropic.com/" -ForegroundColor Yellow
    Write-Host ""
    $continue = Read-Host "  Continue anyway? (y/n)"
    if ($continue -ne 'y') {
        exit 1
    }
}

Write-Host ""
Write-Host "Step 3/7: Starting PostgreSQL and Redis..." -ForegroundColor Green

docker-compose up -d postgres redis

if ($LASTEXITCODE -eq 0) {
    Write-Host "  Services started successfully" -ForegroundColor Green
    Write-Host "  Waiting for services to be healthy (30 seconds)..." -ForegroundColor Gray
    Start-Sleep -Seconds 30
} else {
    Write-Host "  Failed to start services" -ForegroundColor Red
    Write-Host "  Try: docker-compose down, then restart Docker Desktop" -ForegroundColor Yellow
    exit 1
}

# Check if services are healthy
$postgresStatus = docker-compose ps postgres | Select-String "healthy"
$redisStatus = docker-compose ps redis | Select-String "healthy"

if ($postgresStatus -and $redisStatus) {
    Write-Host "  All services healthy!" -ForegroundColor Green
} else {
    Write-Host "  Warning: Services may not be fully healthy yet" -ForegroundColor Yellow
    Write-Host "  Check with: docker-compose ps" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Step 4/7: Setting up Python virtual environment..." -ForegroundColor Green

Set-Location backend

if (-Not (Test-Path "venv")) {
    Write-Host "  Creating virtual environment..." -ForegroundColor Gray
    python -m venv venv
    Write-Host "  Virtual environment created" -ForegroundColor Green
} else {
    Write-Host "  Virtual environment already exists" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Step 5/7: Activating virtual environment..." -ForegroundColor Green

# Activate venv
try {
    & .\venv\Scripts\Activate.ps1
    Write-Host "  Virtual environment activated" -ForegroundColor Green
} catch {
    Write-Host "  Could not activate virtual environment" -ForegroundColor Red
    Write-Host "  You may need to run: Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "Step 6/7: Installing Python dependencies..." -ForegroundColor Green
Write-Host "  This may take a few minutes..." -ForegroundColor Gray

pip install -r requirements.txt --quiet

if ($LASTEXITCODE -eq 0) {
    Write-Host "  Dependencies installed successfully" -ForegroundColor Green
} else {
    Write-Host "  Failed to install dependencies" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Step 7/7: Initializing database..." -ForegroundColor Green

# Run Alembic migrations
Write-Host "  Running database migrations..." -ForegroundColor Gray
alembic upgrade head

if ($LASTEXITCODE -eq 0) {
    Write-Host "  Database initialized successfully" -ForegroundColor Green
} else {
    Write-Host "  Failed to initialize database" -ForegroundColor Red
    Write-Host "  Check if PostgreSQL is running: docker-compose ps" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Current Status:" -ForegroundColor Yellow
Write-Host "  Database:    Running (PostgreSQL)" -ForegroundColor Green
Write-Host "  Cache:       Running (Redis)" -ForegroundColor Green
Write-Host "  Backend:     NOT STARTED (needs agent implementations)" -ForegroundColor Yellow
Write-Host "  Frontend:    NOT BUILT (pending)" -ForegroundColor Yellow
Write-Host ""

Write-Host "What's Been Built:" -ForegroundColor Yellow
Write-Host "  Database schema and models" -ForegroundColor Green
Write-Host "  Base agent framework" -ForegroundColor Green
Write-Host "  Docker configuration" -ForegroundColor Green
Write-Host "  Migration system" -ForegroundColor Green
Write-Host ""

Write-Host "What's Needed:" -ForegroundColor Yellow
Write-Host "  7 agent implementations (CEO, CTO, PM, HR, Engineers, Designer)" -ForegroundColor Red
Write-Host "  FastAPI routes and main app" -ForegroundColor Red
Write-Host "  Agent initialization script" -ForegroundColor Red
Write-Host "  Frontend dashboard" -ForegroundColor Red
Write-Host ""

Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "  1. Read IMPLEMENTATION_STATUS.md for full details" -ForegroundColor White
Write-Host "  2. Decide on implementation approach (see that file)" -ForegroundColor White
Write-Host "  3. Let me know when ready to continue building!" -ForegroundColor White
Write-Host ""

Write-Host "Useful Commands:" -ForegroundColor Cyan
Write-Host "  View services:     docker-compose ps" -ForegroundColor White
Write-Host "  View logs:         docker-compose logs -f postgres" -ForegroundColor White
Write-Host "  Stop services:     docker-compose down" -ForegroundColor White
Write-Host "  Activate venv:     .\venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host ""

Write-Host "Press Enter to exit..." -ForegroundColor Gray
Read-Host
