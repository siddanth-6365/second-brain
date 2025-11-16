#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
VENV_DIR="${SCRIPT_DIR}/.venv"

echo "=========================================="
echo "  Second Brain - Backend Setup"
echo "=========================================="
echo ""

cd "${SCRIPT_DIR}"

echo "Python version: $(python3 --version 2>&1)"
echo ""

if [ ! -d "${VENV_DIR}" ]; then
  echo "Creating virtual environment under backend/.venv ..."
  python3 -m venv "${VENV_DIR}"
else
  echo "✓ Virtual environment already exists (backend/.venv)"
fi

echo ""
echo "Activating virtual environment..."
# shellcheck disable=SC1090
source "${VENV_DIR}/bin/activate"

echo ""
echo "Upgrading pip..."
pip install --upgrade pip

echo ""
echo "Installing backend dependencies..."
pip install -r "${SCRIPT_DIR}/requirements.txt"

ENV_FILE="${SCRIPT_DIR}/.env"

if [ ! -f "${ENV_FILE}" ]; then
  echo ""
  echo "Creating backend/.env (empty template)..."
cat <<'EOF' > "${ENV_FILE}"
# Backend environment variables
QDRANT_HOST=localhost
QDRANT_PORT=6333
# For Qdrant Cloud, comment the host/port above and set one of the following:
# QDRANT_ENDPOINT=https://YOUR-ENDPOINT.aws.cloud.qdrant.io
# QDRANT_CLUSTER_ID=YOUR_CLUSTER_ID
# QDRANT_API_KEY=your_qdrant_api_key

# Supabase credentials
# SUPABASE_URL=
# SUPABASE_ANON_KEY=

# Optional integrations
# GROQ_API_KEY=
EOF
  echo "✓ Created backend/.env. Please update it with real credentials."
else
  echo ""
  echo "✓ backend/.env already exists"
fi

echo ""
echo "Starting (or reusing) Qdrant via docker compose..."
if command -v docker-compose &> /dev/null; then
  (cd "${REPO_ROOT}" && docker-compose up -d)
elif command -v docker &> /dev/null; then
  (cd "${REPO_ROOT}" && docker compose up -d)
else
  echo "⚠ Docker is not installed. Please install Docker to run Qdrant locally."
fi

echo ""
echo "=========================================="
echo "  Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. source backend/.venv/bin/activate"
echo "  2. cd backend"
echo "  3. uvicorn main:app --reload"
echo ""
echo "Docs: http://localhost:8000/docs"
echo "Happy memory building! 🧠"
echo ""

