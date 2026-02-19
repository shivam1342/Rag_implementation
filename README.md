# 🤖 NeuralDocs - Production RAG System

A **scalable, multi-user RAG (Retrieval-Augmented Generation)** system with session isolation, intelligent caching, and production-grade architecture.

🌍 **[Live Demo](https://neuraldocs-production.up.railway.app/)** | 📚 **[API Docs](https://neuraldocs-production.up.railway.app/docs)** | 🐙 **[GitHub](https://github.com/shivam1342/neuraldocs-rag-system)**

## 🎯 Executive Summary

Production-ready RAG system featuring **session-isolated multi-user architecture** with metadata-filtered vector retrieval. Deployed on Railway with optimized Docker image (76% size reduction), lazy-loaded embeddings (92% startup improvement), and dual-tier caching for sub-200ms cached responses.

**Key Metrics:**
- ⚡ **<1s startup** (lazy loading: 13s → <1s)
- 🐳 **2GB Docker image** (optimized from 8.3GB, CPU-only PyTorch)
- 💾 **<200ms cached queries** (session-aware caching with hit rate tracking)
- 👥 **Multi-user isolation** (cookie-based sessions with metadata filtering)
- 🧹 **Auto-cleanup** (1,186 expired documents removed on deployment)

**Tech Stack:** FastAPI • ChromaDB • Sentence-Transformers • Groq LLaMA-3.3-70B • Docker • Railway

---

## ✨ Core Features

- 📁 **Multi-Format Upload** - Upload TXT, PDF, DOCX with async processing
- 🔍 **Semantic Search** - Find relevant content using vector embeddings
- 👥 **Multi-User Sessions** - Session-based isolation with admin persistent storage
- 💾 **Smart Caching** - Embedding cache + query response cache with hit/miss metrics
- 📊 **Audit Logging** - Track queries, sources, and response times in SQLite
- 🔄 **Background Processing** - Non-blocking file processing
- 📈 **Observability** - Health checks, stats, cache metrics, and query logs
- 🎨 **Auto API Docs** - Interactive Swagger UI at `/docs`
- 🐳 **Docker Ready** - Full containerization with docker-compose

## 🏗️ Architecture

```
┌─────────────┐
│   FastAPI   │ ← REST API Layer
└──────┬──────┘
       │
   ┌───┴────┬─────────┬──────────┬─────────┐
   │        │         │          │         │
┌──▼───┐ ┌─▼────┐ ┌──▼──────┐ ┌─▼──────┐ ┌▼────────┐
│Upload│ │Cache │ │Embedding│ │Vector  │ │LLM      │
│Svc   │ │Svc   │ │Service  │ │DB      │ │Service  │
└──────┘ └──────┘ └─────────┘ └────────┘ └─────────┘
   │        │         │          │         │
   └────────┴─────────┴──────────┴─────────┘
                     │
              ┌──────▼──────┐
              │ Audit Log   │
              │  (SQLite)   │
              └─────────────┘
```

## 📁 Project Structure

```
Rag/
├── app/
│   ├── main.py                    # FastAPI app entry
│   ├── api/
│   │   └── routes/
│   │       ├── query.py           # POST /api/query
│   │       ├── upload.py          # POST /api/upload
│   │       └── admin.py           # GET /api/health, /api/stats
│   ├── services/
│   │   ├── embedding_service.py   # Text → embeddings
│   │   ├── vector_service.py      # ChromaDB operations
│   │   ├── llm_service.py         # Groq API
│   │   ├── cache_service.py       # In-memory cache
│   │   └── document_service.py    # File processing
│   ├── models/
│   │   ├── schemas.py             # Pydantic models
│   │   └── database.py            # SQLite audit log
│   ├── core/
│   │   ├── config.py              # Settings & config
│   │   └── logger.py              # Logging setup
│   └── utils/
│       ├── chunking.py            # Text chunking
│       └── validators.py          # File validation
├── uploads/                       # Uploaded files
├── chroma_store/                  # Vector DB
├── logs/                          # Application logs
├── audit.db                       # SQLite audit log
├── requirements.txt
├── .env                           # Environment variables
├── run.py                         # Easy startup script
└── README.md

```

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Clone the repo
cd Rag

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure

Create `.env` file:
```
GROQ_API_KEY=your_groq_api_key_here
```

Get your API key from [Groq Console](https://console.groq.com/)

### 3. Run the Application

#### Option A: Local Development

```bash
# Easy way
python run.py

# Or directly
python -m uvicorn app.main:app --reload
```

#### Option B: Docker (Recommended)

```bash
# Copy environment file
cp .env.example .env
# Edit .env with your GROQ_API_KEY

# Build and run
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### 4. Access the Application

- **Web UI**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/health
- **Stats**: http://localhost:8000/api/stats

### 5. Admin Features

1. Click "Admin Login" in the web UI
2. Enter password (default: `admin123`, change via `ADMIN_PASSWORD` env var)
3. Upload documents as admin → they persist forever
4. Regular users get temporary sessions (auto-cleanup)

## 📡 API Endpoints

### Query

```bash
POST /api/query
{
  "query": "What is RAG?"
}

Response:
{
  "answer": "...",
  "source_chunks": ["...", "..."],
  "chunk_ids": ["chunk_1", "chunk_2"],
  "response_time_ms": 234
}
```

### Upload File

```bash
POST /api/upload
Content-Type: multipart/form-data

file: <your_file.txt>

Response:
{
  "success": true,
  "message": "File uploaded successfully",
  "filename": "your_file.txt"
}
```

### Health Check

```bash
GET /api/health

Response:
{
  "status": "healthy",
  "version": "2.0.0",
  "documents_indexed": 42
}
```

### Get Logs

```bash
GET /api/logs?limit=10

Response:
{
  "logs": [...],
  "count": 10
}
```

## 🧪 Quick Test

```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is this project about?"}'
```

## ⚙️ Configuration

Key settings in `app/core/config.py`: `MAX_FILE_SIZE` (10MB), `CHUNK_SIZE` (300), `TOP_K` (3), `CACHE_TTL` (3600s), `EMBEDDING_MODEL` (all-MiniLM-L6-v2)

## 📊 Monitoring

**Logs:** `tail -f logs/rag_*.log`  
**Stats:** http://localhost:8000/api/stats (docs count, queries, cache metrics)  
**Audit DB:** `sqlite3 audit.db` → Query `query_logs` table for full history

## 🎯 Architecture Decisions (Interview Ready)

**Clean Architecture:** Services layer (embedding, vector, LLM, cache, document) → API routes → FastAPI app  
**Multi-User Isolation:** Cookie-based sessions + metadata filtering (`session_id OR is_admin=true`)  
**Performance:** Lazy loading (13s→<1s), dual-tier caching (embedding + query response), background file processing  
**Scalability:** ChromaDB (local MVP) → Easily migrate to Qdrant/Pinecone/Weaviate for production scale

### Interview Q&A

**"How would you scale this?"**
> Redis for distributed cache, Qdrant/Pinecone for vector DB, S3 for file storage, JWT auth, rate limiting, Prometheus/Grafana monitoring, Kubernetes orchestration, CDN for static assets.

**"How do you handle multiple users?"**
> Session-based isolation with UUID cookies. Admin uploads persist forever (`is_admin=true`), user uploads are session-scoped. Vector search filters by `session_id OR is_admin=true` in ChromaDB metadata, ensuring zero cross-user data leakage.

**"Why lazy loading for embeddings?"**
> Railway health checks timeout if startup >30s. Original model loading took 13s, failing health checks. Lazy loading defers to first query, enabling <1s startup and reliable deployments. One-time 13s delay acceptable vs deployment failure.

**"Explain the caching strategy"**
> Two-tier: (1) Embedding cache (avoid re-encoding same text), (2) Query response cache with session isolation (MD5 hash of `query:session_id`). Track hit/miss metrics for optimization insights. In-memory for MVP, Redis for production horizontal scaling.

---

## 📊 Skills Demonstrated

- **Backend:** RESTful API design, async processing, file handling (multipart/form-data)
- **AI/ML:** RAG pipelines, vector embeddings (384-dim), semantic search, LLM integration
- **Database:** ChromaDB (vector DB), SQLite (audit logs), persistent storage strategies
- **DevOps:** Docker optimization (8.3GB→2GB), Railway deployment, environment management
- **Architecture:** Clean architecture, service layer pattern, session management, caching strategies
- **Production:** Health checks, monitoring, logging, error handling, security (session isolation)

---

## 📄 License

MIT License

---

**Built by [Shivam Singh](https://github.com/shivam1342)** | Open for interviews and collaborations

## 🚀 Deployment

**Railway (Current Production):**
```bash
# Push to GitHub, connect repo on railway.app
# Set env vars: GROQ_API_KEY, ADMIN_PASSWORD
# Auto-deploys from main branch
```

**Docker Anywhere:**
```bash
docker-compose up -d
# Edit .env with your GROQ_API_KEY first
```

**Key optimizations:** Dynamic PORT binding, lazy model loading for health checks, CPU-only PyTorch build

## 🔮 Roadmap

- [x] PDF extraction with pypdf
- [x] DOCX extraction with python-docx  
- [x] Session-based multi-user isolation
- [x] Cache hit/miss metrics
- [x] Docker deployment
- [ ] Redis cache integration
- [ ] Semantic chunking (sentence-aware)
- [ ] Re-ranking for better retrieval
- [ ] CI/CD pipeline
- [ ] Monitoring dashboard

## 🐛 Common Issues

**"Invalid API Key"** → Check `.env` has `GROQ_API_KEY` (no spaces, no quotes)  
**"No documents found"** → Upload files via `/api/upload` or login as admin  
**Import errors** → Activate venv: `source venv/bin/activate` (Linux/Mac) or `venv\Scripts\activate` (Windows)

---

## 🎯 Architecture Decisions (Interview Ready)

**Clean Architecture:** Services layer (embedding, vector, LLM, cache, document) → API routes → FastAPI app  
**Multi-User Isolation:** Cookie-based sessions + metadata filtering (`session_id OR is_admin=true`)  
**Performance:** Lazy loading (13s→<1s), dual-tier caching (embedding + query response), background file processing  
**Scalability:** ChromaDB (local MVP) → Easily migrate to Qdrant/Pinecone/Weaviate for production scale

### Interview Q&A

**"How would you scale this?"**
> Redis for distributed cache, Qdrant/Pinecone for vector DB, S3 for file storage, JWT auth, rate limiting, Prometheus/Grafana monitoring, Kubernetes orchestration, CDN for static assets.

**"How do you handle multiple users?"**
> Session-based isolation with UUID cookies. Admin uploads persist forever (`is_admin=true`), user uploads are session-scoped. Vector search filters by `session_id OR is_admin=true` in ChromaDB metadata, ensuring zero cross-user data leakage.

**"Why lazy loading for embeddings?"**
> Railway health checks timeout if startup >30s. Original model loading took 13s, failing health checks. Lazy loading defers to first query, enabling <1s startup and reliable deployments. One-time 13s delay acceptable vs deployment failure.

**"Explain the caching strategy"**
> Two-tier: (1) Embedding cache (avoid re-encoding same text), (2) Query response cache with session isolation (MD5 hash of `query:session_id`). Track hit/miss metrics for optimization insights. In-memory for MVP, Redis for production horizontal scaling.

---

## 📊 Skills Demonstrated

- **Backend:** RESTful API design, async processing, file handling (multipart/form-data)
- **AI/ML:** RAG pipelines, vector embeddings (384-dim), semantic search, LLM integration
- **Database:** ChromaDB (vector DB), SQLite (audit logs), persistent storage strategies
- **DevOps:** Docker optimization (8.3GB→2GB), Railway deployment, environment management
- **Architecture:** Clean architecture, service layer pattern, session management, caching strategies
- **Production:** Health checks, monitoring, logging, error handling, security (session isolation)

---

## 📄 License

MIT License

---

**Built by [Shivam Singh](https://github.com/shivam1342)** | Open for interviews and collaborations
