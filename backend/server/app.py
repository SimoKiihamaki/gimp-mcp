"""
MCP Server main application file.

This is the entry point for the MCP server that handles JSON-RPC requests from the GIMP plugin.
"""
import logging
import os
from typing import Dict, Any

import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    logger.warning("python-dotenv not installed, skipping .env file loading")

# Check if authentication is enabled
enable_auth = os.getenv("MCP_ENABLE_AUTH", "false").lower() == "true"

# Import authentication utilities
if enable_auth:
    from .utils.auth import get_api_key, api_key_middleware_factory

# Initialize FastAPI app
app = FastAPI(
    title="GIMP AI Integration MCP Server",
    description="MCP Server for AI-powered GIMP operations",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("MCP_ALLOW_ORIGINS", "*").split(","),  # For development, restrict this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add authentication middleware if enabled
if enable_auth:
    app.middleware("http")(api_key_middleware_factory(enable_auth=True))
    logger.info("API Key authentication is enabled")
else:
    logger.info("Authentication is disabled")

# Define JSON-RPC request model
class JsonRpcRequest(BaseModel):
    jsonrpc: str
    method: str
    params: Dict[str, Any]
    id: int

# Define JSON-RPC response model
class JsonRpcResponse(BaseModel):
    jsonrpc: str = "2.0"
    result: Dict[str, Any] = None
    error: Dict[str, Any] = None
    id: int

# Simple in-memory store for task progress (replace with a more robust solution later)
tasks_progress = {}

@app.post("/jsonrpc")
async def handle_jsonrpc(request: JsonRpcRequest):
    """
    Handle JSON-RPC requests from the GIMP plugin.
    
    Args:
        request: The JSON-RPC request object
        
    Returns:
        JsonRpcResponse: The JSON-RPC response
    """
    logger.info(f"Received JSON-RPC request: {request.method}")
    
    # Import handlers here to avoid circular imports
    from .routes.json_rpc import get_handler
    
    try:
        # Get the appropriate handler for the method
        handler = get_handler(request.method)
        if not handler:
            return JsonRpcResponse(
                error={"code": -32601, "message": f"Method '{request.method}' not found"},
                id=request.id
            )
        
        # Call the handler with the params
        result = await handler(request.params)
        
        # Return the result
        return JsonRpcResponse(
            result=result,
            id=request.id
        )
    except Exception as e:
        logger.exception(f"Error handling request: {e}")
        return JsonRpcResponse(
            error={"code": -32000, "message": str(e)},
            id=request.id
        )

import asyncio  # Add this import for asyncio.sleep

@app.get("/progress/{task_id}")
async def get_progress(task_id: str):
    """
    Get progress updates for a long-running task using SSE.
    
    Args:
        task_id: The ID of the task to get progress for
        
    Returns:
        EventSourceResponse: SSE response with progress updates
    """
    if task_id not in tasks_progress:
        tasks_progress[task_id] = {"progress": 0, "status": "initializing"}
    
    async def event_generator():
        while True:
            if task_id in tasks_progress:
                yield {"data": tasks_progress[task_id]}
            await asyncio.sleep(0.5)
    
    return EventSourceResponse(event_generator())

@app.get("/")
async def root():
    """Root endpoint for health check"""
    # Import auth utilities here to avoid circular imports
    from .utils.auth import get_current_auth_status
    return {
        "status": "ok", 
        "message": "GIMP AI Integration MCP Server is running",
        "version": "0.1.0",
        "auth": get_current_auth_status()
    }

@app.post("/generate_api_key")
async def generate_key(name: str, expires_days: int = 30):
    """
    Generate a new API key (development only, protect in production)
    """
    if enable_auth:
        # Only allow this in development mode or local networks
        if os.getenv("MCP_ENV", "development") == "production":
            raise HTTPException(status_code=403, detail="This endpoint is disabled in production mode")
        
        from .utils.auth import generate_api_key
        key = generate_api_key(name, expires_days)
        return {"key": key, "name": name, "expires_days": expires_days}
    else:
        raise HTTPException(status_code=400, detail="Authentication is not enabled")

if __name__ == "__main__":    
    # Get host and port from environment variables or use defaults
    host = os.getenv("MCP_SERVER_HOST", "127.0.0.1")
    port = int(os.getenv("MCP_SERVER_PORT", "8000"))
    
    # Check if we should use HTTPS
    use_https = os.getenv("MCP_USE_HTTPS", "false").lower() == "true"
    
    if use_https:
        # Check if SSL certificate and key files exist
        ssl_certfile = os.getenv("MCP_SSL_CERTFILE")
        ssl_keyfile = os.getenv("MCP_SSL_KEYFILE")
        
        if not ssl_certfile or not ssl_keyfile:
            logger.error("HTTPS is enabled but certificate or key file is not specified")
            logger.error("Please set MCP_SSL_CERTFILE and MCP_SSL_KEYFILE environment variables")
            sys.exit(1)
        
        if not os.path.exists(ssl_certfile) or not os.path.exists(ssl_keyfile):
            logger.error(f"SSL certificate ({ssl_certfile}) or key file ({ssl_keyfile}) not found")
            sys.exit(1)
        
        logger.info(f"Starting MCP server with HTTPS on {host}:{port}")
        uvicorn.run(
            app, 
            host=host, 
            port=port,
            ssl_certfile=ssl_certfile,
            ssl_keyfile=ssl_keyfile
        )
    else:
        logger.info(f"Starting MCP server on {host}:{port}")
        uvicorn.run(app, host=host, port=port)
