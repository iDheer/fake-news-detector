"""
Configuration utilities for loading environment variables
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).resolve().parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Social Media API Keys
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USERNAME = os.getenv("REDDIT_USERNAME")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT")

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL")

# News API Keys
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")
NEWS_DATA_API_KEY = os.getenv("NEWS_DATA_API_KEY")
GNEWS_API_KEY = os.getenv("GNEWS_API_KEY")

# System Configuration
USE_GPU = os.getenv("USE_GPU", "False").lower() == "true"
WIKIPEDIA_ROBUST = os.getenv("WIKIPEDIA_ROBUST", "True").lower() == "true"
LOGGING_LEVEL = os.getenv("LOGGING_LEVEL", "INFO")
WIKIPEDIA_LANGUAGE = os.getenv("WIKIPEDIA_LANGUAGE", "en")
MAX_WIKIPEDIA_RETRIES = int(os.getenv("MAX_WIKIPEDIA_RETRIES", "3"))
CLOUD_READY = os.getenv("CLOUD_READY", "True").lower() == "true"

# AI API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
AI_PROVIDER = os.getenv("AI_PROVIDER", "gemini")  # Options: "openai", "gemini"

def validate_configuration():
    """Validates that all required configuration variables are set"""
    missing_vars = []
    
    # Check for essential API keys
    if not REDDIT_CLIENT_ID or not REDDIT_CLIENT_SECRET:
        missing_vars.append("Reddit API credentials")
    
    if not NEWSAPI_KEY and not NEWS_DATA_API_KEY and not GNEWS_API_KEY:
        missing_vars.append("At least one News API key")
    
    if AI_PROVIDER == "openai" and not OPENAI_API_KEY:
        missing_vars.append("OpenAI API key - please add OPENAI_API_KEY to your .env file")
    elif AI_PROVIDER == "gemini" and not GOOGLE_API_KEY:
        missing_vars.append("Google API key - please add GOOGLE_API_KEY to your .env file")
    
    if missing_vars:
        for var in missing_vars:
            print(f"Missing configuration: {var}")
        return False
    
    return True
