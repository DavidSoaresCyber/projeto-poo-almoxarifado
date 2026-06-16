#!/usr/bin/env bash
# Inicia o Moranguinho Stock Manager
cd "$(dirname "$0")/backend" || exit 1

if [ ! -d "venv" ]; then
  echo "Criando ambiente virtual..."
  python3 -m venv venv
  source venv/bin/activate
  pip install -r requirements.txt
else
  source venv/bin/activate
fi

[ -f .env ] || cp .env.example .env 2>/dev/null

echo ""
echo "  Moranguinho Stock Manager"
echo "  Acesse: http://localhost:8000"
echo ""

python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
