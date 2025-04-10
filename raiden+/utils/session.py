from uuid import uuid4
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import Request
from redis import Redis
import json

class SessionManager:
    def __init__(self, redis_url: str, expiry: int = 3600):
        self.redis = Redis.from_url(redis_url)
        self.expiry = expiry
    
    def create_session(self, user_data: Dict[str, Any] = None) -> str:
        session_id = str(uuid4())
        session_data = {
            "created_at": datetime.utcnow().isoformat(),
            "last_accessed": datetime.utcnow().isoformat(),
            "user_data": user_data or {}
        }
        self.redis.setex(
            f"session:{session_id}",
            self.expiry,
            json.dumps(session_data)
        )
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        data = self.redis.get(f"session:{session_id}")
        if not data:
            return None
        
        session_data = json.loads(data)
        session_data["last_accessed"] = datetime.utcnow().isoformat()
        self.redis.setex(
            f"session:{session_id}",
            self.expiry,
            json.dumps(session_data)
        )
        return session_data
    
    def update_session(self, session_id: str, data: Dict[str, Any]) -> bool:
        existing = self.get_session(session_id)
        if not existing:
            return False
            
        existing["user_data"].update(data)
        existing["last_accessed"] = datetime.utcnow().isoformat()
        
        self.redis.setex(
            f"session:{session_id}",
            self.expiry,
            json.dumps(existing)
        )
        return True
    
    def delete_session(self, session_id: str) -> bool:
        return bool(self.redis.delete(f"session:{session_id}"))

    async def verify_session(self, request: Request) -> Optional[Dict[str, Any]]:
        session_id = request.cookies.get("session_id")
        if not session_id:
            return None
        return self.get_session(session_id)

    def clear_session(self, session_id: str) -> bool:
        """Clears all data associated with a session."""
        try:
            # Clear session data
            self.redis.delete(f"session:{session_id}")
            
            # Clear conversation history
            self.redis.delete(f"conversation:{session_id}")
            
            # Clear any associated tool outputs
            self.redis.delete(f"tooloutput:{session_id}")
            
            # Clear any temporary data
            pattern = f"temp:{session_id}:*"
            temp_keys = self.redis.keys(pattern)
            if temp_keys:
                self.redis.delete(*temp_keys)
                
            return True
        except Exception as e:
            print(f"Error clearing session {session_id}: {e}")
            return False
    
    def clear_all_sessions(self) -> bool:
        """Clears all sessions and associated data (admin only)."""
        try:
            # Get all session keys
            session_pattern = "session:*"
            session_keys = self.redis.keys(session_pattern)
            
            # Get all conversation keys
            conv_pattern = "conversation:*"
            conv_keys = self.redis.keys(conv_pattern)
            
            # Get all tool output keys
            tool_pattern = "tooloutput:*"
            tool_keys = self.redis.keys(tool_pattern)
            
            # Get all temporary data keys
            temp_pattern = "temp:*"
            temp_keys = self.redis.keys(temp_pattern)
            
            # Combine all keys
            all_keys = session_keys + conv_keys + tool_keys + temp_keys
            
            if all_keys:
                self.redis.delete(*all_keys)
            
            return True
        except Exception as e:
            print(f"Error clearing all sessions: {e}")
            return False
