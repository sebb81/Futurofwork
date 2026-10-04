#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ ! -x .venv/bin/python ]]; then
  python3 -m venv .venv
fi
if [[ ! -f .venv/.work2030-installed ]] || [[ requirements.lock -nt .venv/.work2030-installed ]]; then
  .venv/bin/python -m pip install -r requirements.lock
  touch .venv/.work2030-installed
fi
if [[ ! -d frontend/node_modules ]] || [[ frontend/package-lock.json -nt frontend/node_modules/.package-lock.json ]]; then
  (cd frontend && npm ci)
fi
# Build once if missing/stale; launches after preparation work with no Internet access.
if [[ ! -f frontend/dist/index.html ]] || [[ -n "$(find frontend/src frontend/index.html frontend/vite.config.ts -newer frontend/dist/index.html -print -quit)" ]]; then
  (cd frontend && npm run build)
fi
if [[ ! -f .env ]]; then
  cp .env.example .env
  .venv/bin/python - <<'PY'
from pathlib import Path
import secrets
p=Path('.env');s=p.read_text().replace('change-me-before-lan-workshop', secrets.token_urlsafe(18));p.write_text(s)
PY
  echo 'Configuration créée dans .env. Le code animateur est ANIMATOR_TOKEN.'
fi
echo 'WORK/2030 : http://localhost:8000 · console : /animateur · cartes : /cartes'
exec .venv/bin/python - <<'PY'
import os
from dotenv import load_dotenv
import uvicorn
load_dotenv('.env')
uvicorn.run('work2030.api:app',host=os.getenv('HOST','0.0.0.0'),port=int(os.getenv('PORT','8000')),workers=1)
PY
