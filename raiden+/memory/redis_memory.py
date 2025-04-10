import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from redis import Redis
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage

class RaidenMemory:
    def __init__(self):
        self.redis_url = os.environ.get("UPSTASH_REDIS_REST_URL")
        self.redis_token = os.environ.get("UPSTASH_REDIS_REST_TOKEN")
        self.redis_ttl = int(os.environ.get("REDIS_MEMORY_TTL", "2592000"))  # 30 days default
        
        # Initialize Redis client
        self.redis = Redis.from_url(
            url=self.redis_url,
            password=self.redis_token,
            decode_responses=True
        )
    
    def save_conversation(self, session_id: str, messages: List[BaseMessage]) -> bool:
        """Save conversation history to Redis"""
        try:
            # Convert messages to serializable format
            serialized_msgs = []
            for msg in messages:
                msg_data = {
                    "type": msg.__class__.__name__,
                    "content": msg.content,
                    "timestamp": datetime.now().isoformat()
                }
                if hasattr(msg, 'tool_calls'):
                    msg_data["tool_calls"] = msg.tool_calls
                serialized_msgs.append(msg_data)
            
            # Save with TTL
            key = f"conversation:{session_id}"
            self.redis.setex(
                key,
                self.redis_ttl,
                json.dumps(serialized_msgs)
            )
            return True
        except Exception as e:
            print(f"Error saving conversation: {e}")
            return False
    
    def load_conversation(self, session_id: str) -> List[BaseMessage]:
        """Load conversation history from Redis"""
        try:
            key = f"conversation:{session_id}"
            data = self.redis.get(key)
            if not data:
                return []
            
            # Deserialize messages
            messages = []
            for msg_data in json.loads(data):
                if msg_data["type"] == "HumanMessage":
                    msg = HumanMessage(content=msg_data["content"])
                elif msg_data["type"] == "AIMessage":
                    msg = AIMessage(
                        content=msg_data["content"],
                        tool_calls=msg_data.get("tool_calls", [])
                    )
                elif msg_data["type"] == "SystemMessage":
                    msg = SystemMessage(content=msg_data["content"])
                messages.append(msg)
            return messages
        except Exception as e:
            print(f"Error loading conversation: {e}")
            return []
    
    def save_context(self, session_id: str, context: Dict[str, Any]) -> bool:
        """Save additional context for a session"""
        try:
            key = f"context:{session_id}"
            context["last_updated"] = datetime.now().isoformat()
            self.redis.setex(
                key,
                self.redis_ttl,
                json.dumps(context)
            )
            return True
        except Exception as e:
            print(f"Error saving context: {e}")
            return False
    
    def load_context(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load additional context for a session"""
        try:
            key = f"context:{session_id}"
            data = self.redis.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            print(f"Error loading context: {e}")
            return None
    
    def clear_session(self, session_id: str) -> bool:
        """Clear all data for a session"""
        try:
            self.redis.delete(f"conversation:{session_id}")
            self.redis.delete(f"context:{session_id}")
            return True
        except Exception as e:
            print(f"Error clearing session: {e}")
            return False
