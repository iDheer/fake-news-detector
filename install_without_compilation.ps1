# Installation without Compilation for Fake News Detection System
# This script installs pre-compiled packages wherever possible to avoid C++ compilation issues

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "    FAKE NEWS DETECTION SYSTEM - INSTALLATION WITHOUT COMPILATION     " -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "This script will install dependencies using pre-compiled binary wheels" -ForegroundColor Yellow
Write-Host "Use this if you don't have Microsoft Build Tools installed" -ForegroundColor Yellow
Write-Host

# Check if we're in a virtual environment
if (-not $env:VIRTUAL_ENV) {
    Write-Host "No active virtual environment detected." -ForegroundColor Red
    Write-Host "Would you like to create and activate one now? (y/n)" -ForegroundColor Yellow
    $createVenv = Read-Host
    
    if ($createVenv -eq "y" -or $createVenv -eq "Y") {
        # Create virtual environment
        Write-Host "Creating a new virtual environment..." -ForegroundColor Yellow
        python -m venv venv
        
        # Activate virtual environment
        Write-Host "Activating virtual environment..." -ForegroundColor Yellow
        .\venv\Scripts\Activate
        
        if (-not $env:VIRTUAL_ENV) {
            Write-Host "ERROR: Failed to activate virtual environment" -ForegroundColor Red
            Write-Host "Please run 'venv\Scripts\Activate' manually and try again" -ForegroundColor Red
            Write-Host "Press any key to exit..." -ForegroundColor Yellow
            $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
            exit 1
        }
    } else {
        Write-Host "WARNING: Installing without a virtual environment is not recommended" -ForegroundColor Red
        Write-Host "Do you want to continue anyway? (y/n)" -ForegroundColor Yellow
        $continue = Read-Host
        
        if ($continue -ne "y" -and $continue -ne "Y") {
            Write-Host "Installation cancelled" -ForegroundColor Red
            Write-Host "Press any key to exit..." -ForegroundColor Yellow
            $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
            exit 1
        }
    }
}

# Function to safely install packages with error handling
function Install-PreBuiltPackage {
    param (
        [string]$Name,
        [string]$Version = "",
        [switch]$FallbackToSource = $false,
        [switch]$Critical = $false
    )
    
    $package = if ($Version) { "$Name==$Version" } else { $Name }
    
    Write-Host "Installing $package..." -NoNewline
    
    try {
        # Try to install using binary wheels
        $output = pip install --prefer-binary --only-binary=:all: $package 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host " Success (binary)" -ForegroundColor Green
            return $true
        } else {
            if ($FallbackToSource) {
                # Fall back to regular install if binary install fails
                Write-Host " Retrying from source..." -NoNewline
                $output = pip install $package 2>&1
                if ($LASTEXITCODE -eq 0) {
                    Write-Host " Success (from source)" -ForegroundColor Green
                    return $true
                } else {
                    Write-Host " Failed" -ForegroundColor Red
                    if ($Critical) {
                        Write-Host "Critical package $package installation failed! Cannot continue." -ForegroundColor Red
                        return $false
                    } else {
                        Write-Host "Non-critical package $package installation failed. Continuing..." -ForegroundColor Yellow
                        return $true
                    }
                }
            } else {
                Write-Host " Failed" -ForegroundColor Red
                if ($Critical) {
                    Write-Host "Critical package $package installation failed! Cannot continue." -ForegroundColor Red
                    return $false
                } else {
                    Write-Host "Non-critical package $package installation failed. Continuing..." -ForegroundColor Yellow
                    return $true
                }
            }
        }
    } catch {
        Write-Host " Error" -ForegroundColor Red
        Write-Host "Exception: $_" -ForegroundColor Red
        if ($Critical) {
            return $false
        } else {
            return $true
        }
    }
}

# Clear pip cache to avoid conflicts
Write-Host "`nClearing pip cache..." -ForegroundColor Yellow
pip cache purge

# Install wheel for binary packages
Write-Host "Installing wheel and setuptools..." -ForegroundColor Yellow
pip install --upgrade wheel setuptools pip

# Install core dependencies that don't require compilation
Write-Host "`nInstalling core dependencies..." -ForegroundColor Green
$success = $true
$success = $success -and (Install-PreBuiltPackage "fastapi" "0.103.1" -FallbackToSource -Critical)
$success = $success -and (Install-PreBuiltPackage "pydantic" "2.3.0" -FallbackToSource -Critical)
$success = $success -and (Install-PreBuiltPackage "uvicorn" "0.23.2" -FallbackToSource -Critical)
$success = $success -and (Install-PreBuiltPackage "streamlit" "1.26.0" -FallbackToSource -Critical)
$success = $success -and (Install-PreBuiltPackage "python-dotenv" "1.0.0" -FallbackToSource -Critical)
$success = $success -and (Install-PreBuiltPackage "sqlalchemy" "2.0.20" -FallbackToSource -Critical)

if (-not $success) {
    Write-Host "Critical dependencies failed to install. Cannot continue." -ForegroundColor Red
    Write-Host "Press any key to exit..." -ForegroundColor Yellow
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}

# Install AI dependencies with compatible versions
Write-Host "`nInstalling OpenAI and LangChain..." -ForegroundColor Green
Install-PreBuiltPackage "openai" "1.6.1" -FallbackToSource -Critical
Install-PreBuiltPackage "langchain" -FallbackToSource -Critical
Install-PreBuiltPackage "langchain-openai" -FallbackToSource -Critical
Install-PreBuiltPackage "langchain-community" -FallbackToSource

# Install PyTorch (CPU version to avoid CUDA requirements)
Write-Host "`nInstalling PyTorch (CPU version)..." -ForegroundColor Green
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Install scientific and ML packages using pre-built wheels
Write-Host "`nInstalling scientific and ML packages (pre-built wheels)..." -ForegroundColor Green
Install-PreBuiltPackage "numpy" -FallbackToSource
Install-PreBuiltPackage "scipy" -FallbackToSource
Install-PreBuiltPackage "pandas" -FallbackToSource
Install-PreBuiltPackage "scikit-learn" "1.3.0"
Install-PreBuiltPackage "transformers" "4.33.2" -FallbackToSource
Install-PreBuiltPackage "sentence-transformers" -FallbackToSource

# Try to install spaCy and NLTK from binaries
Write-Host "`nInstalling NLP packages..." -ForegroundColor Green
Install-PreBuiltPackage "nltk" "3.8.1" -FallbackToSource
Install-PreBuiltPackage "spacy" "3.6.1"

# Install RAG components (using simpler alternatives if needed)
Write-Host "`nInstalling RAG components..." -ForegroundColor Green
Install-PreBuiltPackage "chromadb" -FallbackToSource

# Install other dependencies that typically don't require compilation
Write-Host "`nInstalling remaining packages..." -ForegroundColor Green
Install-PreBuiltPackage "beautifulsoup4" "4.12.2" -FallbackToSource
Install-PreBuiltPackage "aiohttp" "3.8.5" -FallbackToSource
Install-PreBuiltPackage "plotly" "5.16.1" -FallbackToSource
Install-PreBuiltPackage "matplotlib" "3.8.0"
Install-PreBuiltPackage "praw" "7.7.1" -FallbackToSource
Install-PreBuiltPackage "wikipedia" "1.4.0" -FallbackToSource
Install-PreBuiltPackage "newspaper3k" "0.2.8" -FallbackToSource

# Try to download language models
Write-Host "`nDownloading language resources..." -ForegroundColor Green
try {
    Write-Host "Downloading spaCy English language model..." -NoNewline
    $output = python -m spacy download en_core_web_sm 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host " Success" -ForegroundColor Green
    } else {
        Write-Host " Failed" -ForegroundColor Yellow
        Write-Host "You may need to run 'python -m spacy download en_core_web_sm' manually later" -ForegroundColor Yellow
    }
} catch {
    Write-Host " Error" -ForegroundColor Red
    Write-Host "You may need to run 'python -m spacy download en_core_web_sm' manually later" -ForegroundColor Yellow
}

try {
    Write-Host "Downloading NLTK data..." -NoNewline
    $output = python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host " Success" -ForegroundColor Green
    } else {
        Write-Host " Failed" -ForegroundColor Yellow
        Write-Host "You may need to run 'python -c \"import nltk; nltk.download(\'punkt\')\"' manually later" -ForegroundColor Yellow
    }
} catch {
    Write-Host " Error" -ForegroundColor Red
    Write-Host "You may need to download NLTK data manually later" -ForegroundColor Yellow
}

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

# Check if .env file exists, create if needed
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
    Write-Host "Please edit the .env file and add your OpenAI API key (required)" -ForegroundColor Magenta
}

# Create requirements.txt from installed packages
pip freeze > requirements.txt

Write-Host "`n=====================================================================" -ForegroundColor Cyan
Write-Host "Installation complete without compilation!" -ForegroundColor Green
Write-Host "=====================================================================" -ForegroundColor Cyan

Write-Host "`nNext steps:" -ForegroundColor White
Write-Host "1. Add your OpenAI API key to the .env file (REQUIRED)" -ForegroundColor White
Write-Host "2. Run 'python run.py' to start the application" -ForegroundColor White
Write-Host "`nThe application will be available at:" -ForegroundColor Green
Write-Host "- Frontend: http://localhost:8501" -ForegroundColor Green
Write-Host "- API Documentation: http://localhost:8000/docs" -ForegroundColor Green

# Keep the terminal window open
Write-Host "`nPress any key to exit..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
