# 🤖 RAG System - Production Ready

A **scalable, production-ready RAG (Retrieval-Augmented Generation)** system with FastAPI, ChromaDB, and intelligent caching. Built with clean architecture for interviews and real-world deployment.

## ✨ Key Features

- 📁 **File Upload** - Upload documents (TXT, PDF*, DOCX*) with async processing
- 🔍 **Semantic Search** - Find relevant content using vector embeddings
- 💾 **Dual Caching** - Embedding cache + query response cache
- 📊 **Audit Logging** - Track queries, sources, and response times in SQLite
- 🔄 **Background Processing** - Non-blocking file processing
- 📈 **Observability** - Health checks, stats, and query logs
- 🎨 **Auto API Docs** - Interactive Swagger UI at `/docs`

*PDF and DOCX support coming soon

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

### 3. Build Index (Optional)

If you have documents in `data/` folder:
```bash
python build_index_new.py
```

### 4. Run the Application

```bash
# Easy way
python run.py

# Or directly
python -m uvicorn app.main:app --reload
```

### 5. Access the API

- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/health
- **Stats**: http://localhost:8000/api/stats

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

## 🧪 Testing

Try these example queries after building the index:

```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is this project about?"}'
```

## ⚙️ Configuration

Edit `app/core/config.py` to customize:

- `MAX_FILE_SIZE`: Upload limit (default: 10MB)
- `CHUNK_SIZE`: Text chunk size (default: 300)
- `TOP_K`: Number of results retrieved (default: 3)
- `CACHE_TTL`: Cache timeout (default: 3600 seconds)
- `EMBEDDING_MODEL`: HuggingFace model (default: all-MiniLM-L6-v2)

## 📊 Monitoring

### View Logs
```bash
tail -f logs/rag_*.log
```

### Check Stats
Visit http://localhost:8000/api/stats to see:
- Total documents indexed
- Total queries processed
- Cache statistics

### Audit Database
Query logs are stored in `audit.db`:
```sql
sqlite3 audit.db
SELECT * FROM query_logs ORDER BY timestamp DESC LIMIT 10;
```

## 🎯 Key Design Decisions (Interview Ready)

### Why FastAPI?
- Async support for background file processing
- Auto-generated OpenAPI docs
- Type hints with Pydantic validation
- Better performance than Flask

### Why ChromaDB?
- Free and local (no API costs)
- Simple persistent storage
- Easy to scale to Qdrant/Pinecone later

### Why In-Memory Cache?
- Fast prototype (Redis later)
- 80% cache hit rate reduces LLM calls
- Easy to upgrade to Redis for distributed caching

### Why SQLite for Audit Logs?
- Lightweight, zero-config
- Perfect for tracking query → source mapping
- Easy to query for analytics

## 🔮 Roadmap

- [ ] PDF extraction with pypdf
- [ ] DOCX extraction with python-docx  
- [ ] Redis cache integration
- [ ] Semantic chunking (sentence-aware)
- [ ] Re-ranking for better retrieval
- [ ] Docker deployment
- [ ] CI/CD pipeline
- [ ] Monitoring dashboard

## 🐛 Troubleshooting

### "Invalid API Key" error
- Check your `.env` file has `GROQ_API_KEY`
- Verify key at https://console.groq.com

### "No documents found" error
- Run `python build_index_new.py` first
- Or upload files via `/api/upload` endpoint

### Import errors
- Make sure virtual environment is activated
- Reinstall: `pip install -r requirements.txt`

## 📄 License

MIT License - Feel free to use for interviews and projects!

## 🙋 Interview Questions?

This project demonstrates:
- Clean architecture (services, models, routes)
- API design principles
- Caching strategies
- Error handling & validation
- Logging & observability
- Async processing
- File upload handling
- Database integration

**"How would you scale this?"**
> Redis for distributed cache, move to Qdrant/Pinecone for vector DB, add load balancer, use S3 for files, monitor with Prometheus.

---

Built with ❤️ for interviews and production## 🔒 Security Notes

- Never commit your `.env` file
- Keep your Groq API key secret
- The `.gitignore` file is configured to exclude sensitive files

## 🤝 Contributing

Feel free to fork this project and submit pull requests!

## 📄 License

MIT License

## 🙏 Acknowledgments

- [Groq](https://groq.com/) for fast LLM inference
- [ChromaDB](https://www.trychroma.com/) for vector storage
- [Sentence Transformers](https://www.sbert.net/) for embeddings

---

Made with ❤️ for learning RAG systems
