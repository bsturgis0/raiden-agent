import os
from typing import Optional, List, Dict
from pathlib import Path
import json
from datetime import datetime

from langchain_core.tools import tool
from langchain_community.chat_message_histories import UpstashRedisChatMessageHistory
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage

try:
    from app import WORKSPACE_DIR, color_text
except ImportError:
    WORKSPACE_DIR = Path("./raiden_workspace_srv")
    WORKSPACE_DIR.mkdir(exist_ok=True)
    def color_text(text, color="WHITE"): print(f"[{color}] {text}"); return text

class ChatHistoryManager:
    """Manages chat history using Upstash Redis"""
    def __init__(self):
        self.url = os.environ.get("UPSTASH_REDIS_REST_URL")
        self.token = os.environ.get("UPSTASH_REDIS_REST_TOKEN")
        self.ttl = int(os.environ.get("UPSTASH_REDIS_TTL", "86400"))  # Default 24 hours
        
        if not self.url or not self.token:
            print(color_text("Warning: Upstash Redis credentials not configured. Using fallback storage.", "YELLOW"))
            
    def get_history(self, session_id: str) -> UpstashRedisChatMessageHistory:
        """Get chat history for a specific session"""
        return UpstashRedisChatMessageHistory(
            url=self.url,
            token=self.token,
            ttl=self.ttl,
            session_id=session_id
        )
        
    @staticmethod
    def serialize_message(msg: BaseMessage) -> Dict:
        """Serialize a message for storage"""
        return {
            "type": msg.__class__.__name__,
            "content": msg.content,
            "additional_kwargs": msg.additional_kwargs,
            "timestamp": datetime.now().isoformat()
        }
        
    @staticmethod
    def deserialize_message(data: Dict) -> BaseMessage:
        """Deserialize a message from storage"""
        msg_type = data["type"]
        content = data["content"]
        additional_kwargs = data.get("additional_kwargs", {})
        
        if msg_type == "HumanMessage":
            return HumanMessage(content=content, additional_kwargs=additional_kwargs)
        elif msg_type == "AIMessage":
            return AIMessage(content=content, additional_kwargs=additional_kwargs)
        elif msg_type == "SystemMessage":
            return SystemMessage(content=content, additional_kwargs=additional_kwargs)
        else:
            raise ValueError(f"Unknown message type: {msg_type}")

# Initialize global chat history manager
chat_manager = ChatHistoryManager()

@tool
def save_chat_history(session_id: str, messages: List[Dict]) -> str:
    """
    Saves chat messages to Upstash Redis storage.
    
    Args:
        session_id (str): Unique identifier for the chat session
        messages (List[Dict]): List of message dictionaries to store
    
    Returns:
        str: Confirmation message
    """
    try:
        history = chat_manager.get_history(session_id)
        
        # Clear existing messages for this session
        history.clear()
        
        # Add all messages
        for msg in messages:
            if msg["role"] == "human":
                history.add_user_message(msg["content"])
            elif msg["role"] == "assistant":
                history.add_ai_message(msg["content"])
            elif msg["role"] == "system":
                # Special handling for system messages
                history.messages.append(SystemMessage(content=msg["content"]))
                
        return f"Successfully saved {len(messages)} messages for session {session_id}"
        
    except Exception as e:
        return f"Error saving chat history: {str(e)}"

@tool
def load_chat_history(session_id: str) -> str:
    """
    Loads chat messages from Upstash Redis storage.
    
    Args:
        session_id (str): Unique identifier for the chat session
    
    Returns:
        str: JSON string containing the chat messages
    """
    try:
        history = chat_manager.get_history(session_id)
        messages = []
        
        for msg in history.messages:
            if isinstance(msg, HumanMessage):
                role = "human"
            elif isinstance(msg, AIMessage):
                role = "assistant"
            elif isinstance(msg, SystemMessage):
                role = "system"
            else:
                continue
                
            messages.append({
                "role": role,
                "content": msg.content,
                "additional_kwargs": msg.additional_kwargs
            })
            
        return json.dumps(messages, indent=2)
        
    except Exception as e:
        return f"Error loading chat history: {str(e)}"

@tool
def delete_chat_history(session_id: str) -> str:
    """
    Deletes chat history for a specific session.
    
    Args:
        session_id (str): Unique identifier for the chat session
    
    Returns:
        str: Confirmation message
    """
    try:
        history = chat_manager.get_history(session_id)
        history.clear()
        return f"Successfully deleted chat history for session {session_id}"
        
    except Exception as e:
        return f"Error deleting chat history: {str(e)}"