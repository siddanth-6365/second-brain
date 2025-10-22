# Quick Start Guide

## Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start Qdrant
docker-compose up -d

# 3. Start API server
uvicorn backend.main:app --reload
```

## Test the System

```bash
# Test relationship detection
python test_relationships.py

# Visualize the graph
python visualize_graph.py
```

## API Usage

### Ingest Document
```bash
curl -X POST "http://localhost:8000/documents/ingest" \
  -H "Content-Type: application/json" \
  -d '{"content": "Your text here", "title": "Title"}'
```

### Search Memories
```bash
curl -X POST "http://localhost:8000/memories/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "Your question", "limit": 5}'
```

### Chat with Memories (Optional)
```bash
# Add GROQ_API_KEY to .env first
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"question": "What are my hobbies?"}'
```

## Configuration

Create `.env`:
```bash
QDRANT_HOST=localhost
QDRANT_PORT=6333
GROQ_API_KEY=your_key_here  # Optional
```

## Troubleshooting

- **Qdrant not running**: `docker-compose up -d`
- **Module errors**: `pip install -r requirements.txt`
- **API docs**: http://localhost:8000/docs