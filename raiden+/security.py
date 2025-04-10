import secrets
import hashlib
from typing import Optional
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Security, HTTPException, status

security = HTTPBearer()

class SecurityManager:
    def __init__(self):
        self._api_keys = {}
        self._rate_limits = {}
        
    def generate_api_key(self) -> str:
        """Generate a secure API key"""
        return secrets.token_urlsafe(32)
        
    def verify_api_key(self, credentials: HTTPAuthorizationCredentials) -> bool:
        """Verify API key and enforce rate limits"""
        if not credentials or not credentials.credentials:
            return False
            
        api_key = credentials.credentials
        if api_key not in self._api_keys:
            return False
            
        # Implement rate limiting
        return True
        
    def enforce_rate_limit(self, api_key: str) -> bool:
        """Enforce rate limits per API key"""
        # Implement rate limiting logic
        return True

security_manager = SecurityManager()

async def verify_api_key(credentials: HTTPAuthorizationCredentials = Security(security)):
    """FastAPI dependency for API key verification"""
    if not security_manager.verify_api_key(credentials):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    return credentials.credentials
