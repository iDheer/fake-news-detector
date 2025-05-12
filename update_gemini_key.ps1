# Update Gemini API Key - Helper Script
# This script activates your virtual environment and runs the Python script to update the Gemini API key

# Check if virtual environment exists
if (Test-Path -Path ".\venv\Scripts\Activate.ps1") {
    Write-Host "Activating virtual environment..." -ForegroundColor Green
    .\venv\Scripts\Activate
} else {
    Write-Host "Virtual environment not found. Please run fresh_install.ps1 or quick_start.ps1 first" -ForegroundColor Red
    Write-Host "Press any key to exit..." -ForegroundColor Yellow
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}

# Run the Python script to update the API key
Write-Host "Running API key update script..." -ForegroundColor Cyan
python update_gemini_key.py

Write-Host "`nNext steps:" -ForegroundColor White
Write-Host "1. Run 'python run.py' to start the application" -ForegroundColor White
Write-Host "`nThe application will be available at:" -ForegroundColor Green
Write-Host "- Frontend: http://localhost:8501" -ForegroundColor Green
Write-Host "- API Documentation: http://localhost:8000/docs" -ForegroundColor Green

# Keep the terminal window open
Write-Host "`nPress any key to exit..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
