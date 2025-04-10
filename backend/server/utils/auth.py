"""
Authentication utilities for the MCP server.

This module provides authentication middleware and utility functions
for securing the MCP server when exposed externally.
"""
import os
import logging
import secrets
import time
from typing import Optional, Dict, Callable, Any
from fastapi import Request, HTTPException, Depends
from fastapi.security import APIKeyHeader

logger = logging.getLogger(__name__)

# API key header
X_API_KEY = APIKeyHeader(name="X-API-Key")

# In-memory key store with expiration (for demonstration purposes)
# In a production environment, use a more robust storage solution
API_KEYS = {}  # Format: {key: {"expires": timestamp, "name": "user name"}}

def generate_api_key(name: str, expires_days: int = 30) -> str:
    """
    Generate a new API key.
    
    Args:
        name: Name or identifier for the key owner
        expires_days: Number of days until the key expires
        
    Returns:
        str: The generated API key
    """
    key = secrets.token_urlsafe(32)
    expires = time.time() + (expires_days * 24 * 60 * 60)
    
    # Store the key
    API_KEYS[key] = {
        "expires": expires,
        "name": name
    }
    
    logger.info(f"Generated new API key for '{name}', expires in {expires_days} days")
    return key

def is_api_key_valid(key: str) -> bool:
    """
    Check if an API key is valid.
    
    Args:
        key: The API key to check
        
    Returns:
        bool: True if the key is valid, False otherwise
    """
    if key not in API_KEYS:
        return False
    
    # Check if the key has expired
    key_info = API_KEYS[key]
    if time.time() > key_info["expires"]:
        # Remove expired key
        del API_KEYS[key]
        return False
    
    return True

async def get_api_key(api_key: str = Depends(X_API_KEY)) -> str:
    """
    Validate the API key.
    
    Args:
        api_key: The API key from the request header
        
    Returns:
        str: The API key if valid
        
    Raises:
        HTTPException: If the API key is invalid
    """
    if is_api_key_valid(api_key):
        return api_key
    raise HTTPException(status_code=401, detail="Invalid or expired API key")

def load_api_keys_from_env() -> None:
    """
    Load API keys from environment variables.
    
    Looks for environment variables in the format MCP_API_KEY_<NAME>=<KEY>
    and adds them to the API_KEYS dictionary.
    """
    for key, value in os.environ.items():
        if key.startswith("MCP_API_KEY_") and value:
            name = key[13:]  # Remove "MCP_API_KEY_" prefix
            API_KEYS[value] = {
                "expires": float("inf"),  # Never expires
                "name": name
            }
            logger.info(f"Loaded API key for '{name}' from environment")

def api_key_auth_middleware_factory(enable_auth: bool = False) -> Callable:
    """
    Create a middleware for API key authentication.
    
    Args:
        enable_auth: Whether to enable authentication
        
    Returns:
        Callable: Middleware function
    """
    async def api_key_middleware(request: Request, call_next):
        # Skip authentication if disabled or for specific paths
        if not enable_auth or request.url.path == "/":
            return await call_next(request)
        
        # Check for API key in header
        api_key = request.headers.get("X-API-Key")
        if not api_key or not is_api_key_valid(api_key):
            return HTTPException(status_code=401, detail="Invalid or missing API key")
        
        return await call_next(request)
    
    return api_key_middleware

def get_current_auth_status() -> Dict[str, Any]:
    """
    Get the current authentication status.
    
    Returns:
        dict: Authentication status information
    """
    return {
        "enabled": os.getenv("MCP_ENABLE_AUTH", "false").lower() == "true",
        "active_keys": len(API_KEYS),
        "auth_type": "API Key"
    }

# Initialize by loading any API keys defined in environment variables
load_api_keys_from_env()
