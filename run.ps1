# run.ps1 - Script to start the Fake News Detection System
# This script will activate the virtual environment and start both the backend and frontend

Write-Host "Starting Fake News Detection System..." -ForegroundColor Cyan

# Check if virtual environment exists
if (-not (Test-Path -Path ".\venv\Scripts\Activate.ps1")) {
    Write-Host "Error: Virtual environment not found." -ForegroundColor Red
    Write-Host "Please run fresh_install.ps1 or quick_start.ps1 first." -ForegroundColor Red
    Write-Host "Press any key to exit..." -ForegroundColor Yellow
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}

# Check if .env file exists with OpenAI key
if (-not (Test-Path -Path ".\.env")) {
    Write-Host "Error: .env file not found." -ForegroundColor Red
    Write-Host "Please create a .env file with your API keys." -ForegroundColor Red
    Write-Host "Press any key to exit..." -ForegroundColor Yellow
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}

# Read .env file to check for OpenAI API key
$envContent = Get-Content -Path ".\.env" -Raw
if (-not ($envContent -match "OPENAI_API_KEY=.+")) {
    Write-Host "Warning: OpenAI API key not found in .env file." -ForegroundColor Yellow
    Write-Host "The AI analysis features will not work without an API key." -ForegroundColor Yellow
    Write-Host "Do you want to continue anyway? (y/n)" -ForegroundColor Yellow
    $continue = Read-Host
    
    if ($continue -ne "y" -and $continue -ne "Y") {
        Write-Host "Please add your OpenAI API key to the .env file and try again." -ForegroundColor Red
        Write-Host "Press any key to exit..." -ForegroundColor Yellow
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
        exit 1
    }
}

# Activate the virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Green
.\venv\Scripts\Activate

# Function to check if a port is in use
function Test-PortInUse {
    param (
        [int]$Port
    )
    
    $listener = $null
    try {
        $listener = New-Object System.Net.Sockets.TcpListener([System.Net.IPAddress]::Loopback, $Port)
        $listener.Start()
        $listener.Stop()
        return $false
    } catch {
        return $true
    } finally {
        if ($listener) {
            $listener.Stop()
        }
    }
}

# Check if ports are available
$apiPort = 8000
$frontendPort = 8501

if (Test-PortInUse -Port $apiPort) {
    Write-Host "Warning: Port $apiPort is already in use. API server may not start properly." -ForegroundColor Yellow
}

if (Test-PortInUse -Port $frontendPort) {
    Write-Host "Warning: Port $frontendPort is already in use. Frontend may not start properly." -ForegroundColor Yellow
}

# Start the API server in a new window
$apiCommand = "python -m uvicorn app.api.app:app --host 0.0.0.0 --port $apiPort"
Write-Host "Starting API server on port $apiPort..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit -Command `"cd '$PWD'; .\venv\Scripts\Activate; $apiCommand`""

# Wait for API server to start
Write-Host "Waiting for API server to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

# Start the Streamlit frontend
$streamlitCommand = "streamlit run app/frontend/streamlit_app.py"
Write-Host "Starting Streamlit frontend on port $frontendPort..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit -Command `"cd '$PWD'; .\venv\Scripts\Activate; $streamlitCommand`""

# Wait for browser to open
Start-Sleep -Seconds 2

# Open the browser to the Streamlit app
Write-Host "Opening browser to http://localhost:$frontendPort ..." -ForegroundColor Cyan
Start-Process "http://localhost:$frontendPort"

Write-Host "`nFake News Detection System is now running!" -ForegroundColor Green
Write-Host "- Frontend: http://localhost:$frontendPort" -ForegroundColor Cyan
Write-Host "- API Documentation: http://localhost:$apiPort/docs" -ForegroundColor Cyan
Write-Host "`nPress Ctrl+C in the terminal windows to stop the application" -ForegroundColor Yellow
