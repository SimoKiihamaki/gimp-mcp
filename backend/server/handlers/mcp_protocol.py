"""
MCP Protocol handlers for implementing the Model Context Protocol standard.

This module provides handlers for MCP protocol-specific methods like 'initialize'.
"""
import logging
from typing import Dict, Any, List, Optional
import sys

logger = logging.getLogger(__name__)

async def handle_initialize(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle the MCP initialize method.
    
    This is the first method called by an MCP client to establish capabilities
    and protocol version compatibility.
    
    Args:
        params: Parameters from the client, including:
            - protocolVersion: The MCP protocol version supported by the client
            - capabilities: Client capabilities
            - clientInfo: Information about the client
            
    Returns:
        Dict containing server capabilities and information
    """
    logger.info(f"Handling MCP initialize request with params: {params}")
    
    # Extract client information
    protocol_version = params.get("protocolVersion", "unknown")
    client_info = params.get("clientInfo", {})
    client_name = client_info.get("name", "unknown")
    client_version = client_info.get("version", "unknown")
    
    logger.info(f"Client: {client_name} {client_version}, Protocol: {protocol_version}")
    
    # Get a list of supported methods from our JSON-RPC handlers
    # We need to import here to avoid circular imports
    from ..routes.json_rpc import HANDLERS
    supported_methods = list(HANDLERS.keys())
    
    # Additional capabilities specific to this server
    server_capabilities = {
        "supportsImageProcessing": True,
        "supportsStyleTransfer": True,
        "supportsInpainting": True,
        "supportsBackgroundRemoval": True,
        "supportsUpscaling": True
    }
    
    # Return the server initialization response
    return {
        "protocolVersion": protocol_version,  # We'll support whatever version the client requested
        "serverInfo": {
            "name": "GIMP AI Integration MCP Server",
            "version": "0.1.0",
            "implementation": "GIMP-AI-Integration",
            "pythonVersion": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        },
        "capabilities": server_capabilities,
        "supportedMethods": supported_methods
    }

async def handle_shutdown(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle the MCP shutdown method.
    
    This method allows clients to gracefully terminate the connection.
    
    Args:
        params: Parameters for shutdown (usually empty)
            
    Returns:
        Dict indicating shutdown acknowledged
    """
    logger.info("Client requested shutdown")
    
    return {
        "shutdown": "acknowledged"
    }
