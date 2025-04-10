"""
Hello World handler for testing the MCP server.

This is a simple handler that returns a greeting message.
"""
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

async def handle_hello_world(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle a hello_world request.
    
    Args:
        params: Parameters for the request (e.g., {"name": "User"})
        
    Returns:
        dict: Response with a greeting message
    """
    name = params.get("name", "World")
    logger.info(f"Handling hello_world request for {name}")
    
    return {
        "message": f"Hello, {name}! Welcome to the GIMP AI Integration MCP Server.",
        "status": "success"
    }
