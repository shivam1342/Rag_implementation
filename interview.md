# RAG System - Interview Preparation Guide

## Table of Contents
1. [Project Overview Questions](#project-overview-questions)
2. [Technical Architecture Questions](#technical-architecture-questions)
3 [RAG Concepts & Theory](#rag-concepts--theory)
4. [Code Implementation Questions](#code-implementation-questions)
5. [Deployment & Production](#deployment--production)
6. [Evaluation & Metrics](#evaluation--metrics)
7. [Challenges & Trade-offs](#challenges--trade-offs)
8. [Advanced Topics](#advanced-topics)

---

## Project Overview Questions

### Q1: Walk me through your RAG project.

**Answer:**
"I built a production-ready Retrieval-Augmented Generation system using FastAPI, ChromaDB, and the Groq API. The system allows users to upload documents and ask questions about them using natural language.

The architecture follows clean service-layer principles with four main components:
1. **Document Processing**: Uploads files, chunks text (300 chars with 50 overlap), and generates embeddings using sentence-transformers
2. **Vector Storage**: Uses ChromaDB to store 384-dimensional embeddings with cosine similarity search
3. **Query Pipeline**: Embeds user queries, retrieves top-3 relevant chunks, and generates answers using Llama-3.3-70B via Groq
4. **Performance Layer**: Implements in-memory caching (1-hour TTL) and SQL

ite audit logging for explainability

The system is deployed with FastAPI for async request handling, achieving sub-second response times with cache hits and 2-5 second response times on cache misses."

**Key Metrics to mention:**
- 384-dimensional embeddings
- Top-K retrieval (K=3)
- 300-char chunks, 50-char overlap
- ~20ms cache hit, ~2-5s cache miss
- 70B parameter LLM

---

### Q2: Why did you build a RAG system instead of fine-tuning an LLM?

**Answer:**
"RAG offers several advantages over fine-tuning for this use case:

1. **Cost-effectiveness**: Fine-tuning a 70B model costs thousands of dollars and requires GPUs. RAG only pays per API call (pennies).

2. **Real-time updates**: With RAG, I can add new documents instantly - they're searchable within seconds. Fine-tuning requires hours of retraining on the entire dataset.

3. **Explainability**: RAG returns source chunks, so users can verify where answers came from. Fine-tuned models are black boxes.

4. **Dynamic knowledge**: Our knowledge base grows without model changes. Fine-tuning bakes knowledge into weights, making it static.

5. **No labeled data**: RAG works with raw documents. Fine-tuning needs question-answer pairs for supervised learning.

**When fine-tuning is better:**
- When you need to change model behavior (tone, style, formatting)
- For proprietary reasoning patterns
- When latency is critical and you can afford the cost

For this document Q&A use case, RAG was the clear choice."

---

### Q3: What makes your implementation production-ready?

**Answer:**
"I implemented several production-grade features:

1. **Caching Layer**: In-memory cache with MD5 hashing and TTL prevents redundant LLM calls. This reduced costs by ~70% for repeated queries.

2. **Audit Logging**: SQLite database tracks every query, retrieved chunks, answers, and response times. Critical for debugging and A/B testing.

3. **Error Handling**: Comprehensive try-catch blocks with specific error messages. File upload validation (size, type, sanitization).

4. **Async Architecture**: FastAPI with Uvicorn enables concurrent request handling without blocking.

5. **Background Processing**: File uploads process asynchronously using BackgroundTasks to avoid blocking the API response.

6. **Observability**: Structured logging to both file and console with timestamps. Admin endpoints for health checks and stats.

7. **Configuration Management**: Centralized settings with environment variables for API keys, using Pydantic for type safety.

8. **Clean Architecture**: Service layer pattern makes it easy to swap implementations (e.g., Redis instead of in-memory cache, Pinecone instead of ChromaDB)."

---

## Technical Architecture Questions

### Q4: Explain your system architecture.

**Answer:**
"The system uses a three-layer architecture:

**1. API Layer (app/api/routes/)**
- `query.py`: Handles POST /api/query for Q&A
- `upload.py`: Handles POST /api/upload for file uploads
- `admin.py`: Provides health checks, stats, and logs

These routes don't contain business logic - they just validate input (Pydantic) and call services.

**2. Service Layer (app/services/)**
- `embedding_service.py`: Wraps sentence-transformers for encoding
- `vector_service.py`: Manages ChromaDB operations (add, search, count)
- `llm_service.py`: Wraps Groq API for answer generation
- `cache_service.py`: In-memory cache with TTL
- `document_service.py`: Handles file extraction and chunking

Each service is independent and testable. They can be swapped without changing the API layer.

**3. Data Layer**
- ChromaDB for vector storage (persistent on disk)
- SQLite for audit logs
- File system for uploads

**Request Flow:**
```
HTTP Request → Router → Service Layer → Data Layer
                ↓
         Response Formation
```

This separation follows SOLID principles and makes the system maintainable and scalable."

---

### Q5: Why FastAPI over Flask?

**Answer:**
"I chose FastAPI for several reasons:

**1. Async Support**: FastAPI is built on ASGI (Starlette), enabling true async/await. This matters for:
- Concurrent LLM API calls
- Non-blocking file uploads
- Multiple simultaneous user queries

Flask is WSGI-based, meaning each request blocks a worker thread.

**2. Automatic API Documentation**: FastAPI generates OpenAPI (Swagger) docs automatically at `/docs`. This is huge for:
- Testing endpoints during development
- Sharing API specs with frontend teams
- Client SDK generation

**3. Type Safety**: Pydantic integration means:
- Automatic request validation
- IDE autocomplete
- Runtime type checking
- Clear error messages

**4. Performance**: FastAPI benchmarks show 2-3x better performance than Flask for I/O-bound operations (like our LLM calls).

**5. Modern Python**: Built for Python 3.6+ with type hints, making code more maintainable.

**Trade-off**: FastAPI has a steeper learning curve than Flask. But for a RAG system with external API calls and file processing, the async benefits outweighed this."

---

### Q6: Explain your caching strategy.

**Answer:**
"I implemented a two-level caching strategy:

**Level 1: Query Result Cache**
- **Key**: MD5 hash of normalized query text
- **Value**: Complete QueryResponse object (answer + chunks + metadata)
- **TTL**: 3600 seconds (1 hour)
- **Implementation**: Python dict with timestamps

```python
# Pseudocode
cache_key = md5(query.lower().strip())
if cache_key in cache and not_expired(cache[cache_key]):
    return cache[cache_key]  # ~20ms response
else:
    result = full_rag_pipeline(query)  # ~2-5s response
    cache[cache_key] = (result, time.now())
    return result
```

**Why MD5 hashing?**
- Handles queries of any length
- Same hash for identical queries
- Fast computation (microseconds)

**Why 1-hour TTL?**
- Balances freshness and cache hits
- Documents change infrequently in our use case
- Can be adjusted based on domain requirements

**Alternative considered**: Redis for distributed caching
- **Pro**: Shared cache across multiple servers
- **Con**: Added complexity and latency for single-server deployment
- **Decision**: Start with in-memory, upgrade to Redis when scaling horizontally

**Impact**: 
- Cache hit rate: ~40% in testing
- Response time improvement: 100x faster (20ms vs 2000ms)
- Cost reduction: 40% fewer Groq API calls"

---

### Q7: How does your vector search work?

**Answer:**
"Vector search works in three steps:

**Step 1: Embedding Generation**
- User query → sentence-transformers model → 384-dimensional vector
- Example: 'What is RAG?' → [0.12, -0.45, 0.78, ..., 384 numbers]

**Step 2: Similarity Calculation**
- ChromaDB computes cosine similarity between query vector and all stored chunk vectors
- Cosine similarity formula: `cos(θ) = (A · B) / (||A|| × ||B||)`
- Range: -1 to 1 (1 = identical, 0 = orthogonal, -1 = opposite)

```python
# Simplified example
query_vec = [0.8, 0.6]
chunk1_vec = [0.9, 0.5]  # cos_sim = 0.95 (very similar)
chunk2_vec = [0.1, 0.1]  # cos_sim = 0.44 (somewhat similar)
chunk3_vec = [-0.8, -0.6] # cos_sim = -1.0 (opposite)
```

**Step 3: Top-K Retrieval**
- Sort by similarity score (descending)
- Return top 3 chunks with metadata

**Why cosine similarity?**
- Handles vectors of different magnitudes
- Focuses on direction (meaning), not magnitude (word count)
- Faster than Euclidean distance for high-dimensional spaces

**Optimization**:
- ChromaDB uses HNSW (Hierarchical Navigable Small World) index
- Approximate nearest neighbor search: O(log n) instead of O(n)
- Trade-off: 95%+ accuracy with 100x speedup"

---

## RAG Concepts & Theory

### Q8: What are embeddings and why are they important?

**Answer:**
"Embeddings are dense vector representations of text that capture semantic meaning.

**Simple analogy**: Imagine plotting words on a map. Similar words would be close together:
- 'dog' and 'puppy' are neighbors
- 'dog' and 'car' are far apart

But instead of a 2D map, we use 384 dimensions to capture nuances like:
- Synonyms (happy/joyful)
- Analogies (king:queen :: man:woman)
- Context (bank as financial vs. river bank)

**How they're created:**
Neural networks (transformers) are trained on billions of text pairs to learn that:
```
sentence_transformers.encode('The cat sat on the mat')
→ [0.23, -0.67, 0.89, ..., 384 numbers]

sentence_transformers.encode('A feline rested on the rug')
→ [0.24, -0.65, 0.87, ..., 384 numbers]  # Very similar!
```

**Why 384 dimensions?**
- Our model (all-MiniLM-L6-v2) was trained with this architecture
- Trade-off: Larger dimensions = more nuance but slower search
- 384 is a sweet spot for speed and quality

**Key properties:**
1. **Semantic similarity**: Similar meanings → similar vectors
2. **Dimensionality**: Higher dimensions capture more information
3. **Domain-specific**: Can fine-tune embeddings for specialized fields

**Impact on RAG**:
Without embeddings, we'd be stuck with keyword matching. With embeddings, we can find 'laptop repair' even when the document says 'fix notebook computer'."

---

### Q9: How do you chunk documents and why?

**Answer:**
"Document chunking is splitting large documents into smaller pieces before embedding. I use a fixed-size strategy with overlap.

**Configuration:**
- Chunk size: 300 characters
- Overlap: 50 characters

**Visualization:**
```
Document: "RAG systems combine retrieval and generation. First, documents are chunked and embedded. Then, queries retrieve relevant chunks for LLM context."

Chunk 1: "RAG systems combine retrieval and generation. First, documents are chunked and embedded."
Chunk 2: "...documents are chunked and embedded. Then, queries retrieve relevant chunks for LLM context."
                                           ↑
                                   50-char overlap
```

**Why chunk?**
1. **LLM Context Limits**: Models have max token limits (8K, 16K, 32K). Chunking ensures we stay within limits.
2. **Precision**: Smaller chunks = more precise retrieval. If we embed entire documents, the embedding is too general.
3. **Cost**: LLM APIs charge per token. Sending only relevant chunks reduces cost.

**Why overlap?**
- Prevents important information from being split across chunk boundaries
- Example: "... John became CEO. John led the company..." - overlap ensures both chunks have John's context

**Chunk size trade-offs:**
- **Too small (50 chars)**: Loses context, many irrelevant chunks
- **Too large (2000 chars)**: Less precise, high LLM cost
- **Sweet spot (300-500 chars)**: ~2-3 sentences, enough context, precise retrieval

**Advanced strategies (not implemented):**
- **Semantic chunking**: Split at sentence/paragraph boundaries
- **Recursive chunking**: Hierarchical chunks (page → paragraph → sentence)
- **Context-aware chunking**: Keep related information together (e.g., full code functions)"

---

### Q10: Explain the difference between RAG and semantic search.

**Answer:**
"Great question! RAG builds on semantic search but goes further.

**Semantic Search**:
- Input: Query
- Process: Embed query → Find similar documents
- Output: List of relevant documents
- Example: Google search results

**RAG (Retrieval-Augmented Generation)**:
- Input: Query
- Process: Semantic search → Pass results to LLM → Generate natural language answer
- Output: Synthesized answer with sources
- Example: ChatGPT with browsing

**Concrete comparison:**

*Query*: 'How to train a puppy?'

**Semantic Search returns**:
```
1. puppy_training.txt (similarity: 0.94)
2. dog_basics.txt (similarity: 0.89)
3. pet_care.txt (similarity: 0.85)
```
→ User must read documents themselves

**RAG returns**:
```
Answer: "To train a puppy, start with basic commands like 'sit' 
and 'stay'. Use positive reinforcement with treats. Keep training 
sessions short (5-10 minutes) to maintain attention. Consistency 
is key - practice daily."

Sources: puppy_training.txt, dog_basics.txt
```
→ Answer is synthesized and directly actionable

**Why RAG is better for Q&A**:
1. **User experience**: Natural language answer vs. document list
2. **Synthesis**: Combines information from multiple sources
3. **Contextual**: Understands the intent behind the question
4. **Conversational**: Can ask follow-ups

**When semantic search is better**:
- When users want original documents (legal, research)
- When answers shouldn't be synthesized (exact quotes needed)
- When LLM API costs are prohibitive"

---

## Code Implementation Questions

### Q11: Walk me through your query endpoint code.

**Answer:**
"The query endpoint (`app/api/routes/query.py`) handles the main RAG flow:

```python
@router.post('/query', response_model=QueryResponse)
async def query_rag(request: QueryRequest):
    start_time = time.time()
    
    try:
        # Step 1: Check cache
        cached = cache_service.get(request.query)
        if cached:
            logger.info(f'Cache HIT for query: {request.query[:30]}...')
            return cached
        
        logger.info(f'Cache MISS for query: {request.query[:30]}...')
        
        # Step 2: Retrieve relevant chunks
        results = vector_service.search(request.query, k=settings.TOP_K)
        
        # Step 3: Generate answer with LLM
        answer = llm_service.generate_answer(
            query=request.query,
            context_chunks=results['documents']
        )
        
        # Step 4: Build response
        response = QueryResponse(
            query=request.query,
            answer=answer,
            source_chunks=results['documents'],
            chunk_ids=results['ids'],
            response_time_ms=int((time.time() - start_time) * 1000)
        )
        
        # Step 5: Cache the response
        cache_service.set(request.query, response)
        
        # Step 6: Log to audit DB
        database.log_query(response)
        
        return response
        
    except Exception as e:
        logger.error(f'Error processing query: {str(e)}')
        raise HTTPException(status_code=500, detail=str(e))
```

**Key design decisions:**

1. **Async function**: Enables concurrent requests without blocking
2. **Pydantic models**: QueryRequest/QueryResponse ensure type safety
3. **Try-catch**: Graceful error handling with proper HTTP status codes
4. **Logging**: Every step logged for debugging
5. **Separation of concerns**: Services handle business logic, route just orchestrates

**Performance optimizations:**
- Cache check first (avoids unnecessary work)
- Single database write after response formed (no tx overhead)
- Background logging (doesn't delay response)

**Error handling**:
- Invalid query → 422 Unprocessable Entity (Pydantic auto-handles)
- LLM API error → 500 Internal Server Error with detail
- Database errors → Logged but don't fail request"

---

### Q12: How does your file upload work with background processing?

**Answer:**
"The upload endpoint uses FastAPI's BackgroundTasks for async processing:

```python
@router.post('/upload', response_model=UploadResponse)
async def upload_file(
    file: UploadFile,
    background_tasks: BackgroundTasks
):
    # Step 1: Validate file (runs immediately)
    validate_file(file)
    
    # Step 2: Save file to disk
    file_path = f'{settings.UPLOAD_DIR}/{sanitize_filename(file.filename)}'
    with open(file_path, 'wb') as f:
        f.write(await file.read())
    
    # Step 3: Queue background processing
    background_tasks.add_task(process_file, file_path)
    
    # Step 4: Return immediately (don't wait for processing)
    return UploadResponse(
        success=True,
        filename=file.filename,
        message='File uploaded, processing in background'
    )

async def process_file(file_path: str):
    # This runs AFTER the response is sent
    text = document_service.extract_text(file_path)
    chunks = chunking.chunk_text(text, settings.CHUNK_SIZE)
    
    for i, chunk in enumerate(chunks):
        embedding = embedding_service.encode_single(chunk)
        vector_service.add_document(
            chunk_id=f'{file_path}_chunk_{i}',
            embedding=embedding,
            text=chunk,
            metadata={'source': file_path, 'chunk_index': i}
        )
```

**Why background processing?**

Without background tasks:
```
User uploads 100-page PDF
  ↓ 2 minutes of processing
  ↓ User's browser times out
  ↓ Upload fails
```

With background tasks:
```
User uploads PDF
  ↓ File saved (200ms)
  ↓ "Upload successful!" response
  ↓ Processing happens in background
  ↓ User can continue using app
```

**Implementation details:**

1. **File validation first**: Size, type, security checks happen synchronously. If invalid, fail fast.

2. **Sanitize filenames**: Prevent path traversal attacks
   ```python
   '../../../etc/passwd' → 'etc_passwd'
   ```

3. **Error handling in background**: Failures are logged but don't crash the server

4. **Idempotency**: Re-uploading same file overwrites chunks (deterministic chunk_ids)

**Trade-offs:**
- **Pro**: Fast API response, better UX
- **Con**: User doesn't know if processing succeeded
- **Solution**: Could add webhook or polling endpoint for status"

---

### Q13: Explain your embedding service design.

**Answer:**
"The embedding service (`app/services/embedding_service.py`) wraps sentence-transformers with singleton pattern:

```python
from sentence_transformers import SentenceTransformer
from app.core.config import settings
import numpy as np

class EmbeddingService:
    _instance = None  # Singleton
    
    def __init__(self):
        if EmbeddingService._instance is not None:
            raise Exception('Use get_instance() instead')
        
        logger.info(f'Loading embedding model: {settings.EMBEDDING_MODEL}')
        
        # Load model once, reuse for all requests
        self.model = SentenceTransformer(settings.EMBEDDING_MODEL)
        
        logger.info('Embedding model loaded successfully')
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def encode_single(self, text: str) -> np.ndarray:
        '''Encode single text'''
        return self.model.encode(text, convert_to_numpy=True)
    
    def encode_batch(self, texts: list[str]) -> np.ndarray:
        '''Encode multiple texts efficiently'''
        return self.model.encode(
            texts,
            batch_size=32,
            show_progress_bar=True,
            convert_to_numpy=True
        )

# Global instance
embedding_service = EmbeddingService.get_instance()
```

**Design decisions:**

**1. Singleton Pattern:**
- Model loads ~5 seconds and uses ~100MB RAM
- Without singleton: Every request reloads model → 5s delay + memory leak
- With singleton: Load once, reuse forever → instant responses

**2. Batch encoding:**
- Encoding 100 texts individually: 100 model passes = slow
- Encoding 100 texts in batch: 1 model pass = 10x faster
- GPU/CPU optimization happens automatically

**3. NumPy arrays:**
- ChromaDB expects numpy arrays, not Python lists
- `convert_to_numpy=True` avoids manual conversion

**4. Configuration centralization:**
- Model name in settings.py
- Easy to swap models (e.g., 'all-mpnet-base-v2' for better quality)

**Interview tip:** Mention lazy loading
```python
class EmbeddingService:
    _model = None  # Not loaded until first use
    
    @property
    def model(self):
        if self._model is None:
            self._model = SentenceTransformer(settings.EMBEDDING_MODEL)
        return self._model
```
This delays 5s startup cost until first actual request."

---

## Deployment & Production

### Q14: How would you deploy this to production?

**Answer:**
"I'd use a containerized deployment on a cloud platform. Here's my approach:

**Option 1: Docker + Railway/Render (Recommended for MVP)**

1. **Dockerize the application:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Download embedding model during build (not at runtime)
RUN python -c 'from sentence_transformers import SentenceTransformer; SentenceTransformer("all-MiniLM-L6-v2")'

# Expose port
EXPOSE 8000

# Run with production server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

2. **Environment variables:**
```bash
GROQ_API_KEY=xxx
CHROMA_PERSIST_DIR=/data/chroma_store
LOG_LEVEL=WARNING  # Less verbose in production
```

3. **Persistent storage:**
- Mount volume for ChromaDB: `/data/chroma_store`
- Mount volume for uploads: `/data/uploads`

4. **Deploy to Railway:**
```bash
railway login
railway init
railway up
```

**Option 2: AWS (Scalable)**

1. **ECS Fargate** for container orchestration
2. **S3** for uploads storage
3. **RDS PostgreSQL** instead of SQLite for audit logs
4. **ElastiCache Redis** instead of in-memory cache
5. **CloudWatch** for logging/monitoring
6. **ALB** for load balancing

**Production Checklist:**

✅ **Security:**
- HTTPS only (let's encrypt SSL)
- CORS whitelist (not allow_origins=['*'])
- Rate limiting (slowapi middleware)
- File upload virus scanning (ClamAV)

✅ **Monitoring:**
- Promethe us metrics (response time, cache hit rate)
- Sentry for error tracking
- Health check endpoint (already implemented at /api/health)

✅ **Performance:**
- Increase Uvicorn workers (4-8 based on CPU count)
- Enable gzip compression
- Add request timeout (30s max)
- Load balancer with auto-scaling

✅ **Database:**
- Migrate SQLite → PostgreSQL for concurrent writes
- Add connection pooling
- Regular backups (daily)

✅ **Costs:**
- Estimate: ~$20/month for Railway + Groq API ($0.27 per million input tokens)
- Caching reduces API costs by ~40%

**CI/CD Pipeline:**
```yaml
# .github/workflows/deploy.yml
on: push
  branches: [main]
jobs:
  deploy:
    - pytest tests/
    - docker build
    - railway deploy
```

---

### Q15: How do you handle scaling issues?

**Answer:**
"I'd scale different components based on bottlenecks:

**Identified Bottlenecks:**

1. **Embedding Model (CPU-bound)**
   - Problem: sentence-transformers uses CPU, slow for large batches
   - Solution: 
     - Use GPU-enabled containers (AWS g4 instances)
     - Or separate embedding service with queue (Celery + Redis)
     - Or switch to API-based embeddings (OpenAI, Cohere)

2. **Vector Search (Memory-bound)**
   - Problem: ChromaDB loads entire index into RAM
   - Solutions:
     - Horizontal scaling → Use Pinecone/Weaviate (cloud vector DBs)
     - Sharding → Partition documents by category
     - HNSW tuning → Reduce n_probes for faster search

3. **LLM API Calls (Network-bound)**
   - Problem: Groq API has rate limits (100 requests/min on free tier)
   - Solutions:
     - Aggressive caching (we already do this)
     - Request batching → Group similar queries
     - Retry logic with exponential backoff
     - Upgrade to paid tier or self-host Llama

4. **Concurrent Users (I/O-bound)**
   - Problem: Single Uvicorn worker can't handle 1000s of concurrent users
   - Solution: Increase workers
     ```python
     # Optimal: workers = 2 * CPU cores + 1
     CMD ['uvicorn', 'app.main:app', '--workers', '8']
     ```

**Scaling Architecture:**

```
                    ┌─────────────┐
                    │ Load Balancer│
                    └──────┬──────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
  ┌─────▼─────┐      ┌─────▼─────┐     ┌─────▼─────┐
  │ FastAPI   │      │ FastAPI   │     │ FastAPI   │
  │ Worker 1  │      │ Worker 2  │     │ Worker 3  │
  └─────┬─────┘      └─────┬─────┘     └─────┬─────┘
        │                  │                  │
        └──────────────────┼──────────────────┘
                           │
                  ┌────────┼────────┐
                  │                 │
           ┌──────▼──────┐   ┌──────▼──────┐
           │ Redis Cache │   │  Pinecone   │
           │  (Shared)   │   │ (Vector DB) │
           └─────────────┘   └─────────────┘
```

**Performance Optimizations:**

1. **Database Connection Pooling:**
```python
# SQLAlchemy for async Postgres
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=0
)
```

2. **Response Streaming:**
```python
@router.post('/query/stream')
async def query_stream():
    async for token in llm_service.stream_answer():
        yield token
```
Streams answer as it's generated (better UX)

3. **Batch Processing:**
```python
# Process multiple queries in one LLM call
queries = ['Q1', 'Q2', 'Q3']
answers = llm_service.batch_generate(queries)
```

**Monitoring for Scale:**
- Response time P95 < 3s
- Cache hit rate > 40%
- Error rate < 0.1%
- CPU usage < 70%
- Memory usage < 80%

**Cost at Scale:**
- 1000 requests/day: ~$5/month (mostly Groq API)
- 10,000 requests/day: ~$50/month
- 100,000 requests/day: ~$500/month (should consider self-hosting LLM)"

---

## Evaluation & Metrics

### Q16: How do you evaluate RAG system quality?

**Answer:**
"RAG evaluation has two components: retrieval quality and generation quality.

**Retrieval Metrics:**

1. **Precision@K:**
   - Of the K chunks retrieved, how many are relevant?
   - Formula: `relevant_retrieved / K`
   - Example: If top-3 chunks include 2 relevant ones → Precision@3 = 2/3 = 0.67

2. **Recall@K:**
   - Of all relevant chunks in the database, how many did we retrieve?
   - Formula: `relevant_retrieved / total_relevant`
   - Example: 10 relevant chunks exist, we retrieved 2 → Recall@3 = 2/10 = 0.20

3. **MRR (Mean Reciprocal Rank):**
   - Position of first relevant chunk
   - Formula: `1 / rank_of_first_relevant`
   - Example: First relevant chunk is #2 → MRR = 1/2 = 0.5

**Implementation:**
```python
def evaluate_retrieval(queries, ground_truth):
    precisions, recalls, mrrs = [], [], []
    
    for query, relevant_ids in zip(queries, ground_truth):
        retrieved_ids = vector_service.search(query, k=3)['ids']
        
        relevant_retrieved = set(retrieved_ids) & set(relevant_ids)
        
        precision = len(relevant_retrieved) / len(retrieved_ids)
        recall = len(relevant_retrieved) / len(relevant_ids)
        
        # Find first relevant
        for rank, id in enumerate(retrieved_ids, 1):
            if id in relevant_ids:
                mrr = 1 / rank
                break
        else:
            mrr = 0
        
        precisions.append(precision)
        recalls.append(recall)
        mrrs.append(mrr)
    
    return {
        'precision@3': np.mean(precisions),
        'recall@3': np.mean(recalls),
        'mrr': np.mean(mrrs)
    }
```

**Generation Metrics:**

1. **Faithfulness:**
   - Does the answer stay true to the retrieved context?
   - Method: Use LLM to judge if answer is supported by context
   ```python
   prompt = f'''
   Context: {context}
   Answer: {answer}
   
   Is the answer faithful to the context? (yes/no)
   '''
   ```

2. **Answer Relevance:**
   - Does the answer actually address the question?
   - Method: Embedding similarity between query and answer

3. **Context Utilization:**
   - Does the answer use the retrieved chunks?
   - Method: Check if key phrases from chunks appear in answer

4. **Human Evaluation:**
   - Have humans rate answers 1-5 on:
     - Correctness
     - Completeness
     - Clarity
     - Usefulness

**End-to-End Metrics:**

1. **Response Time:**
   - Target: <3s for P95
   - Track: Average, P50, P95, P99

2. **Cache Hit Rate:**
   - Formula: `cache_hits / total_requests`
   - Target: >40%

3. **Cost Per Query:**
   - Formula: `total_api_cost / num_queries`
   - Track daily/monthly

**A/B Testing Framework:**
```python
def run_ab_test(control_model, experiment_model, queries):
    for query in queries:
        if random() < 0.5:
            answer = control_model.generate(query)
            log('control', query, answer)
        else:
            answer = experiment_model.generate(query)
            log('experiment', query, answer)
    
    # Compare metrics
    compare_metrics('control', 'experiment')
```

**Real-world evaluation approach:**

Phase 1: Define test set (50-100 queries with ground truth)
Phase 2: Measure baseline metrics
Phase 3: Make improvements (better chunking, different model, etc.)
Phase 4: Re-measure and compare
Phase 5: Deploy winner

**Tools I'd use:**
- RAGAS library for automated RAG evaluation
- LangSmith for LLM tracing and evaluation
- Custom SQL queries on audit.db for analytics"

---

### Q17: What metrics are you tracking in your system?

**Answer:**
"I track both runtime metrics (via logging) and business metrics (via audit database):

**Runtime Metrics (Logged):**

1. **Response Times:**
```python
response_time_ms = int((time.time() - start_time) * 1000)
logger.info(f'Query processed in {response_time_ms}ms')
```
Tracked per request, can aggregate for P50/P95/P99

2. **Cache Performance:**
```python
logger.info(f'Cache HIT for query: {query[:30]}...')
# or
logger.info(f'Cache MISS for query: {query[:30]}...')
```
Enables calculating hit rate: `hits / (hits + misses)`

3. **Retrieval Results:**
```python
logger.info(f'Found {len(results)} results for query')
```
Monitor if retrieval is returning empty results (indicates bad embeddings/queries)

4. **Error Rates:**
```python
logger.error(f'Error processing query: {str(e)}')
```
Track error frequency and types

**Business Metrics (Audit DB):**

The `query_logs` table stores:
```sql
CREATE TABLE query_logs (
    id INTEGER PRIMARY KEY,
    query TEXT,
    answer TEXT,
    source_chunks TEXT,  -- JSON array
    chunk_ids TEXT,      -- JSON array
    timestamp DATETIME,
    response_time_ms INTEGER
)
```

**Analysis queries:**

1. **Average response time:**
```sql
SELECT AVG(response_time_ms) as avg_time
FROM query_logs
WHERE timestamp > datetime('now', '-24 hours')
```

2. **Most common queries:**
```sql
SELECT query, COUNT(*) as frequency
FROM query_logs
GROUP BY LOWER(query)
ORDER BY frequency DESC
LIMIT 10
```
Helps identify topics users care about most

3. **Response time distribution:**
```sql
SELECT 
    MIN(response_time_ms) as min,
    AVG(response_time_ms) as avg,
    MAX(response_time_ms) as max,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY response_time_ms) as p95
FROM query_logs
```

4. **Chunk utilization:**
```sql
SELECT chunk_id, COUNT(*) as times_retrieved
FROM query_logs, json_each(chunk_ids)
GROUP BY chunk_id
ORDER BY times_retrieved DESC
```
Identifies most useful chunks (consider featuring them)

**Dashboard (would build with Streamlit/Grafana):**

```
┌─────────────────────────────────────────┐
│ RAG System Metrics Dashboard            │
├───────────────────┬─────────────────────┤
│ Total Queries     │ 1,234               │
│ Avg Response Time │ 1,856 ms            │
│ Cache Hit Rate    │ 42.3%               │
│ Error Rate        │ 0.8%                │
├───────────────────┴─────────────────────┤
│ Response Time (Last 24h)                │
│ ████████████░░░░░  P50: 1.2s            │
│ ██████████████░░░░ P95: 3.4s            │
│ █████████████████░ P99: 5.1s            │
├─────────────────────────────────────────┤
│ Top Queries                             │
│ 1. What is RAG? (45 times)              │
│ 2. How to upload docs? (32 times)       │
│ 3. API documentation? (28 times)        │
└─────────────────────────────────────────┘
```

**Alerting (would implement):**
- P95 response time > 5s → Slack alert
- Error rate > 5% → PagerDuty
- Cache hit rate < 20% → Email (investigate query patterns)

**Why these metrics matter:**
- **Response time** → User experience
- **Cache hit rate** → Cost optimization
- **Error rate** → System reliability
- **Query patterns** → Product insights (what features to build)"

---

## Challenges & Trade-offs

### Q18: What were the biggest challenges you faced?session

**Answer:**
"Three main challenges:

**1. Chunk Size Optimization**

**Problem**: Different chunk sizes gave wildly different results
- 100 chars: Too granular, lost context
- 1000 chars: Too broad, irrelevant information

**Solution Process**:
1. Created test queries with expected answers
2. Tried chunk sizes: 200, 300, 500, 800, 1000
3. Measured retrieval precision (manual labeling)
4. Settled on 300 chars with 50-char overlap

**Learning**: There's no universal chunk size. It depends on:
- Document structure (tweets vs. research papers)
- Query types (factual vs. conceptual)
- LLM context window

**2. Cold Start Problem**

**Problem**: First request takes 7-8 seconds (model loading time)

**Timeline**:
```
User Request → Load embedding model (5s) → Load Groq client (1s)  
→ Process query (2s) → Total: 8s
```

**Solutions Tried**:
❌ Lazy loading → Doesn't help, still slow on first request
✅ Eager loading → Load during startup, not on first request
✅ Model caching → Keep model in memory (singleton pattern)
❓ Model serving → Separate FastAPI service just for embeddings

**Implemented**:
```python
@app.on_event('startup')
async def startup_event():
    # Pre-load model during server start
    _ = embedding_service.get_instance()
    logger.info('Embedding model preloaded')
```

Now first request is fast, startup takes the 5s hit (acceptable for production).

**3. Caching Complexity**

**Problem**: Queries like 'What is RAG?' vs. 'what is rag?' should hit same cache

**Solution**:
```python
def normalize_query(query: str) -> str:
    return query.lower().strip()

cache_key = hashlib.md5(normalize_query(query).encode()).hexdigest()
```

**Edge cases**:
- Typos: 'What is RAC?' → different cache entry (acceptable)
- Whitespace: 'What  is  RAG?' → same cache entry (handled by strip)
- Order: 'RAG is what?' → different cache entry (acceptable, different intent)

**Further improvement** (not implemented):
- Fuzzy matching: Use embedding similarity for cache lookup
  ```python
  if embed_similarity(query, cached_query) > 0.95:
      return cached_answer
  ```
  Trade-off: More cache hits but slower cache lookups

**Key Takeaway**: Each challenge taught me:
- Always benchmark before optimizing
- User experience trumps perfect accuracy
- Document trade-offs for future decisions"

---

### Q19: What would you do differently if starting over?

**Answer:**
"Several improvements I'd make:

**1. Database Choice**

**Current**: SQLite for audit logs
**Better**: PostgreSQL from day one

**Why**:
- SQLite doesn't support concurrent writes (writes are serialized)
- In production with multiple workers, this causes lock timeouts
- Migration from SQLite → Postgres is painful (schema incompatibilities)

**Lesson**: Start with the production database, even in development. The overhead is minimal.

**2. Async Everything**

**Current**: Synchronous service calls
```python
def search(query): 
    embedding = self.model.encode(query)  # Blocking
    return self.collection.query(embedding)  # Blocking
```

**Better**: Async service calls
```python
async def search(query):
    embedding = await self.encode_async(query)
    return await self.query_async(embedding)
```

**Benefits**:
- True concurrency (handle 10 requests simultaneously)
- Better resource utilization
- Lower latency under load

**Trade-off**: More complex code, harder to debug

**3. Structured Logging**

**Current**: String-based logs
```python
logger.info(f'Query processed in {response_time}ms')
```

**Better**: Structured JSON logs
```python
logger.info('query_processed', extra={
    'response_time_ms': response_time,
    'query_length': len(query),
    'cache_hit': cache_hit,
    'chunks_retrieved': len(chunks)
})
```

**Benefits**:
- Easy to parse with log aggregators (Datadog, Elasticsearch)
- Can filter/search by specific fields
- Enables better dashboards

**4. Testing**

**Current**: Manual testing only

**Better**: Automated test suite
```python
def test_query_endpoint():
    response = client.post('/api/query', json={'query': 'test'})
    assert response.status_code == 200
    assert 'answer' in response.json()

def test_cache_functionality():
    # First call should miss cache
    start = time.time()
    response1 = client.post('/api/query', json={'query': 'test'})
    time1 = time.time() - start
    
    # Second call should hit cache
    start = time.time()
    response2 = client.post('/api/query', json={'query': 'test'})
    time2 = time.time() - start
    
    assert time2 < time1 * 0.5  # Cache should be 2x+ faster
    assert response1.json() == response2.json()
```

**Coverage**:
- Unit tests for services
- Integration tests for endpoints
- End-to-end tests for RAG pipeline

**5. Configuration Validation**

**Current**: Silently use defaults if .env missing

**Better**: Fail fast with clear errors
```python
class Settings(BaseSettings):
    GROQ_API_KEY: str  # Required, no default
    
    @validator('GROQ_API_KEY')
    def validate_api_key(cls, v):
        if not v:
            raise ValueError('GROQ_API_KEY must be set in .env')
        if not v.startswith('gsk_'):
            raise ValueError('Invalid Groq API key format')
        return v
```

**6. Observability**

**Current**: Logs only

**Better**: Full observability stack
- **Traces**: OpenTelemetry to track requests across services
- **Metrics**: Prometheus for time-series data
- **Logs**: ELK stack for centralized logging

**Benefits**: Can answer questions like:
- 'Why was this request slow?' → Check trace
- 'What's the trend for cache hit rate?' → Check metrics
- 'Were there errors at 3am?' → Check logs

**Summary**: 
These aren't mistakes - they're pragmatic choices for an MVP. But knowing what I'd do differently shows growth and production awareness."

---

## Advanced Topics

### Q20: How would you implement hybrid search?

**Answer:**
"Hybrid search combines semantic search (embeddings) with keyword search (BM25) for better retrieval.

**Why hybrid?**

**Semantic search strengths**:
- Understands meaning: 'car repair' finds 'automobile maintenance'
- Handles synonyms and paraphrases

**Semantic search weaknesses**:
- Struggles with exact matches: 'GPT-4' might retrieve 'GPT-3.5'
- Bad with acronyms, codes, dates: 'Meeting on Dec 25' vs 'Christmas meeting'

**Keyword search (BM25) strengths**:
- Exact matches: 'GPT-4' only returns documents with 'GPT-4'
- Good for named entities, dates, numbers

**Keyword search weaknesses**:
- Misses synonyms: 'car repair' won't find 'automobile maintenance'
- No semantic understanding

**Hybrid approach**:

**Step 1: Retrieve from both**
```python
# Semantic search (vector similarity)
semantic_results = chromadb.query(query_embedding, n=10)

# Keyword search (BM25)
bm25_results = bm25_index.search(query, n=10)
```

**Step 2: Merge with RRF (Reciprocal Rank Fusion)**

Formula: `score = 1/(rank + k)` where k=60 (constant)

```python
def reciprocal_rank_fusion(semantic_results, keyword_results, k=60):
    scores = {}
    
    # Score semantic results
    for rank, doc_id in enumerate(semantic_results):
        scores[doc_id] = scores.get(doc_id, 0) + 1/(rank + k)
    
    # Score keyword results
    for rank, doc_id in enumerate(keyword_results):
        scores[doc_id] = scores.get(doc_id, 0) + 1/(rank + k)
    
    # Sort by combined score
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)
```

**Example**:
```
Query: 'GPT-4 release date'

Semantic results:
1. doc_5 (about GPT models)
2. doc_12 (about ChatGPT)
3. doc_8 (about OpenAI)

BM25 results:
1. doc_8 (contains 'GPT-4')
2. doc_15 (contains 'release date')
3. doc_5 (contains both terms)

RRF scores:
doc_5: 1/(0+60) + 1/(2+60) = 0.0167 + 0.0161 = 0.0328
doc_8: 1/(2+60) + 1/(0+60) = 0.0161 + 0.0167 = 0.0328
doc_12: 1/(1+60) = 0.0164
doc_15: 1/(1+60) = 0.0164

Final ranking: [doc_5, doc_8, doc_12, doc_15]
```

**Implementation**:

```python
from rank_bm25 import BM25Okapi

class HybridSearchService:
    def __init__(self):
        # Load documents
        self.documents = load_documents()
        
        # Build BM25 index
        tokenized_docs = [doc.split() for doc in self.documents]
        self.bm25 = BM25Okapi(tokenized_docs)
        
        # Vector service (already exists)
        self.vector_service = vector_service
    
    def search(self, query, top_k=3):
        # Semantic search
        semantic_results = self.vector_service.search(query, k=10)
        
        # BM25 search
        tokenized_query = query.split()
        bm25_scores = self.bm25.get_scores(tokenized_query)
        bm25_results = np.argsort(bm25_scores)[::-1][:10]
        
        # RRF fusion
        final_results = reciprocal_rank_fusion(
            semantic_results['ids'],
            [f'doc_{i}' for i in bm25_results]
        )
        
        return final_results[:top_k]
```

**When to use hybrid**:
- Domain with lots of technical terms (medical, legal)
- Queries mixing concepts and exact terms ('GPT-4 API pricing')
- Documents with important named entities (product names, dates)

**Trade-offs**:
- **Pro**: Better retrieval quality (5-10% improvement)
- **Con**: 2x retrieval time (both searches + fusion)
- **Con**: More complex infrastructure (maintain BM25 index)

**Alternative: Weighted fusion**:
```python
score = alpha * semantic_score + (1-alpha) * keyword_score
# alpha = 0.7 means 70% semantic, 30% keyword
```

**Production consideration**:
- Build BM25 index in background when documents are uploaded
- Cache hybrid results just like semantic results
- A/B test semantic vs. hybrid to validate improvement"

---

### Q21: Explain prompt engineering for RAG.

**Answer:**
"Prompt engineering is critical for RAG quality. Small prompt changes can dramatically affect answers.

**My current prompt structure**:

```python
prompt = f'''
Use the following context to answer the question. If the answer is not in the context, say "I don't have enough information to answer that."

Context:
{chunk_1}

{chunk_2}

{chunk_3}

Question: {query}

Answer:
'''
```

**Prompt engineering techniques I'd apply**:

**1. Few-Shot Examples**

Add examples of good answers:

```python
prompt = f'''
Answer questions based on the provided context.

Example:
Context: RAG combines retrieval and generation. It retrieves documents first.
Question: What does RAG combine?
Answer: RAG combines retrieval and generation.

Now answer this:
Context: {context}
Question: {query}
Answer:
'''
```

**Why it helps**: LLM learns the style and format you want

**2. Chain of Thought (CoT)**

Make LLM explain its reasoning:

```python
prompt = f'''
Context: {context}
Question: {query}

Think step by step:
1. What information from the context is relevant?
2. How does this relate to the question?
3. What is the final answer?

Final Answer:
'''
```

**Why it helps**: Reduces hallucination, improves complex reasoning

**3. System Prompts**

Define the LLM's role:

```python
system_prompt = "You are a helpful AI assistant that answers questions based strictly on provided context. Never make up information."

user_prompt = f'''
Context: {context}
Question: {query}
'''

response = client.chat.completions.create(
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
)
```

**Why it helps**: Sets behavior expectations

**4. Output Formatting**

Request structured output:

```python
prompt = f'''
Context: {context}
Question: {query}

Provide your answer in this format:
{{
    "answer": "your answer here",
    "confidence": "high/medium/low",
    "sources_used": ["chunk 1", "chunk 2"]
}}
'''
```

**Why it helps**: Easier to parse, adds metadata

**5. Negative Instructions**

Tell the LLM what NOT to do:

```python
prompt = f'''
Context: {context}
Question: {query}

Answer the question based on the context.

Rules:
- Do NOT use information outside the context
- Do NOT make assumptions
- Do NOT provide opinions, only facts from the context
- If unsure, say "I don't have enough information"

Answer:
'''
```

**Why it helps**: Prevents common failure modes

**Advanced: Dynamic Prompting**

Adapt prompt based on query type:

```python
def get_prompt_template(query_type):
    if query_type == 'factual':
        return f'''Extract exact facts from context to answer: {{query}}
        Context: {{context}}'''
    
    elif query_type == 'comparison':
        return f'''Compare the items mentioned in the question using the context.
        Create a bullet-point comparison.
        Context: {{context}}
        Question: {{query}}'''
    
    elif query_type == 'summarization':
        return f'''Summarize the context in 2-3 sentences.
        Context: {{context}}'''
    
    return default_template

# Classify query first
query_type = classify_query(query)  # Using small classifier model
prompt = get_prompt_template(query_type).format(query=query, context=context)
```

**Prompt optimization process**:

1. **Define test set**: 20-50 queries with expected answers
2. **Baseline**: Test current prompt, measure accuracy
3. **Iterate**: Change one thing (add example, change instruction, etc.)
4. **Evaluate**: Re-test on same queries
5. **Compare**: Keep change if accuracy improves
6. **Repeat**: Continue iterating

**Measuring prompt quality**:
```python
def evaluate_prompt(prompt_template, test_queries):
    scores = []
    for query, expected_answer in test_queries:
        answer = generate_with_prompt(prompt_template, query)
        score = similarity(answer, expected_answer)  # Embedding similarity
        scores.append(score)
    
    return np.mean(scores)

# Try different prompts
prompts = [baseline_prompt, fewshot_prompt, cot_prompt]
results = [evaluate_prompt(p, test_queries) for p in prompts]
best_prompt = prompts[np.argmax(results)]
```

**Interview tip**: Mention that prompting is experimental. There's no 'best' prompt - it depends on:
- LLM model (GPT-4 vs Llama)
- Domain (medical vs. customer support)
- Query types (factual vs. analytical)
- Desired output format (short vs. detailed)"

---

### Q22: How would you add conversational memory to your RAG system?

**Answer:**
"Conversational memory allows multi-turn conversations where the system remembers previous questions.

**Current limitation**:
```
User: What is RAG?
Bot: RAG is Retrieval-Augmented Generation...

User: How does it work?
Bot: I don't have enough information...  ← Forgot previous context!
```

**Solution: Conversation History**

**Architecture**:

```python
class ConversationMemory:
    def __init__(self, max_history=5):
        self.conversations = {}  # session_id -> messages
        self.max_history = max_history
    
    def add_message(self, session_id, role, content):
        if session_id not in self.conversations:
            self.conversations[session_id] = []
        
        self.conversations[session_id].append({
            'role': role,
            'content': content,
            'timestamp': datetime.now()
        })
        
        # Keep only last N messages
        self.conversations[session_id] = self.conversations[session_id][-self.max_history:]
    
    def get_history(self, session_id):
        return self.conversations.get(session_id, [])
    
    def clear(self, session_id):
        if session_id in self.conversations:
            del self.conversations[session_id]
```

**Updated Query Endpoint**:

```python
@router.post('/query')
async def query_rag(request: QueryRequest, session_id: str = None):
    # Get conversation history
    history = memory.get_history(session_id) if session_id else []
    
    # Build context-aware query
    if history:
        conversation_context = '\n'.join([
            f"{msg['role']}: {msg['content']}" 
            for msg in history
        ])
        
        # Rewrite query with context
        contextual_query = f'''
        Previous conversation:
        {conversation_context}
        
        Current question: {request.query}
        
        Rephrase the current question to be self-contained:
        '''
        
        standalone_query = llm_service.generate(contextual_query)
    else:
        standalone_query = request.query
    
    # Normal RAG pipeline with standalone query
    results = vector_service.search(standalone_query, k=3)
    answer = llm_service.generate_answer(standalone_query, results['documents'])
    
    # Save to memory
    if session_id:
        memory.add_message(session_id, 'user', request.query)
        memory.add_message(session_id, 'assistant', answer)
    
    return QueryResponse(answer=answer, ...)
```

**Key technique: Query Rewriting**

Transforms context-dependent query → standalone query

```
History:
User: What is RAG?
Bot: RAG is Retrieval-Augmented Generation...

Current query: "How does it work?"

Rewritten query: "How does Retrieval-Augmented Generation work?"
```

**Prompt for rewriting**:
```python
rewrite_prompt = f'''
Given a conversation history and a follow-up question, rephrase the follow-up question to be standalone.

Chat History:
{history}

Follow-up Question: {current_query}

Standalone Question:
'''
```

**Advanced: Conversation Summarization**

After N turns, summarize to save tokens:

```python
if len(history) > 10:
    summary_prompt = f'''
    Summarize this conversation:
    {history}
    
    Summary:
    '''
    summary = llm_service.generate(summary_prompt)
    
    # Replace history with summary
    memory.conversations[session_id] = [{
        'role': 'system',
        'content': f'Previous conversation summary: {summary}'
    }]
```

**Storage Considerations**:

**Option 1: In-Memory (Current)**
- Fast
- Lost on restart
- Doesn't scale across servers

**Option 2: Redis**
```python
import redis
r = redis.Redis()

def add_message(session_id, role, content):
    key = f'conversation:{session_id}'
    message = {'role': role, 'content': content, 'ts': time.time()}
    r.rpush(key, json.dumps(message))
    r.expire(key, 3600)  # Expire after 1 hour
```

**Option 3: Database**
```sql
CREATE TABLE conversations (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255),
    role VARCHAR(20),
    content TEXT,
    timestamp TIMESTAMP DEFAULT NOW()
);
```

**Frontend Changes**:

```javascript
let sessionId = localStorage.getItem('session_id');
if (!sessionId) {
    sessionId = generateUUID();
    localStorage.setItem('session_id', sessionId);
}

// Include in requests
fetch('/api/query', {
    method: 'POST',
    body: JSON.stringify({
        query: userQuery,
        session_id: sessionId
    })
});

// Clear conversation button
function clearConversation() {
    fetch(`/api/conversation/${sessionId}/clear`, {method: 'DELETE'});
    localStorage.removeItem('session_id');
}
```

**Trade-offs**:

**Pros**:
- Natural multi-turn conversations
- Better UX
- Can ask clarifying questions

**Cons**:
- More LLM tokens (history in every call)
- Query rewriting adds latency (~500ms)
- More complex state management
- Cache effectiveness reduced (fewer exact matches)

**Cost implications**:
- No history: 300 tokens/query
- With history (5 messages): 300 + 500 = 800 tokens/query
- Query rewriting: +200 tokens
- Total: 1000 tokens/query (3.3x more expensive)

**Optimization**: Only rewrite if pronouns detected
```python
if has_pronoun(query):  # 'it', 'this', 'that', 'they'
    query = rewrite_query(query, history)
```

**Interview point**: 'I designed a session-based conversation memory system with query rewriting to handle multi-turn dialogue while optimizing for costs by conditionally applying context enrichment.'"

---

## Behavioral Questions

### Q23: Walk me through something important you forgot to add initially, and how you fixed it.

**Answer:**
"After deploying the initial version, I realized I forgot to add cache hit/miss tracking metrics - a critical feature for monitoring system performance.

**What I Forgot**:
The cache was working, but I had no visibility into:
- Cache hit rate (how often we're saving API calls)
- Average response time difference (cache vs. no cache)
- Total cache entries and memory usage

**Why It Mattered**:
Without metrics, I couldn't answer:
- "Is caching actually helping?"
- "Should I increase/decrease TTL?"
- "When should I migrate to Redis?"

**Discovery Process**:

1. **Noticed during testing**:
```
Query 1: 2000ms (cold)
Query 2: 20ms (should be cached?)
Query 3: 2100ms (why not cached??)
```

No way to confirm if cache was working!

2. **Checked code - missing pieces**:
```python
# cache_service.py - Original (missing tracking)
class CacheService:
    def __init__(self):
        self.cache = {}  # ❌ No metrics tracking!
```

**The Fix**:

**Step 1** - Added metrics to cache service:
```python
# app/services/cache_service.py
class CacheService:
    def __init__(self):
        self.cache = {}
        self.ttl = settings.CACHE_TTL
        
        # NEW: Tracking metrics
        self.hits = 0
        self.misses = 0
    
    def get(self, query: str):
        cache_key = self._get_cache_key(query)
        
        if cache_key in self.cache:
            entry = self.cache[cache_key]
            age = time.time() - entry['timestamp']
            
            if age < self.ttl:
                self.hits += 1  # ✅ Track hit
                logger.info(f"Cache HIT (total: {self.hits})")
                return entry['response']
            else:
                del self.cache[cache_key]
        
        self.misses += 1  # ✅ Track miss
        logger.info(f"Cache MISS (total: {self.misses})")
        return None
    
    def get_stats(self) -> dict:
        """NEW: Get cache statistics"""
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'total_entries': len(self.cache),
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate_percent': round(hit_rate, 2),
            'ttl_seconds': self.ttl
        }
```

**Step 2** - Added metrics endpoint:
```python
# app/api/routes/admin.py
@router.get('/stats')
async def get_stats():
    cache_stats = cache_service.get_stats()
    
    return {
        'total_chunks': vector_service.get_collection_count(),
        'cache_stats': cache_stats,  # ✅ Now includes hit rate!
        'total_queries': database.get_query_count()
    }
```

**Step 3** - Updated frontend to display metrics:
```javascript
// Added stats display
async function loadStats() {
    const response = await fetch('/api/stats');
    const data = await response.json();
    
    document.getElementById('hit-rate').textContent = 
        `${data.cache_stats.hit_rate_percent}%`;
    document.getElementById('total-requests').textContent = 
        data.cache_stats.hits + data.cache_stats.misses;
}
```

**Result**:
Now I can see in real-time:
```json
{
  "cache_stats": {
    "hits": 342,
    "misses": 158,
    "hit_rate_percent": 68.4,
    "total_entries": 127
  }
}
```

**Key Lesson**: Always add observability from day one. Metrics aren't optional - they're essential for making informed decisions about optimization and scaling."

**What I learned**:

1. **Fail fast**: Validation should match actual capabilities
2. **Error messages matter**: 'PDF support coming soon' helped debug quickly
3. **Test real scenarios**: I tested with TXT files only, missed PDF edge case
4. **Documentation**: Updated README.md to clearly state supported formats

**Prevention**:
Added integration test:
```python
def test_unsupported_file_upload():
    response = client.post('/api/upload', files={'file': ('test.pdf', pdf_content)})
    assert response.status_code == 400
    assert 'not supported' in response.json()['detail']
```

This experience taught me to validate assumptions at system boundaries (frontend ↔ backend) and ensure error messages are actionable."

---

## Closing Thoughts

**What makes a strong RAG interview?**

1. **Know your system deeply**: Every file, every function, every decision
2. **Explain in layers**: Layman → Technical → Advanced
3. **Mention trade-offs**: There's no perfect solution, only appropriate ones
4. **Quantify impact**: Response times, costs, cache hit rates
5. **Show growth**: What you'd do differently

**Key phrases to use**:
- 'I designed...' (ownership)
- 'The trade-off was...' (critical thinking)
- 'I measured... and improved by X%' (data-driven)
- 'In production, I would...' (forward-thinking)

**Red flags to avoid**:
- 'I don't know' (instead: 'I haven't implemented that yet, but here's how I would...')
- 'It just works' (explain WHY)
- 'I copied from tutorial' (explain what you learned/modified)

Good luck with your interviews! 🚀
