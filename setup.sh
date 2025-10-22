#!/bin/bash

echo "=========================================="
echo "  Second Brain - Setup Script"
echo "=========================================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Found Python $python_version"

# Create virtual environment
echo ""
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo ""
    echo "Creating .env file..."
    cp .env.example .env
    echo "✓ Created .env file. Please edit it with your configuration."
else
    echo ""
    echo "✓ .env file already exists"
fi

# Start Qdrant with Docker Compose
echo ""
echo "Starting Qdrant vector database..."
if command -v docker-compose &> /dev/null; then
    docker-compose up -d
    echo "✓ Qdrant started successfully"
elif command -v docker &> /dev/null; then
    docker compose up -d
    echo "✓ Qdrant started successfully"
else
    echo "⚠ Docker not found. Please install Docker to run Qdrant."
    echo "   Or run Qdrant manually with:"
    echo "   docker run -p 6333:6333 -p 6334:6334 -v \$(pwd)/qdrant_storage:/qdrant/storage:z qdrant/qdrant"
fi

echo ""
echo "=========================================="
echo "  Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Activate the virtual environment:"
echo "   source venv/bin/activate"
echo ""
echo "2. Run the test script to see the system in action:"
echo "   python backend/test_system.py"
echo ""
echo "3. Start the API server:"
echo "   python -m uvicorn backend.main:app --reload"
echo ""
echo "4. Access the API documentation:"
echo "   http://localhost:8000/docs"
echo ""
echo "Happy memory building! 🧠"
echo ""

