# build_index.py
"""
Script to build the initial vector index from documents in data/ directory
"""
import os
from app.services.vector_service import vector_service
from app.utils.chunking import chunk_text
from app.core.config import settings
from app.core.logger import logger

DATA_DIR = "data"

def main():
    """Build vector index from documents in data/ directory"""
    logger.info("Starting index build...")
    
    if not os.path.exists(DATA_DIR):
        logger.error(f"Data directory not found: {DATA_DIR}")
        print(f"❌ Error: {DATA_DIR}/ directory not found")
        return
    
    # Get all text files
    files = [f for f in os.listdir(DATA_DIR) if f.endswith('.txt')]
    
    if not files:
        logger.warning(f"No .txt files found in {DATA_DIR}")
        print(f"⚠️  No .txt files found in {DATA_DIR}/")
        return
    
    logger.info(f"Found {len(files)} files to process")
    print(f"\n📚 Found {len(files)} files to process\n")
    
    # Process each file
    total_chunks = 0
    for filename in files:
        file_path = os.path.join(DATA_DIR, filename)
        logger.info(f"Processing: {filename}")
        print(f"  Processing: {filename}")
        
        # Read file
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        # Chunk text
        chunks = chunk_text(text)
        
        # Create metadata
        metadatas = [
            {"source_file": filename, "chunk_index": i} 
            for i in range(len(chunks))
        ]
        
        # Add to vector DB
        vector_service.add_documents(chunks, metadatas)
        
        total_chunks += len(chunks)
        print(f"    ✓ Created {len(chunks)} chunks")
        logger.info(f"  -> Created {len(chunks)} chunks")
    
    print(f"\n✅ Index built successfully!")
    print(f"   Total: {total_chunks} chunks from {len(files)} files")
    print(f"   Collection size: {vector_service.get_collection_count()} documents\n")
    
    logger.info(f"✓ Index built: {total_chunks} chunks from {len(files)} files")
    logger.info(f"Total documents in collection: {vector_service.get_collection_count()}")

if __name__ == "__main__":
    main()
