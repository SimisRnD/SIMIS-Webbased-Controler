# PowerShell script to set up Python virtual environment and install requirements

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Found Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "Error: Python is not installed or not in PATH" -ForegroundColor Red
    exit 1
}

# Create virtual environment
Write-Host "Creating virtual environment..." -ForegroundColor Yellow
python -m venv venv

# Check if virtual environment was created successfully
if (Test-Path "venv\Scripts\Activate.ps1") {
    Write-Host "Virtual environment created successfully" -ForegroundColor Green
} else {
    Write-Host "Error: Failed to create virtual environment" -ForegroundColor Red
    exit 1
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& "venv\Scripts\Activate.ps1"

# Upgrade pip
Write-Host "Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# Install requirements
Write-Host "Installing requirements from requirements.txt..." -ForegroundColor Yellow
if (Test-Path "requirements.txt") {
    pip install -r requirements.txt
    Write-Host "Requirements installed successfully!" -ForegroundColor Green
} else {
    Write-Host "Error: requirements.txt file not found" -ForegroundColor Red
    exit 1
}
Write-Host "Setup complete! Virtual environment is ready to use." -ForegroundColor Green
Write-Host "To activate the environment in the future, run: venv\Scripts\Activate.ps1" -ForegroundColor Cyan
Write-Host "To turn off Virtual environment type deactivate" -ForegroundColor Cyan