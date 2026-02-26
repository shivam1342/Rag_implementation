# 🚀 NeuralDocs - Session-Isolated RAG Pipeline

**Production-grade, multi-tenant RAG system with metadata-filtered retrieval and sub-200ms cached responses.**

🌍 **[Live Demo](https://neuraldocs-production.up.railway.app/)** | 📚 **[API Docs](https://neuraldocs-production.up.railway.app/docs)**

---

## 📖 The Problem It Solves

Traditional RAG implementations suffer from **cross-user data leakage**, high cold-start latency, and naive caching that ignores multi-tenancy. This creates security risks in shared environments and poor UX due to 10+ second startup times.

**NeuralDocs** solves this with session-isolated vector retrieval, lazy-loaded models, and session-aware caching.

---

## ⚡ Performance & Scale

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| **Cold Start** | 13s | <1s | **92% faster** |
| **Docker Image** | 8.3GB | 2.0GB | **76% smaller** |
| **Cached Queries** | N/A | <200ms | **10x faster** |
| **User Isolation** | None | Full | **Zero data leakage** |

**Stack:** FastAPI • ChromaDB • Sentence-Transformers • Groq Llama-3.3-70B • Docker • Railway

---

## 🏗️ Architecture

```
Client Request (with session cookie)
         ↓
   FastAPI Router
         ↓
    ┌────┴────┬─────────┬────────┐
    ▼         ▼         ▼        ▼
 Upload   Cache   Embedding   Groq LLM
    │         │         │
    └─────────┴─────────┘
              ↓
        ChromaDB (Session Filter)
        WHERE session_id = X OR is_admin = true
```

**Key Components:**
- **Session Isolation:** UUID cookies + metadata filtering (`session_id` in ChromaDB)
- **Lazy Loading:** Model loads on first query (13s → <1s startup)
- **Session-Aware Cache:** `MD5(query:session_id)` prevents cross-user cache poisoning
- **Async Processing:** Background file uploads prevent timeouts

---

## 🔧 Key Engineering Decisions

### 1. Why Lazy Loading?
**Problem:** Railway kills containers if startup >30s. Model loading took 13s → failed health checks.  
**Solution:** `@property` decorator defers loading to first query.  
**Trade-off:** First request pays 13s vs guaranteed deployment failure.

### 2. Why Session-Aware Caching?
**Problem:** Simple `query → response` cache leaks data between users.  
**Solution:** Cache key = `MD5(query:session_id)`.  
**Result:** Same question returns different answers based on user's documents.

### 3. Why Metadata Filtering Over Separate Collections?
**Problem:** 1000 users = 1000 ChromaDB collections doesn't scale.  
**Solution:** Single collection with `WHERE session_id = X OR is_admin = true`.  
**Result:** Operational simplicity + mathematical isolation guarantee.

---

## 🧗 Challenges Solved

**Challenge 1: Railway Health Check Failures**  
Railway health checks timing out → Lazy loading pattern → <1s startup, 100% pass rate.

**Challenge 2: Cross-User Data Contamination**  
User A retrieving User B's docs → Added `session_id` metadata filtering → Zero leakage.

**Challenge 3: Docker Image OOM Errors**  
8.3GB image causing Railway OOM → CPU-only PyTorch → 2GB image, zero functionality loss.

---

## 🚀 Quick Start

### Docker (Recommended)

```bash
# 1. Clone repository
git clone https://github.com/shivam1342/neuraldocs-rag-system.git
cd neuraldocs-rag-system

# 2. Configure environment
cat > .env << EOF
GROQ_API_KEY=your_groq_api_key_here
ADMIN_PASSWORD=admin123
EOF

# 3. Run
docker-compose up --build

# Access at http://localhost:8000
# API Docs: http://localhost:8000/docs
```

**Get Groq API key:** [console.groq.com](https://console.groq.com/)

---

### Local Python (Alternative)

```bash
# 1. Setup
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 2. Install
pip install -r requirements.txt

# 3. Configure .env with GROQ_API_KEY

# 4. Run
python run.py
```

---

## 📡 API Reference

### Query Documents
```bash
POST /api/query
{"query": "What is RAG?"}

# Returns: answer, source_chunks, response_time_ms
```

### Upload Files
```bash
POST /api/upload
Content-Type: multipart/form-data
file: <document.txt/pdf/docx>
```

### System Stats
```bash
GET /api/health   # Health check
GET /api/stats    # Document count, cache metrics
GET /api/logs     # Query history
```

**Interactive docs:** http://localhost:8000/docs

---

## 🎯 Interview Talking Points

### "How would you scale to 10,000 concurrent users?"
- **Horizontal Scaling:** Stateless FastAPI behind load balancer
- **Distributed Cache:** Migrate to Redis Cluster
- **Vector DB:** Replace ChromaDB with Qdrant/Pinecone (managed, replicated)
- **Storage:** Move uploads to S3 with presigned URLs
- **Auth:** JWT tokens replacing cookie sessions
- **Observability:** Prometheus + Grafana + OpenTelemetry

### "Explain your session isolation"
1. UUID generated on first visit → stored in cookie
2. All document chunks tagged with `session_id` in metadata
3. Vector search filters: `WHERE session_id = X OR is_admin = true`
4. Cache keys include session: `MD5(query:session_id)`

**Security:** ChromaDB metadata filtering provides mathematical isolation—physically impossible to retrieve other users' data.

### "What was the hardest bug you fixed?"
**Bug:** "Connection refused" errors on Railway after deployment.  
**Root Cause:** 13s model loading blocked event loop → health checks failed → container killed.  
**Fix:** Lazy loading with `@property` → app starts <1s, first query pays load time.

---

## ⚙️ Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `GROQ_API_KEY` | *required* | Groq API authentication |
| `CHUNK_SIZE` | `500` | Characters per chunk |
| `CHUNK_OVERLAP` | `100` | 20% overlap for continuity |
| `TOP_K` | `3` | Chunks to retrieve |
| `CACHE_TTL` | `3600` | Cache expiry (seconds) |

---

## 🔮 Future Improvements

- [ ] Redis distributed caching
- [ ] Sentence-aware chunking (respect boundaries)
- [ ] Re-ranking layer (Cohere/CrossEncoder)
- [ ] JWT authentication
- [ ] Prometheus + Grafana monitoring
- [ ] CI/CD with GitHub Actions

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| "Invalid API Key" | Check `.env` has `GROQ_API_KEY` (no quotes/spaces) |
| "No documents found" | Upload via `/api/upload` or admin login |
| Import errors | Activate venv: `venv\Scripts\activate` |
| Port conflict | Change `PORT` in `.env` |

---

## 📊 Skills Demonstrated

**Backend:** FastAPI async, RESTful design, session management, background tasks  
**AI/ML:** RAG pipelines, 384-dim embeddings, semantic search, LLM integration  
**Database:** ChromaDB vector DB, SQLite audit logs, metadata filtering  
**DevOps:** Docker optimization, Railway deployment, health checks  
**System Design:** Clean architecture, caching strategies, multi-tenancy, security

---

## 📚 Documentation

- [STUDY.md](STUDY.md) - Deep dive into RAG concepts and system design
- [ARCHITECTURE.md](ARCHITECTURE.md) - Complete code walkthrough

---

## 👨‍💻 Author

**Shivam Singh** - [GitHub](https://github.com/shivam1342) | [LinkedIn](https://linkedin.com/in/shivam-singh)

*Open to remote AI Engineer and Backend roles. Focused on production ML systems, latency optimization, and scalable architecture.*

---


**⭐ Star this repo if you found it valuable!**
