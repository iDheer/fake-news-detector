# Quick Start Script for Fake News Detection System
# Use this script if you already have Microsoft Build Tools installed
# and just want to install dependencies without purging everything

# Check if virtual environment exists and activate it, or create it
if (Test-Path -Path ".\venv\Scripts\Activate.ps1") {
    Write-Host "Virtual environment found, activating..." -ForegroundColor Green
    .\venv\Scripts\Activate
} else {
    Write-Host "Creating new virtual environment..." -ForegroundColor Yellow
    python -m venv venv
    .\venv\Scripts\Activate
    python -m pip install --upgrade pip setuptools wheel
}

Write-Host "Installing or updating required packages..." -ForegroundColor Cyan

# Core packages
pip install fastapi==0.103.1 pydantic==2.3.0 uvicorn==0.23.2
pip install streamlit==1.26.0 requests==2.31.0 python-dotenv==1.0.0
pip install sqlalchemy==2.0.20

# AI and LangChain
pip install "openai>=1.6.1,<2.0.0" langchain langchain-openai langchain-community
pip install faiss-cpu chromadb sentence-transformers

# Install PyTorch (CPU version to avoid CUDA requirements)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Other dependencies
pip install transformers==4.33.2 scikit-learn==1.3.0
pip install nltk==3.8.1 spacy==3.6.1
pip install praw==7.7.1 wikipedia==1.4.0 newspaper3k==0.2.8
pip install beautifulsoup4==4.12.2 aiohttp==3.8.5

# Download language resources
python -m spacy download en_core_web_sm
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"

# Create .env file if it doesn't exist
if (-not (Test-Path -Path ".\.env")) {
    Write-Host "Creating .env file..." -ForegroundColor Yellow
    @"
# API Keys for Fake News Detection System

# OpenAI API Key (Required)
OPENAI_API_KEY=

# Reddit API Credentials (Optional)
REDDIT_CLIENT_ID=
REDDIT_CLIENT_SECRET=
REDDIT_USER_AGENT=FakeNewsDetector/1.0

# News API Key (Optional)
NEWSAPI_KEY=
"@ | Out-File -FilePath ".\.env" -Encoding utf8
    Write-Host "Please edit the .env file and add your OpenAI API key" -ForegroundColor Magenta
}

# Make sure data directories exist
if (-not (Test-Path -Path ".\app\data")) {
    New-Item -ItemType Directory -Path ".\app\data" -Force | Out-Null
}

Write-Host "`nSetup complete!" -ForegroundColor Green
Write-Host "To start the application, run: python run.py" -ForegroundColor Cyan
Write-Host "Don't forget to add your OpenAI API key to the .env file" -ForegroundColor Yellow

# Keep the terminal window open
Write-Host "`nPress any key to exit..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
