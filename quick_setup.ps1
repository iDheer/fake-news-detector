# Quick setup script for the Fake News Detector project
Write-Host "Setting up Fake News Detector environment..." -ForegroundColor Green

# Check if Python is installed
try {
    $pythonVersion = python --version
    Write-Host "Found Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "Python is not installed or not in PATH. Please install Python 3.8 or higher." -ForegroundColor Red
    exit 1
}

# Create virtual environment
Write-Host "Creating virtual environment..." -ForegroundColor Yellow
python -m venv venv

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
.\venv\Scripts\Activate

# Upgrade pip
Write-Host "Upgrading pip to latest version..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# Install core requirements first
Write-Host "Installing core dependencies..." -ForegroundColor Yellow
pip install fastapi streamlit uvicorn requests python-dotenv sqlalchemy pandas

# Install AI dependencies
Write-Host "Installing AI dependencies (this may take a while)..." -ForegroundColor Yellow
pip install "openai>=1.6.1,<2.0.0" langchain==0.0.267 langchain-openai==0.0.2

# Install wheel for pre-built packages
Write-Host "Installing wheel for pre-built packages..." -ForegroundColor Yellow
pip install wheel

# Install packages that need compilation using pre-built wheels
Write-Host "Installing scientific and ML packages (using pre-built wheels)..." -ForegroundColor Yellow
pip install --only-binary=:all: numpy scipy pandas scikit-learn
pip install --only-binary=:all: torch torchvision
pip install --only-binary=:all: transformers
pip install --only-binary=:all: nltk spacy

# Install the rest of the requirements
Write-Host "Installing remaining dependencies from requirements.txt..." -ForegroundColor Yellow
pip install --no-deps -r requirements.txt

# Install spaCy model
Write-Host "Downloading spaCy English language model..." -ForegroundColor Yellow
python -m spacy download en_core_web_sm

# Download NLTK data
Write-Host "Downloading NLTK data..." -ForegroundColor Yellow
python -c "import nltk; nltk.download('punkt')"

# Create data directory if it doesn't exist
if (-not (Test-Path -Path ".\app\data")) {
    Write-Host "Creating data directory..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path ".\app\data" -Force | Out-Null
}

# Check for OpenAI API key in .env
if (Test-Path -Path ".\.env") {
    $envContent = Get-Content .\.env -Raw
    if (-not ($envContent -match "OPENAI_API_KEY=.+")) {
        Write-Host "WARNING: OPENAI_API_KEY not found in .env file. LLM features will not work." -ForegroundColor Yellow
        Write-Host "Please add your OpenAI API key to the .env file." -ForegroundColor Yellow
    } else {
        Write-Host "OpenAI API key found in .env file." -ForegroundColor Green
    }
} else {
    Write-Host "WARNING: .env file not found. Please create one from .env.example." -ForegroundColor Yellow
}

Write-Host "Setup complete! To run the application, use:" -ForegroundColor Green
Write-Host "python run.py" -ForegroundColor Cyan

# Keep the terminal window open
Write-Host "Press any key to exit..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
