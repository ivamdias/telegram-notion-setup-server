import os
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv('DATABASE_URL')

@contextmanager
def get_db_connection():
    """Context manager for database connections"""
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

def store_user_integration_data(telegram_id: int, integration_data: dict):
    """Store internal integration data for a user"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (
                telegram_id, notion_access_token, notion_workspace_id,
                notion_workspace_name, notion_bot_id, notion_database_id,
                user_name, updated_at
            ) VALUES (%(telegram_id)s, %(access_token)s, %(workspace_id)s,
                     %(workspace_name)s, %(bot_id)s, %(database_id)s,
                     %(user_name)s, NOW())
            ON CONFLICT (telegram_id) 
            DO UPDATE SET
                notion_access_token = EXCLUDED.notion_access_token,
                notion_workspace_id = EXCLUDED.notion_workspace_id,
                notion_workspace_name = EXCLUDED.notion_workspace_name,
                notion_bot_id = EXCLUDED.notion_bot_id,
                notion_database_id = EXCLUDED.notion_database_id,
                user_name = EXCLUDED.user_name,
                updated_at = NOW()
        """, {
            'telegram_id': telegram_id,
            'access_token': integration_data['access_token'],
            'workspace_id': integration_data.get('workspace_id', 'internal'),
            'workspace_name': integration_data.get('workspace_name', 'Personal Workspace'),
            'bot_id': integration_data.get('bot_id', 'internal_integration'),
            'database_id': integration_data.get('database_id'),
            'user_name': integration_data.get('user_name', 'Unknown')
        })

def get_user_integration_data(telegram_id: int):
    """Get integration data for a user"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT notion_access_token, notion_workspace_id, notion_workspace_name,
                   notion_bot_id, notion_database_id, user_name, created_at, updated_at
            FROM users WHERE telegram_id = %s
        """, (telegram_id,))
        return cursor.fetchone()

def delete_user_integration_data(telegram_id: int):
    """Delete integration data for a user"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE telegram_id = %s", (telegram_id,))
        return cursor.rowcount > 0

def test_database_connection():
    """Test database connectivity"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            return result is not None
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False

def get_user_count():
    """Get total number of connected users"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM users")
            result = cursor.fetchone()
            return result['count'] if result else 0
    except Exception as e:
        logger.error(f"Error getting user count: {e}")
        return 0
