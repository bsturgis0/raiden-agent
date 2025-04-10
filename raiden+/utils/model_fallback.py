import os
import logging
from typing import Dict, Any, Optional, Callable, List, TypeVar
from langchain_core.language_models import BaseLLM
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_together import ChatTogether
from langchain_deepseek import ChatDeepSeek

T = TypeVar('T')

class ModelFallbackManager:
    def __init__(self):
        self.models = []
        self.current_model_index = 0
        
        # Setup logging
        logging.basicConfig(
            filename='model_fallback.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
    def initialize_models(self):
        """Initialize backup models in priority order"""
        # Clear existing models
        self.models = []
        
        # Add available models based on API keys
        if os.environ.get("GOOGLE_API_KEY"):
            self.models.append({
                "name": "google-gemini",
                "instance": ChatGoogleGenerativeAI(
                    model="gemini-2.0-flash",
                    temperature=0.7,
                    max_tokens=4096
                )
            })
            
        if os.environ.get("TOGETHER_API_KEY"):
            self.models.append({
                "name": "together-llama",
                "instance": ChatTogether(
                    model="meta-llama/Llama-3-70b-chat-hf",
                    temperature=0.7,
                    max_tokens=4096
                )
            })
            
        if os.environ.get("DEEPSEEK_API_KEY"):
            self.models.append({
                "name": "deepseek-chat",
                "instance": ChatDeepSeek(
                    model="deepseek-chat",
                    temperature=0.7,
                    max_tokens=4096
                )
            })
    
    async def execute_with_fallback(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """Execute a function with model fallback on failure"""
        if not self.models:
            raise RuntimeError("No fallback models available")
        
        last_error = None
        for model in self.models:
            try:
                # Update global LLM instance
                from app import selected_llm_instance, llm_name, llm_with_tools, available_tools_list
                selected_llm_instance = model["instance"]
                llm_name = model["name"]
                llm_with_tools = selected_llm_instance.bind_tools(available_tools_list)
                
                print(f"Trying fallback model: {model['name']}")
                result = await func(*args, **kwargs)
                return result
                
            except Exception as e:
                last_error = e
                print(f"Fallback model {model['name']} failed: {e}")
                continue
        
        raise RuntimeError(f"All fallback models failed. Last error: {last_error}")
