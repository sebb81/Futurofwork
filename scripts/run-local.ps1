# Launch the previously installed/built workshop without downloading dependencies.
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")
& .venv/Scripts/python.exe -c "import os; from dotenv import load_dotenv; import uvicorn; load_dotenv('.env'); uvicorn.run('work2030.api:app',host=os.getenv('HOST','0.0.0.0'),port=int(os.getenv('PORT','8000')),workers=1)"
