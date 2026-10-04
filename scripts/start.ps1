$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")
if (!(Test-Path ".venv/Scripts/python.exe")) { python -m venv .venv }
& .venv/Scripts/python.exe -m pip install -r requirements.lock
if ($LASTEXITCODE -ne 0) { throw "Installation Python échouée" }
Push-Location frontend
npm ci
if ($LASTEXITCODE -ne 0) { throw "Installation npm échouée" }
npm run build
if ($LASTEXITCODE -ne 0) { throw "Build frontend échoué" }
Pop-Location
if (!(Test-Path ".env")) {
  Copy-Item .env.example .env
  & .venv/Scripts/python.exe -c "from pathlib import Path; import secrets; p=Path('.env'); p.write_text(p.read_text().replace('change-me-before-lan-workshop',secrets.token_urlsafe(18)))"
}
Write-Host "WORK/2030 : http://localhost:8000 ; console : /animateur ; code : ANIMATOR_TOKEN dans .env"
& .venv/Scripts/python.exe -c "import os; from dotenv import load_dotenv; import uvicorn; load_dotenv('.env'); uvicorn.run('work2030.api:app',host=os.getenv('HOST','0.0.0.0'),port=int(os.getenv('PORT','8000')),workers=1)"
