"""
Main launcher for the Fake News Detection system
"""
import os
import sys
import subprocess
import time
import webbrowser
import argparse
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Define paths
BASE_DIR = Path(__file__).resolve().parent

# Check for GPU usage from environment
USE_GPU = os.getenv("USE_GPU", "False").lower() == "true"

def check_dependencies():
    """Check if all required dependencies are installed"""
    try:
        import fastapi
        import streamlit
        import langchain
        import openai
        import torch
        import transformers
        import praw
        import sqlalchemy
        logger.info("All required dependencies are installed")
        return True
    except ImportError as e:
        logger.error(f"Missing dependency: {e}")
        return False

def install_dependencies():
    """Install required dependencies"""
    requirements_path = BASE_DIR / "requirements.txt"
    
    if not requirements_path.exists():
        logger.error("requirements.txt not found")
        return False
    
    logger.info("Installing dependencies...")
    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(requirements_path)])
    
    # Download NLTK data
    subprocess.run([sys.executable, "-c", "import nltk; nltk.download('punkt')"])
    
    # Download spaCy model
    subprocess.run([sys.executable, "-m", "spacy", "download", "en_core_web_sm"])
    
    logger.info("Dependencies installed successfully")
    return True

def start_backend():
    """Start the FastAPI backend server"""
    api_path = BASE_DIR / "app" / "api" / "app.py"
    
    if not api_path.exists():
        logger.error(f"Backend file not found: {api_path}")
        return None
    
    cmd = [
        sys.executable, "-m", "uvicorn", "app.api.app:app", 
        "--host", "0.0.0.0", "--port", "8000", "--reload"
    ]
    
    logger.info(f"Starting backend server: {' '.join(cmd)}")
    process = subprocess.Popen(cmd, cwd=str(BASE_DIR))
    
    # Give the server some time to start
    time.sleep(3)
    
    return process

def start_frontend():
    """Start the Streamlit frontend"""
    frontend_path = BASE_DIR / "app" / "frontend" / "streamlit_app.py"
    
    if not frontend_path.exists():
        logger.error(f"Frontend file not found: {frontend_path}")
        return None
    
    cmd = [
        sys.executable, "-m", "streamlit", "run", 
        str(frontend_path), "--server.port", "8501"
    ]
    
    logger.info(f"Starting frontend: {' '.join(cmd)}")
    process = subprocess.Popen(cmd, cwd=str(BASE_DIR))
    
    # Give the frontend some time to start
    time.sleep(3)
    
    # Open web browser
    webbrowser.open("http://localhost:8501")
    
    return process

def start_system(mode="all"):
    """Start the Fake News Detection system"""
    logger.info(f"Starting the Fake News Detection system in {mode} mode")
    
    if mode in ["all", "backend"]:
        backend_process = start_backend()
        if not backend_process:
            logger.error("Failed to start backend")
            return False
        
    if mode in ["all", "frontend"]:
        frontend_process = start_frontend()
        if not frontend_process:
            logger.error("Failed to start frontend")
            return False
    
    logger.info(f"System started in {mode} mode")
    
    try:
        # Keep the script running
        if mode == "all":
            logger.info("Press Ctrl+C to stop all services")
            while True:
                time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping services...")
        if mode in ["all", "backend"]:
            backend_process.terminate()
        if mode in ["all", "frontend"]:
            frontend_process.terminate()
        logger.info("All services stopped")
    
    return True

def main():
    """Main function to parse arguments and start the system"""
    parser = argparse.ArgumentParser(description="Fake News Detection System Launcher")
    parser.add_argument(
        "--mode", 
        choices=["all", "backend", "frontend"], 
        default="all",
        help="Mode to start the system in"
    )
    parser.add_argument(
        "--install", 
        action="store_true",
        help="Install dependencies before starting"
    )
    
    args = parser.parse_args()
    
    # Install dependencies if requested
    if args.install:
        if not install_dependencies():
            logger.error("Failed to install dependencies")
            sys.exit(1)
    elif not check_dependencies():
        logger.warning("Some dependencies are missing. Run with --install to install them.")
    
    # Start the system
    if not start_system(args.mode):
        logger.error("Failed to start the system")
        sys.exit(1)

if __name__ == "__main__":
    main()
