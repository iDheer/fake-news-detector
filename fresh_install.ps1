# Complete reset and installation script with Microsoft Build Tools support
# This will purge all previous installations and set up a fresh environment

Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host "     FAKE NEWS DETECTION SYSTEM - FRESH INSTALLATION     " -ForegroundColor Cyan
Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host "This script will remove previous installations and create a clean environment" -ForegroundColor Yellow
Write-Host "Make sure you have Microsoft Build Tools installed for C++ dependencies" -ForegroundColor Yellow
Write-Host

# Function to check if running as administrator
function Test-Administrator {
    $currentUser = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
    return $currentUser.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# Check if running as administrator and warn if not
if (-not (Test-Administrator)) {
    Write-Host "WARNING: You are not running as Administrator. Some operations may fail." -ForegroundColor Red
    Write-Host "It's recommended to run this script as Administrator." -ForegroundColor Red
    Write-Host "Press any key to continue anyway, or Ctrl+C to cancel..." -ForegroundColor Yellow
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}

# Check if Microsoft Build Tools are installed
$vcvarsallPath = "C:\Program Files (x86)\Microsoft Visual Studio\*\BuildTools\VC\Auxiliary\Build\vcvarsall.bat"
$vcvarsall = Get-ChildItem -Path $vcvarsallPath -ErrorAction SilentlyContinue

if ($null -eq $vcvarsall) {
    Write-Host "WARNING: Microsoft Build Tools might not be installed or not found." -ForegroundColor Red
    Write-Host "Some packages requiring C++ compilation may fail to install." -ForegroundColor Red
    Write-Host "If installation fails, please install Microsoft Visual C++ Build Tools" -ForegroundColor Red
    Write-Host "Press any key to continue anyway, or Ctrl+C to cancel..." -ForegroundColor Yellow
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}

Write-Host "Step 1: Cleaning up previous installation" -ForegroundColor Green

# Check if we're in a virtual environment and deactivate if so
if ($env:VIRTUAL_ENV) {
    Write-Host "Deactivating current virtual environment..." -ForegroundColor Yellow
    deactivate
}

# Delete existing virtual environment
if (Test-Path -Path ".\venv") {
    Write-Host "Removing existing virtual environment..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force venv
}

# Remove __pycache__ directories
Write-Host "Cleaning up __pycache__ directories..." -ForegroundColor Yellow
Get-ChildItem -Path . -Filter "__pycache__" -Recurse | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

# Clear pip cache
Write-Host "Clearing pip cache..." -ForegroundColor Yellow
pip cache purge

# Step 2: Create a fresh virtual environment
Write-Host "Step 2: Creating a fresh virtual environment..." -ForegroundColor Green

# Check Python version
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.8 or later and try again" -ForegroundColor Red
    Write-Host "Press any key to exit..." -ForegroundColor Yellow
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}

Write-Host "Detected: $pythonVersion" -ForegroundColor Cyan
Write-Host "Creating fresh virtual environment..." -ForegroundColor Yellow
python -m venv venv

if (-not (Test-Path -Path ".\venv\Scripts\Activate.ps1")) {
    Write-Host "ERROR: Failed to create virtual environment" -ForegroundColor Red
    Write-Host "Please check your Python installation and try again" -ForegroundColor Red
    Write-Host "Press any key to exit..." -ForegroundColor Yellow
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}

# Activate the virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
try {
    .\venv\Scripts\Activate
} catch {
    Write-Host "ERROR: Failed to activate virtual environment" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    Write-Host "Press any key to exit..." -ForegroundColor Yellow
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}

# Upgrade pip, setuptools, and wheel
Write-Host "Upgrading pip, setuptools, and wheel..." -ForegroundColor Yellow
try {
    python -m pip install --upgrade pip setuptools wheel
} catch {
    Write-Host "WARNING: Failed to upgrade pip. Continuing with installation..." -ForegroundColor Yellow
}

# Step 3: Install dependencies
Write-Host "Step 3: Installing dependencies (this may take a while)..." -ForegroundColor Green
Write-Host "Using Microsoft Build Tools for C++ dependencies if available" -ForegroundColor Cyan

# Function to install package with error handling
function Install-Package {
    param (
        [string]$name,
        [string]$version = "",
        [switch]$critical = $false
    )
    
    $package = if ($version) { "$name==$version" } else { $name }
    
    try {
        Write-Host "Installing $package..." -NoNewline
        $output = pip install $package 2>&1
        Write-Host " Done" -ForegroundColor Green
        return $true
    }
    catch {
        if ($critical) {
            Write-Host " FAILED (critical dependency)" -ForegroundColor Red
            Write-Host "Error installing $package. This is a critical dependency." -ForegroundColor Red
            Write-Host "Error details: $_" -ForegroundColor Red
            return $false
        }
        else {
            Write-Host " FAILED (will try to continue)" -ForegroundColor Yellow
            Write-Host "Error installing $package. Will try to continue without it." -ForegroundColor Yellow
            return $true
        }
    }
}

# Install base dependencies
Write-Host "`nInstalling base dependencies..." -ForegroundColor Yellow
$success = $true
$success = $success -and (Install-Package "fastapi" "0.103.1" -critical)
$success = $success -and (Install-Package "pydantic" "2.3.0" -critical)
$success = $success -and (Install-Package "uvicorn" "0.23.2" -critical)
$success = $success -and (Install-Package "streamlit" "1.26.0" -critical)
$success = $success -and (Install-Package "requests" "2.31.0" -critical)
$success = $success -and (Install-Package "python-dotenv" "1.0.0" -critical)

if (-not $success) {
    Write-Host "Critical dependencies failed to install. Cannot continue." -ForegroundColor Red
    Write-Host "Press any key to exit..." -ForegroundColor Yellow
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}

# Install database and data processing packages
Write-Host "`nInstalling database and data processing packages..." -ForegroundColor Yellow
Install-Package "sqlalchemy" "2.0.20"
Install-Package "pandas" "2.1.0"

# Install vector database and embeddings for RAG
Write-Host "`nInstalling vector database and RAG components..." -ForegroundColor Yellow
Install-Package "sentence-transformers"
Install-Package "chromadb"
Install-Package "faiss-cpu"

# Install AI and ML packages
Write-Host "`nInstalling AI and ML packages (this may take some time)..." -ForegroundColor Yellow
Install-Package "openai" "1.6.1"
Install-Package "langchain"
Install-Package "langchain-openai" 
Install-Package "langchain-community"
Install-Package "scikit-learn" "1.3.0" 
Install-Package "transformers" "4.33.2"

# Install PyTorch (CPU version to avoid CUDA issues)
Write-Host "`nInstalling PyTorch (CPU version)..." -ForegroundColor Yellow
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Install NLP packages
Write-Host "`nInstalling NLP packages..." -ForegroundColor Yellow
Install-Package "nltk" "3.8.1"
Install-Package "spacy" "3.6.1"

# Install API integrations
Write-Host "`nInstalling API integrations..." -ForegroundColor Yellow
Install-Package "praw" "7.7.1"
Install-Package "wikipedia" "1.4.0"
Install-Package "newspaper3k" "0.2.8"

# Install visualization and testing tools
Write-Host "`nInstalling visualization and testing tools..." -ForegroundColor Yellow
Install-Package "plotly" "5.16.1"
Install-Package "matplotlib" "3.8.0"
Install-Package "pytest" "7.4.2"
Install-Package "pytest-asyncio" "0.21.1"
Install-Package "beautifulsoup4" "4.12.2"
Install-Package "aiohttp" "3.8.5"

# Step 4: Download additional resources
Write-Host "Step 4: Downloading additional language resources..." -ForegroundColor Green

# Try to download SpaCy model
try {
    Write-Host "Downloading spaCy English language model..." -ForegroundColor Yellow
    $spacy_output = python -m spacy download en_core_web_sm 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "WARNING: Could not download spaCy English language model" -ForegroundColor Yellow
        Write-Host "You may need to run 'python -m spacy download en_core_web_sm' manually later" -ForegroundColor Yellow
    } else {
        Write-Host "SpaCy English language model downloaded successfully" -ForegroundColor Green
    }
} catch {
    Write-Host "WARNING: Could not download spaCy English language model" -ForegroundColor Yellow
}

# Try to download NLTK data
try {
    Write-Host "Downloading NLTK data..." -ForegroundColor Yellow
    python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')" 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "WARNING: Could not download NLTK data" -ForegroundColor Yellow
        Write-Host "You may need to run 'python -c \"import nltk; nltk.download('punkt'); nltk.download('stopwords')\"' manually later" -ForegroundColor Yellow
    } else {
        Write-Host "NLTK data downloaded successfully" -ForegroundColor Green
    }
} catch {
    Write-Host "WARNING: Could not download NLTK data" -ForegroundColor Yellow
}

# Step 5: Set up project directories and configuration
Write-Host "Step 5: Setting up project directories and configuration..." -ForegroundColor Green

# Create required directories
$directories = @(
    ".\app\data",
    ".\app\data\embeddings",
    ".\app\data\cache"
)

foreach ($dir in $directories) {
    if (-not (Test-Path -Path $dir)) {
        Write-Host "Creating directory: $dir" -ForegroundColor Yellow
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}

# Check if .env file exists and create if necessary
if (-not (Test-Path -Path ".\.env")) {
    # Create .env file from example if it doesn't exist
    if (Test-Path -Path ".\.env.example") {
        Write-Host "Creating .env file from example template..." -ForegroundColor Yellow
        Copy-Item -Path ".\.env.example" -Destination ".\.env"
    } else {
        Write-Host "Creating new .env file..." -ForegroundColor Yellow
        New-Item -ItemType File -Path ".\.env" -Force | Out-Null
        @"
# API Keys for Fake News Detection System

# OpenAI API Key (Required for AI analysis)
# Get your API key from: https://platform.openai.com/api-keys
OPENAI_API_KEY=

# Reddit API Credentials (Optional but recommended)
# Create an application at: https://www.reddit.com/prefs/apps
REDDIT_CLIENT_ID=
REDDIT_CLIENT_SECRET=
REDDIT_USERNAME=
REDDIT_USER_AGENT=FakeNewsDetector/1.0

# News API Keys (Optional - at least one recommended)
# Get from: https://newsapi.org/
NEWSAPI_KEY=

# Database Configuration
DATABASE_URL=sqlite:///./app/data/fakenews.db

# RAG Configuration
EMBEDDINGS_PATH=./app/data/embeddings
VECTOR_DB_PATH=./app/data/vector_db

# System Configuration
LOG_LEVEL=INFO
DEBUG_MODE=False
"@ | Out-File -FilePath ".\.env" -Encoding utf8
    }
    Write-Host "Please edit the .env file and add your OpenAI API key (required)" -ForegroundColor Magenta
}

# Create or update requirements.txt from installed packages
Write-Host "Generating requirements.txt from installed packages..." -ForegroundColor Yellow
pip freeze > requirements.txt

# Verification step
$verificationFailed = $false
Write-Host "`nStep 6: Verifying installation..." -ForegroundColor Green

# Test importing critical packages
$packagesToTest = @(
    "fastapi",
    "streamlit",
    "langchain",
    "openai"
)

foreach ($package in $packagesToTest) {
    Write-Host "Testing import of $package..." -NoNewline
    $testResult = python -c "import $package; print(f'$package version {$package.__version__}')" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host " OK" -ForegroundColor Green
    } else {
        Write-Host " FAILED" -ForegroundColor Red
        $verificationFailed = $true
    }
}

# Final status
Write-Host "`n=========================================================" -ForegroundColor Cyan
if ($verificationFailed) {
    Write-Host "Installation completed with WARNINGS" -ForegroundColor Yellow
    Write-Host "Some components may not work correctly." -ForegroundColor Yellow
} else {
    Write-Host "Installation completed SUCCESSFULLY" -ForegroundColor Green
}
Write-Host "=========================================================" -ForegroundColor Cyan

Write-Host "`nBefore running the application:" -ForegroundColor White
Write-Host "1. Add your OpenAI API key to the .env file (REQUIRED)" -ForegroundColor White 
Write-Host "   Without this key, the AI analysis will not work." -ForegroundColor White
Write-Host "2. Run 'python run.py' to start the application" -ForegroundColor White

Write-Host "`nThe application will be available at:" -ForegroundColor Green
Write-Host "- Frontend: http://localhost:8501" -ForegroundColor Green
Write-Host "- API Documentation: http://localhost:8000/docs" -ForegroundColor Green

# Keep the terminal window open
Write-Host "`nPress any key to exit..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
