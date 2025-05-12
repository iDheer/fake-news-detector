@echo off
REM Run script for Fake News Detector application

echo Starting Fake News Detector...

REM Check if virtual environment exists
if not exist venv (
    echo Virtual environment not found. Creating one...
    python -m venv venv
    call venv\Scripts\activate
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    echo Virtual environment setup complete.
) else (
    call venv\Scripts\activate
)

REM Check if requirements are installed
python -c "import fastapi" 2>NUL
if %ERRORLEVEL% NEQ 0 (
    echo Installing dependencies...
    pip install -r requirements.txt
)

REM Check if database exists
if not exist app\data (
    mkdir app\data
)

REM Check if OpenAI API key is set
set OPENAI_KEY_SET=0
for /F "tokens=1,2 delims==" %%a in (.env) do (
    if "%%a"=="OPENAI_API_KEY" (
        if not "%%b"=="" (
            set OPENAI_KEY_SET=1
        )
    )
)

if %OPENAI_KEY_SET%==0 (
    echo WARNING: OPENAI_API_KEY not set in .env file. LLM features will not work correctly.
    echo Please add your OpenAI API key to the .env file.
    timeout /t 5
)

REM Run the application
echo Starting services...
python run.py %*

REM Deactivate virtual environment when done
call venv\Scripts\deactivate
