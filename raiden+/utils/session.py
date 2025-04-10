from uuid import uuid4
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import Request
import sqlite3
import json
import os

class SessionManager:
    def __init__(self, db_path: str = "sessions.db", expiry: int = 3600):
        self.db_path = db_path
        self.expiry = expiry
        self._initialize_db()
    
    def _initialize_db(self):
        """Initialize SQLite database and required tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Create sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    last_accessed TEXT NOT NULL,
                    user_data TEXT,
                    expires_at TEXT NOT NULL
                )
            """)
            # Create conversation history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    session_id TEXT,
                    message_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
                )
            """)
            # Create tool outputs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tool_outputs (
                    session_id TEXT,
                    tool_name TEXT NOT NULL,
                    output TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
                )
            """)
            conn.commit()
    
    def create_session(self, user_data: Dict[str, Any] = None) -> str:
        """Creates a new session with unique ID and stores it in SQLite."""
        session_id = str(uuid4())
        now = datetime.utcnow()
        expires_at = now + timedelta(seconds=self.expiry)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO sessions (session_id, created_at, last_accessed, user_data, expires_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (session_id, now.isoformat(), now.isoformat(),
                 json.dumps(user_data or {}), expires_at.isoformat())
            )
            conn.commit()
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves session data from SQLite and updates last_accessed."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
                
            # Update last_accessed
            now = datetime.utcnow()
            expires_at = now + timedelta(seconds=self.expiry)
            cursor.execute(
                """UPDATE sessions 
                   SET last_accessed = ?, expires_at = ?
                   WHERE session_id = ?""",
                (now.isoformat(), expires_at.isoformat(), session_id)
            )
            conn.commit()
            
            # Return session data
            return {
                "created_at": row[1],
                "last_accessed": now.isoformat(),
                "user_data": json.loads(row[3])
            }
    
    def update_session(self, session_id: str, data: Dict[str, Any]) -> bool:
        """Updates session data in SQLite."""
        existing = self.get_session(session_id)
        if not existing:
            return False
            
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            existing["user_data"].update(data)
            now = datetime.utcnow()
            expires_at = now + timedelta(seconds=self.expiry)
            
            cursor.execute(
                """UPDATE sessions 
                   SET user_data = ?, 
                       last_accessed = ?,
                       expires_at = ?
                   WHERE session_id = ?""",
                (json.dumps(existing["user_data"]), 
                 now.isoformat(),
                 expires_at.isoformat(),
                 session_id)
            )
            conn.commit()
            return True

    def delete_session(self, session_id: str) -> bool:
        """Deletes a session and its related data from SQLite."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
            rows_affected = cursor.rowcount
            conn.commit()
            return rows_affected > 0

    async def verify_session(self, request: Request) -> Optional[Dict[str, Any]]:
        """Verifies and retrieves session data from cookie."""
        session_id = request.cookies.get("session_id")
        if not session_id:
            return None
        return self.get_session(session_id)

    def clear_session(self, session_id: str) -> bool:
        """Clears all data associated with a session."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # Delete conversations and tool outputs first (due to foreign key constraints)
                cursor.execute("DELETE FROM conversations WHERE session_id = ?", (session_id,))
                cursor.execute("DELETE FROM tool_outputs WHERE session_id = ?", (session_id,))
                # Then delete the session
                cursor.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error clearing session {session_id}: {e}")
            return False
    
    def clear_all_sessions(self) -> bool:
        """Clears all sessions and associated data (admin only)."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # Delete all data from all tables
                cursor.execute("DELETE FROM conversations")
                cursor.execute("DELETE FROM tool_outputs")
                cursor.execute("DELETE FROM sessions")
                conn.commit()
                return True
        except Exception as e:
            print(f"Error clearing all sessions: {e}")
            return False
