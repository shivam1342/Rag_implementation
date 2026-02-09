# app/models/database.py
import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any
from app.core.config import settings
from app.core.logger import logger

class AuditDatabase:
    """SQLite database for audit logging"""
    
    def __init__(self):
        self.db_path = settings.AUDIT_DB
        self._init_db()
        logger.info(f"Audit database initialized: {self.db_path}")
    
    def _init_db(self):
        """Initialize database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS query_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                answer TEXT NOT NULL,
                source_chunks TEXT,
                chunk_ids TEXT,
                timestamp DATETIME NOT NULL,
                response_time_ms INTEGER
            )
        """)
        
        conn.commit()
        conn.close()
    
    def log_query(
        self,
        query: str,
        answer: str,
        source_chunks: List[str] = None,
        chunk_ids: List[str] = None,
        response_time_ms: int = None
    ) -> int:
        """
        Log a query and its response.
        
        Returns:
            ID of the logged entry
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO query_logs 
                (query, answer, source_chunks, chunk_ids, timestamp, response_time_ms)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                query,
                answer,
                json.dumps(source_chunks) if source_chunks else None,
                json.dumps(chunk_ids) if chunk_ids else None,
                datetime.now().isoformat(),
                response_time_ms
            ))
            
            log_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            logger.debug(f"Logged query with ID: {log_id}")
            return log_id
        except Exception as e:
            logger.error(f"Error logging query: {e}")
            raise
    
    def get_recent_logs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent query logs"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM query_logs 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (limit,))
            
            rows = cursor.fetchall()
            conn.close()
            
            logs = []
            for row in rows:
                log = dict(row)
                # Parse JSON fields
                if log['source_chunks']:
                    log['source_chunks'] = json.loads(log['source_chunks'])
                if log['chunk_ids']:
                    log['chunk_ids'] = json.loads(log['chunk_ids'])
                logs.append(log)
            
            return logs
        except Exception as e:
            logger.error(f"Error getting recent logs: {e}")
            return []
    
    def get_total_queries(self) -> int:
        """Get total number of logged queries"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM query_logs")
            count = cursor.fetchone()[0]
            
            conn.close()
            return count
        except Exception as e:
            logger.error(f"Error getting query count: {e}")
            return 0

# Global instance
audit_db = AuditDatabase()
