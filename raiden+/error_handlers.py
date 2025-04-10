from fastapi import Request, status
from fastapi.responses import JSONResponse
import traceback
import sys
from typing import Dict, Any

async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle uncaught exceptions"""
    error_id = generate_error_id()
    
    # Log the error with full traceback
    error_details = {
        "error_id": error_id,
        "endpoint": str(request.url),
        "method": request.method,
        "traceback": traceback.format_exception(*sys.exc_info())
    }
    
    # Log to error monitoring service
    await log_error(error_details)
    
    # User-facing response
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "An unexpected error occurred",
            "error_id": error_id
        }
    )

async def rate_limit_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle rate limit exceptions"""
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "error": "Rate limit exceeded",
            "retry_after": 60  # seconds
        }
    )
