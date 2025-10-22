# Second Brain: Unified Memory Management Platform

Transform messy inputs into intelligent, connected memories with automatic relationship detection and semantic search.

## 🚀 Quick Start

### 1. Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Start Qdrant
docker-compose up -d

# Start API server
uvicorn backend.main:app --reload
```

### 2. Test the System
```bash
# Test with sample data
python test_relationships.py

# Visualize the graph
python visualize_graph.py
```

### 3. Use the API
- **API Docs**: http://localhost:8000/docs
- **Ingest**: `POST /documents/ingest`
- **Search**: `POST /memories/search`
- **Chat**: `POST /chat` (requires Groq API key)

## ✨ Features

- **Document Ingestion**: Text → Chunks → Embeddings → Memories
- **Relationship Detection**: UPDATES, EXTENDS, SIMILAR relationships
- **Semantic Search**: Find memories by meaning, not keywords
- **Chat with Memories**: RAG system using Groq LLM
- **Graph Visualization**: Interactive knowledge graph

## 🧪 Test Scripts

- `test_relationships.py` - Demonstrates relationship detection
- `ingest_sample_data.py` - Ingests personal sample data
- `visualize_graph.py` - Creates interactive graph visualization

## 🔧 Configuration

Create `.env` file:
```bash
QDRANT_HOST=localhost
QDRANT_PORT=6333
GROQ_API_KEY=your_key_here  # Optional, for chat feature
```

## 📊 Example Results

```
✅ Total Memories: 6
✅ Total Relationships: 3
✅ Relationship Types: UPDATES (confidence: 0.96-0.97)
```

Your Second Brain is ready! 🧠

