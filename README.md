# Second Brain: Unified Memory Management Platform

Transform messy inputs into intelligent, connected memories with automatic relationship detection and semantic search.

## 🚀 Quick Start

### 1. Backend Setup
```bash
cd backend
./setup.sh              # creates backend/.venv, installs deps, boots Qdrant
source .venv/bin/activate
uvicorn main:app --reload
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
- **Supabase Auth**: Each memory is scoped to the authenticated Supabase user
- **Persistent Storage**: Keep vectors locally via bind-mounted storage or point to Qdrant Cloud
- **Graph Persistence**: Nodes/edges automatically hydrate from Qdrant so restarts don’t lose context

## 📝 Ingest Options

| Type | Provide | What happens |
|------|---------|--------------|
| `note` | Plain text | Text is chunked, embedded, and enriched with entities & keywords. |
| `link` | URL only | The backend fetches the page, summarizes it via LLM (with fallback if needed), and stores the summary plus link metadata. |
| `file` | PDF / DOCX / TXT | Files are parsed server-side (PyPDF2 / python-docx) and converted into clean, searchable text. |

Every type supports optional `title` and `description`; additional metadata (e.g., `source_url`, `file_name`) is added automatically.

## 🔗 Relationship Types

| Relationship | When it’s created | Example |
|--------------|------------------|---------|
| `updates` | New memory contradicts or supersedes older info, marking the older one as `is_latest = False`. | “You work at Amazon as a Content Engineer” → “You now work at Amazon as the CMO.” |
| `extends` | New memory enriches an existing fact without replacing it. | “You work at Amazon as the CMO” → “Your work covers SEO, campaigns, and documentation quality.” |
| `derives` | The system infers a connection based on shared entities/keywords. | “Siddanth is the founder of AI1” + “Siddanth talks about machine learning” ⇒ “AI1 is likely an AI-focused company.” |

Relationships, like memories, are persisted in Qdrant so the graph survives restarts.

## ⚙️ Processing Pipeline

| Stage | What happens |
|-------|--------------|
| `queued` | Document received and waiting to be processed |
| `extracting` | Content gathered from the note/link/file |
| `chunking` | Semantic chunks created for downstream embeddings |
| `embedding` | Vectors generated via SentenceTransformers |
| `indexing` | Memories stored in Qdrant, relationships detected |
| `done` | Memories are searchable, linked, and hydrated on restart |

## 🔐 Supabase Authentication

- Every API request now requires a Supabase session token in the `Authorization: Bearer <token>` header.
- The frontend automatically signs users in/out and attaches the token to all API calls.
- Memories, graph nodes, and relationships are isolated per `user_id`, so multiple users can safely share a deployment.

## 🧪 Test Scripts

- `test_relationships.py` - Demonstrates relationship detection
- `ingest_sample_data.py` - Ingests personal sample data
- `visualize_graph.py` - Creates interactive graph visualization

## 🔧 Configuration

Create `backend/.env` for the FastAPI service:
```bash
# Qdrant options
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION_NAME=memories
# Optional: connect to Qdrant Cloud (set one of the following)
# QDRANT_ENDPOINT=https://YOUR-ENDPOINT.aws.cloud.qdrant.io
# QDRANT_CLUSTER_ID=your_cluster_id   # builds https://<id>.aws.cloud.qdrant.io
# QDRANT_API_KEY=your_qdrant_api_key

# Supabase Auth (required)
SUPABASE_URL=https://YOUR_PROJECT.supabase.co
SUPABASE_ANON_KEY=your_public_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key  # optional, for future admin tasks

# Optional integrations
GROQ_API_KEY=your_key_here
```

For the Next.js frontend, create `frontend/.env.local`:
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=https://YOUR_PROJECT.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_public_anon_key
```

> 💾 **Persist Qdrant data locally:**  
> The `docker-compose.yml` file now mounts `${QDRANT_STORAGE_PATH:-./qdrant_storage}` into the container.  
> Set `QDRANT_STORAGE_PATH` to an absolute path if you want to store the vector data outside this repository.

### Using Qdrant Cloud

1. Provision a Qdrant Cloud cluster and grab the HTTPS endpoint + API key.
2. Set either `QDRANT_ENDPOINT=https://YOUR-CLUSTER.aws.cloud.qdrant.io` **or** `QDRANT_CLUSTER_ID=YOUR_CLUSTER_ID` plus `QDRANT_API_KEY=...` in `backend/.env`.
3. (Optional) Remove `QDRANT_HOST`/`PORT` when using the hosted URL.
4. Restart the API server – the vector store will automatically connect over TLS.

## 📊 Example Results

```
✅ Total Memories: 6
✅ Total Relationships: 3
✅ Relationship Types: UPDATES (confidence: 0.96-0.97)
```

Your Second Brain is ready! 🧠

