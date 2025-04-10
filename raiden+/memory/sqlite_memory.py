import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
import sqlite3
from pathlib import Path
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_community.chat_message_histories import SQLChatMessageHistory

try:
    from app import WORKSPACE_DIR
except ImportError:
    WORKSPACE_DIR = Path("./raiden_workspace_srv")
    WORKSPACE_DIR.mkdir(exist_ok=True)

class RaidenMemory:
    def __init__(self, workspace_dir: Path = WORKSPACE_DIR):
        self.db_path = workspace_dir / "raiden_memory.db"
        self._initialize_db()
        
    def _initialize_db(self):
        """Initialize SQLite database with enhanced tables for conversation memory"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Create conversations table with additional fields
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    session_id TEXT,
                    message_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    tool_calls TEXT,
                    entities TEXT,  -- Store extracted entities/topics
                    sentiment TEXT, -- Store message sentiment
                    timestamp TEXT NOT NULL,
                    PRIMARY KEY (session_id, timestamp)
                )
            """)
            
            # Create context table for session memory
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS context (
                    session_id TEXT PRIMARY KEY,
                    data TEXT NOT NULL,
                    preferences TEXT,  -- Store user preferences
                    topics TEXT,       -- Store conversation topics
                    last_updated TEXT NOT NULL
                )
            """)
            
            # Create entity memory table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS entity_memory (
                    entity_id TEXT PRIMARY KEY,
                    entity_type TEXT NOT NULL,
                    data TEXT NOT NULL,
                    last_mentioned TEXT NOT NULL,
                    mention_count INTEGER DEFAULT 1,
                    first_seen TEXT NOT NULL
                )
            """)
            
            # Create conversation summaries table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversation_summaries (
                    session_id TEXT PRIMARY KEY,
                    summary TEXT NOT NULL,
                    key_points TEXT,
                    last_updated TEXT NOT NULL
                )
            """)
            conn.commit()
    
    def save_conversation(self, session_id: str, messages: List[BaseMessage]) -> bool:
        """Save conversation history with enhanced metadata"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Insert new messages with metadata
                for msg in messages:
                    msg_data = {
                        "type": msg.__class__.__name__,
                        "content": msg.content,
                        "timestamp": datetime.now().isoformat(),
                        "entities": "[]",  # Placeholder for entity extraction
                        "sentiment": "neutral"  # Default sentiment
                    }
                    
                    if hasattr(msg, 'tool_calls') and msg.tool_calls:
                        msg_data["tool_calls"] = json.dumps(msg.tool_calls)
                    
                    cursor.execute(
                        """INSERT INTO conversations 
                           (session_id, message_type, content, tool_calls, entities, sentiment, timestamp)
                           VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        (session_id, msg_data["type"], msg_data["content"],
                         msg_data.get("tool_calls"), msg_data["entities"],
                         msg_data["sentiment"], msg_data["timestamp"])
                    )
                conn.commit()
                return True
        except Exception as e:
            print(f"Error saving conversation: {e}")
            return False
    
    def load_conversation(self, session_id: str, limit: int = None) -> List[BaseMessage]:
        """Load conversation history with optional limit"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                query = """
                    SELECT message_type, content, tool_calls, entities, sentiment 
                    FROM conversations 
                    WHERE session_id = ?
                    ORDER BY timestamp
                """
                if limit:
                    query += f" LIMIT {int(limit)}"
                    
                cursor.execute(query, (session_id,))
                rows = cursor.fetchall()
                
                messages = []
                for msg_type, content, tool_calls, entities, sentiment in rows:
                    additional_kwargs = {
                        "entities": json.loads(entities) if entities else [],
                        "sentiment": sentiment
                    }
                    
                    if msg_type == "HumanMessage":
                        msg = HumanMessage(content=content, additional_kwargs=additional_kwargs)
                    elif msg_type == "AIMessage":
                        if tool_calls:
                            additional_kwargs["tool_calls"] = json.loads(tool_calls)
                        msg = AIMessage(content=content, additional_kwargs=additional_kwargs)
                    elif msg_type == "SystemMessage":
                        msg = SystemMessage(content=content, additional_kwargs=additional_kwargs)
                    messages.append(msg)
                return messages
        except Exception as e:
            print(f"Error loading conversation: {e}")
            return []
    
    def save_context(self, session_id: str, context: Dict[str, Any], 
                    preferences: Dict = None, topics: List[str] = None) -> bool:
        """Save session context with enhanced metadata"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                now = datetime.now().isoformat()
                
                cursor.execute(
                    """INSERT OR REPLACE INTO context 
                       (session_id, data, preferences, topics, last_updated)
                       VALUES (?, ?, ?, ?, ?)""",
                    (session_id, json.dumps(context),
                     json.dumps(preferences or {}),
                     json.dumps(topics or []),
                     now)
                )
                conn.commit()
                return True
        except Exception as e:
            print(f"Error saving context: {e}")
            return False
    
    def load_context(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load session context with enhanced metadata"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """SELECT data, preferences, topics 
                       FROM context 
                       WHERE session_id = ?""",
                    (session_id,)
                )
                row = cursor.fetchone()
                if row:
                    return {
                        "data": json.loads(row[0]),
                        "preferences": json.loads(row[1]) if row[1] else {},
                        "topics": json.loads(row[2]) if row[2] else []
                    }
                return None
        except Exception as e:
            print(f"Error loading context: {e}")
            return None
    
    def save_entity_memory(self, entity_id: str, entity_type: str, 
                         data: Dict[str, Any]) -> bool:
        """Save or update entity memory"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                now = datetime.now().isoformat()
                
                # Check if entity exists
                cursor.execute(
                    "SELECT mention_count FROM entity_memory WHERE entity_id = ?",
                    (entity_id,)
                )
                row = cursor.fetchone()
                
                if row:
                    # Update existing entity
                    cursor.execute(
                        """UPDATE entity_memory 
                           SET data = ?, 
                               last_mentioned = ?,
                               mention_count = mention_count + 1
                           WHERE entity_id = ?""",
                        (json.dumps(data), now, entity_id)
                    )
                else:
                    # Insert new entity
                    cursor.execute(
                        """INSERT INTO entity_memory 
                           (entity_id, entity_type, data, last_mentioned, first_seen)
                           VALUES (?, ?, ?, ?, ?)""",
                        (entity_id, entity_type, json.dumps(data), now, now)
                    )
                conn.commit()
                return True
        except Exception as e:
            print(f"Error saving entity memory: {e}")
            return False
    
    def get_entity_memory(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve entity memory"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """SELECT entity_type, data, last_mentioned, mention_count, first_seen
                       FROM entity_memory 
                       WHERE entity_id = ?""",
                    (entity_id,)
                )
                row = cursor.fetchone()
                if row:
                    return {
                        "entity_type": row[0],
                        "data": json.loads(row[1]),
                        "last_mentioned": row[2],
                        "mention_count": row[3],
                        "first_seen": row[4]
                    }
                return None
        except Exception as e:
            print(f"Error getting entity memory: {e}")
            return None
    
    def save_conversation_summary(self, session_id: str, summary: str, 
                                key_points: List[str] = None) -> bool:
        """Save a summary of the conversation"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                now = datetime.now().isoformat()
                
                cursor.execute(
                    """INSERT OR REPLACE INTO conversation_summaries
                       (session_id, summary, key_points, last_updated)
                       VALUES (?, ?, ?, ?)""",
                    (session_id, summary, 
                     json.dumps(key_points or []), 
                     now)
                )
                conn.commit()
                return True
        except Exception as e:
            print(f"Error saving conversation summary: {e}")
            return False
    
    def get_conversation_summary(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve conversation summary"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """SELECT summary, key_points, last_updated
                       FROM conversation_summaries 
                       WHERE session_id = ?""",
                    (session_id,)
                )
                row = cursor.fetchone()
                if row:
                    return {
                        "summary": row[0],
                        "key_points": json.loads(row[1]) if row[1] else [],
                        "last_updated": row[2]
                    }
                return None
        except Exception as e:
            print(f"Error getting conversation summary: {e}")
            return None
    
    def clear_session(self, session_id: str) -> bool:
        """Clear all data for a session"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM conversations WHERE session_id = ?", (session_id,))
                cursor.execute("DELETE FROM context WHERE session_id = ?", (session_id,))
                cursor.execute("DELETE FROM conversation_summaries WHERE session_id = ?", (session_id,))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error clearing session: {e}")
            return False

# Create a singleton instance
memory_instance = RaidenMemory()