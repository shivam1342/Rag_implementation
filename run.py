# run.py
"""
Simple script to run the RAG application
"""
import uvicorn

if __name__ == "__main__":
    print("=" * 60)
    print("Starting RAG System API Server")
    print("=" * 60)
    print("\nAPI Documentation: http://localhost:8000/docs")
    print("Health Check: http://localhost:8000/api/health")
    print("Stats: http://localhost:8000/api/stats")
    print("\nPress CTRL+C to stop\n")
    print("=" * 60)
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
