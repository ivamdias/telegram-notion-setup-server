import os
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)

# Try multiple ways to get DATABASE_URL
DATABASE_URL = (
    os.getenv('DATABASE_URL') or 
    os.environ.get('DATABASE_URL') or
    os.environ.get('POSTGRES_URL') or  # Railway sometimes uses this
    os.environ.get('PGURL')  # Another common name
)

if not DATABASE_URL:
    logger.error("❌ No DATABASE_URL found in environment variables")
    logger.error(f"Available env vars: {[k for k in os.environ.keys() if 'DATA' in k or 'PG' in k or 'POSTGRES' in k]}")
else:
    logger.info(f"✅ Found DATABASE_URL: {DATABASE_URL[:50]}...")

@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL environment variable not set")
    
    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        yield conn
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        if conn:
            conn.close()

# Rest of your functions remain the same...
