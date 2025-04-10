"""
JSON-RPC route handlers for the MCP server.

This module maps JSON-RPC method names to their corresponding handler functions.
"""
import logging
from typing import Dict, Any, Callable, Optional

# Import handlers
from ..handlers.hello_world import handle_hello_world
from ..handlers.background_removal import handle_background_removal
from ..handlers.inpainting import handle_inpainting
from ..handlers.style_transfer import handle_style_transfer, handle_get_styles
from ..handlers.upscale import handle_upscale
from ..handlers.feedback import handle_submit_feedback, handle_get_feedback
from ..handlers.gimp_api import handle_gimp_api
from ..handlers.image_analysis import handle_image_analysis
from ..handlers.ai_assistant import handle_ai_assistant
from ..handlers.mcp_protocol import handle_initialize, handle_shutdown
from ..mcp_integration import handle_mcp_operation, execute_gimp_commands, handle_mcp_close_session

# Setup logging
logger = logging.getLogger(__name__)

# Dictionary mapping method names to handler functions
HANDLERS = {
    # MCP Protocol methods
    "initialize": handle_initialize,
    "shutdown": handle_shutdown,
    
    # GIMP AI feature handlers
    "hello_world": handle_hello_world,
    "ai_background_removal": handle_background_removal,
    "ai_inpainting": handle_inpainting,
    "ai_style_transfer": handle_style_transfer,
    "get_available_styles": handle_get_styles,
    "ai_upscale": handle_upscale,
    "submit_feedback": handle_submit_feedback,
    "get_feedback": handle_get_feedback,
    "gimp_api": handle_gimp_api,
    "image_analysis": handle_image_analysis,
    "ai_assistant": handle_ai_assistant,
    
    # MCP-specific handlers for direct integration with AI systems
    "mcp_operation": handle_mcp_operation,
    "execute_gimp_commands": execute_gimp_commands,
    "mcp_close_session": handle_mcp_close_session,
    # Add more handlers as they are implemented
}

def get_handler(method: str) -> Optional[Callable]:
    """
    Get the handler function for a given method name.
    
    Args:
        method: The JSON-RPC method name
        
    Returns:
        The handler function or None if the method is not found
    """
    handler = HANDLERS.get(method)
    if not handler:
        logger.warning(f"Handler not found for method: {method}")
    return handler
