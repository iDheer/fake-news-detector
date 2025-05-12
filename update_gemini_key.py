#!/usr/bin/env python
"""
Utility script to update the .env file with Google API key for Gemini AI
"""
import os
from pathlib import Path

def update_env_file():
    """Update the .env file with the Google API key"""
    env_path = Path(__file__).resolve().parent / '.env'
    
    if not env_path.exists():
        print(f"Error: .env file not found at {env_path}")
        return False
    
    # Prompt for API key
    google_api_key = input("Enter your Google API key for Gemini: ")
    
    if not google_api_key.strip():
        print("No API key provided. Exiting.")
        return False
    
    # Read current .env content
    with open(env_path, 'r') as file:
        env_content = file.read()
    
    # Replace or add Google API key
    if "GOOGLE_API_KEY=" in env_content:
        lines = env_content.split('\n')
        for i, line in enumerate(lines):
            if line.startswith("GOOGLE_API_KEY="):
                lines[i] = f'GOOGLE_API_KEY="{google_api_key}"'
                break
        env_content = '\n'.join(lines)
    else:
        # If not found, add it after AI_PROVIDER
        lines = env_content.split('\n')
        for i, line in enumerate(lines):
            if line.startswith("AI_PROVIDER="):
                lines.insert(i + 1, f'GOOGLE_API_KEY="{google_api_key}"')
                break
        env_content = '\n'.join(lines)
    
    # Write updated content back to .env
    with open(env_path, 'w') as file:
        file.write(env_content)
    
    print(f"Successfully updated .env file with Google API key")
    print("The system will now use Gemini AI for analysis")
    return True

if __name__ == "__main__":
    update_env_file()
