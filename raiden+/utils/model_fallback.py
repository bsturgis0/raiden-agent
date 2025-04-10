import os
import logging
from typing import Dict, Any, Optional
from langchain_core.language_models import BaseLLM
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_together import ChatTogether
from langchain_deepseek import ChatDeepSeek

class ModelFallbackManager:
    def __init__(self):
        self.models: Dict[str, BaseLLM] = {}
        self.current_model: Optional[str] = None
        self.fallback_order = ['groq', 'google', 'together', 'deepseek']
        
        # Setup logging
        logging.basicConfig(
            filename='model_fallback.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
    def initialize_models(self):
        """Initialize available models"""
        model_configs = {
            'groq': {
                'api_key': os.getenv('GROQ_API_KEY'),
                'class': ChatGroq,
                'params': {
                    'temperature': 0.7,
                    'model_name': "deepseek-r1-distill-llama-70b",
                    'max_tokens': 8192
                }
            },
            'google': {
                'api_key': os.getenv('GOOGLE_API_KEY'),
                'class': ChatGoogleGenerativeAI,
                'params': {
                    'model': "gemini-2.0-flash",
                    'temperature': 0.7,
                    'max_tokens': 4096
                }
            },
            'together': {
                'api_key': os.getenv('TOGETHER_API_KEY'),
                'class': ChatTogether,
                'params': {
                    'model': "meta-llama/Llama-3-70b-chat-hf",
                    'temperature': 0.7,
                    'max_tokens': 4096
                }
            },
            'deepseek': {
                'api_key': os.getenv('DEEPSEEK_API_KEY'),
                'class': ChatDeepSeek,
                'params': {
                    'model': "deepseek-chat",
                    'temperature': 0.7,
                    'max_tokens': 4096
                }
            }
        }
        
        for model_name, config in model_configs.items():
            if config['api_key']:
                try:
                    model = config['class'](**config['params'])
                    self.models[model_name] = model
                    logging.info(f"Initialized {model_name} model")
                except Exception as e:
                    logging.error(f"Failed to initialize {model_name}: {e}")
                    
        # Set initial model
        self.current_model = self.get_first_available_model()
        
    def get_first_available_model(self) -> Optional[str]:
        """Get first available model from fallback order"""
        for model_name in self.fallback_order:
            if model_name in self.models:
                return model_name
        return None
        
    def get_next_model(self) -> Optional[str]:
        """Get next available model in fallback order"""
        if not self.current_model:
            return self.get_first_available_model()
            
        current_index = self.fallback_order.index(self.current_model)
        for model_name in self.fallback_order[current_index + 1:]:
            if model_name in self.models:
                return model_name
        return None
        
    async def execute_with_fallback(self, func, *args, **kwargs):
        """Execute function with model fallback on failure"""
        if not self.current_model:
            raise RuntimeError("No models available")
            
        attempts = 0
        max_attempts = len(self.models)
        
        while attempts < max_attempts:
            try:
                model = self.models[self.current_model]
                result = await func(model, *args, **kwargs)
                return result
            except Exception as e:
                logging.error(f"Model {self.current_model} failed: {e}")
                next_model = self.get_next_model()
                
                if next_model:
                    logging.info(f"Falling back to {next_model}")
                    self.current_model = next_model
                else:
                    logging.error("No more models available")
                    raise RuntimeError("All models failed")
                    
                attempts += 1
                
        raise RuntimeError("All fallback attempts exhausted")
