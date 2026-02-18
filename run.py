# run.py
"""
Simple script to run the RAG application
"""
import uvicorn
import os

if __name__ == "__main__":
    # Railway provides PORT env variable - use it or default to 8000
    port = int(os.getenv("PORT", 8000))
    
    print("=" * 60)
    print("Starting RAG System API Server")
    print("=" * 60)
    print(f"\nRunning on port: {port}")
    print(f"API Documentation: http://localhost:{port}/docs")
    print(f"Health Check: http://localhost:{port}/api/health")
    print(f"Stats: http://localhost:{port}/api/stats")
    print("\nPress CTRL+C to stop\n")
    print("=" * 60)
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=False,  # Disable reload in production
        log_level="info"
    )
