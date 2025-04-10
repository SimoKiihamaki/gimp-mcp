"""
MCP Integration Module for GIMP AI Integration.

This module provides specialized functionality for seamless integration with the
Model Context Protocol (MCP), allowing AI systems like Claude Desktop to
directly control GIMP and perform image editing operations.
"""
import logging
import json
import base64
from typing import Dict, Any, List, Optional
import os
import tempfile
from io import BytesIO

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

# Cache of open images to maintain state between calls
OPEN_IMAGES = {}

class MCPImageSession:
    """
    Class to manage an image session for MCP interactions.
    Maintains state between multiple API calls.
    """
    def __init__(self, session_id: str, image_data: Optional[bytes] = None, name: str = "untitled.png"):
        self.session_id = session_id
        self.name = name
        self.history = []  # Operation history
        self.layers = []  # Layer information
        self.temp_files = []  # Temporary files to clean up
        
        # If image data is provided, initialize with it
        if image_data:
            self.image = Image.open(BytesIO(image_data))
        else:
            # Create a blank 1000x1000 image with transparent background
            self.image = Image.new("RGBA", (1000, 1000), (0, 0, 0, 0))
        
        # Initialize layer information
        self.layers = [{
            "id": 0,
            "name": "Background",
            "visible": True,
            "opacity": 100,
            "mode": "normal"
        }]
    
    def add_operation(self, operation: str, params: Dict[str, Any], result: Dict[str, Any]):
        """Add an operation to the history"""
        self.history.append({
            "operation": operation,
            "params": params,
            "result": result,
            "timestamp": time.time()
        })
    
    def get_image_data(self, format: str = "PNG") -> bytes:
        """Get the current image data as bytes"""
        buffer = BytesIO()
        self.image.save(buffer, format=format)
        return buffer.getvalue()
    
    def get_image_base64(self, format: str = "PNG") -> str:
        """Get the current image as a base64 string"""
        return base64.b64encode(self.get_image_data(format)).decode('utf-8')
    
    def apply_operation(self, operation: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Apply an operation to the image"""
        # This would call the appropriate operation on the image
        # For now, we'll implement a few basic operations
        
        result = {"success": False, "message": "Operation not implemented"}
        
        if operation == "create_new_image":
            width = params.get("width", 1000)
            height = params.get("height", 1000)
            color = params.get("color", (0, 0, 0, 0))
            
            self.image = Image.new("RGBA", (width, height), color)
            result = {
                "success": True,
                "message": f"Created new {width}x{height} image",
                "width": width,
                "height": height
            }
        
        elif operation == "resize_image":
            width = params.get("width", self.image.width)
            height = params.get("height", self.image.height)
            
            self.image = self.image.resize((width, height), Image.LANCZOS)
            result = {
                "success": True,
                "message": f"Resized image to {width}x{height}",
                "width": width,
                "height": height
            }
        
        elif operation == "crop_image":
            x = params.get("x", 0)
            y = params.get("y", 0)
            width = params.get("width", self.image.width - x)
            height = params.get("height", self.image.height - y)
            
            self.image = self.image.crop((x, y, x + width, y + height))
            result = {
                "success": True,
                "message": f"Cropped image to region {x},{y},{width},{height}",
                "width": width,
                "height": height
            }
        
        elif operation == "adjust_brightness_contrast":
            from PIL import ImageEnhance
            
            brightness = params.get("brightness", 0) / 100 + 1.0  # Convert to factor
            contrast = params.get("contrast", 0) / 100 + 1.0  # Convert to factor
            
            if brightness != 1.0:
                enhancer = ImageEnhance.Brightness(self.image)
                self.image = enhancer.enhance(brightness)
            
            if contrast != 1.0:
                enhancer = ImageEnhance.Contrast(self.image)
                self.image = enhancer.enhance(contrast)
            
            result = {
                "success": True,
                "message": f"Adjusted brightness to {brightness} and contrast to {contrast}"
            }
        
        elif operation == "apply_blur":
            from PIL import ImageFilter
            
            radius = params.get("radius", 5.0)
            self.image = self.image.filter(ImageFilter.GaussianBlur(radius=radius))
            
            result = {
                "success": True,
                "message": f"Applied Gaussian blur with radius {radius}"
            }
        
        elif operation == "save_image":
            format = params.get("format", "PNG")
            quality = params.get("quality", 95)
            
            # For demonstration, just update the result
            result = {
                "success": True,
                "message": f"Image saved in {format} format with quality {quality}",
                "image_data": self.get_image_base64(format)
            }
        
        # Add the operation to history
        self.add_operation(operation, params, result)
        
        return result
    
    def cleanup(self):
        """Clean up temporary files"""
        for file_path in self.temp_files:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                logger.error(f"Error cleaning up temp file {file_path}: {e}")

async def handle_mcp_operation(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle an MCP operation request.
    
    This function works as a higher-level handler specifically designed for
    MCP interactions, allowing AI systems like Claude to directly control GIMP.
    
    Args:
        params: Parameters for the request, including:
            - operation (str): Name of the operation to perform
            - session_id (str, optional): Session ID for persistent state
            - image_data (str, optional): Base64-encoded image data for new sessions
            - [Additional parameters specific to the operation]
            
    Returns:
        dict: Response with operation results and session information
    """
    try:
        # Extract the operation name
        operation = params.get("operation")
        if not operation:
            raise ValueError("Missing required parameter: operation")
        
        # Get or create session
        session_id = params.get("session_id")
        if not session_id:
            # Generate a new session ID
            session_id = str(uuid.uuid4())
            
            # Check if image data is provided for a new session
            image_data = None
            if "image_data" in params:
                image_data_b64 = params.get("image_data")
                image_data = base64.b64decode(image_data_b64)
            
            # Create a new session
            OPEN_IMAGES[session_id] = MCPImageSession(session_id, image_data)
            logger.info(f"Created new image session: {session_id}")
        elif session_id not in OPEN_IMAGES:
            raise ValueError(f"Invalid session ID: {session_id}")
        
        # Get the session
        session = OPEN_IMAGES[session_id]
        
        # Apply the operation
        result = session.apply_operation(operation, params)
        
        # Add session information to the result
        result["session_id"] = session_id
        result["image_dimensions"] = {
            "width": session.image.width,
            "height": session.image.height
        }
        
        # Include image data if requested or if it's a save operation
        if operation == "save_image" or params.get("include_image_data", False):
            result["image_data"] = session.get_image_base64()
        
        return result
    
    except Exception as e:
        logger.exception(f"Error in MCP operation: {e}")
        raise RuntimeError(f"MCP operation failed: {str(e)}")

async def execute_gimp_commands(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a sequence of GIMP commands.
    
    This function is designed to execute a sequence of GIMP operations
    in a single request, making it easier for AI systems to perform
    complex image editing tasks.
    
    Args:
        params: Parameters for the request, including:
            - commands (list): List of commands to execute
            - image_data (str, optional): Base64-encoded image data
            - session_id (str, optional): Session ID for persistent state
            
    Returns:
        dict: Response with execution results
    """
    try:
        commands = params.get("commands", [])
        if not commands:
            raise ValueError("Missing required parameter: commands")
        
        # Get or create session
        session_id = params.get("session_id")
        if not session_id:
            # Generate a new session ID
            session_id = str(uuid.uuid4())
            
            # Check if image data is provided for a new session
            image_data = None
            if "image_data" in params:
                image_data_b64 = params.get("image_data")
                image_data = base64.b64decode(image_data_b64)
            
            # Create a new session
            OPEN_IMAGES[session_id] = MCPImageSession(session_id, image_data)
            logger.info(f"Created new image session: {session_id}")
        elif session_id not in OPEN_IMAGES:
            raise ValueError(f"Invalid session ID: {session_id}")
        
        # Get the session
        session = OPEN_IMAGES[session_id]
        
        # Execute commands
        results = []
        for cmd in commands:
            operation = cmd.get("operation")
            cmd_params = cmd.get("params", {})
            
            # Execute the command
            result = session.apply_operation(operation, cmd_params)
            results.append(result)
        
        # Return results
        return {
            "session_id": session_id,
            "success": True,
            "results": results,
            "image_dimensions": {
                "width": session.image.width,
                "height": session.image.height
            },
            "image_data": session.get_image_base64() if params.get("include_image_data", False) else None
        }
    
    except Exception as e:
        logger.exception(f"Error executing GIMP commands: {e}")
        raise RuntimeError(f"Command execution failed: {str(e)}")

async def handle_mcp_close_session(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Close an MCP image session.
    
    Args:
        params: Parameters for the request, including:
            - session_id (str): Session ID to close
            
    Returns:
        dict: Response with close status
    """
    try:
        session_id = params.get("session_id")
        if not session_id:
            raise ValueError("Missing required parameter: session_id")
        
        if session_id in OPEN_IMAGES:
            # Clean up the session
            session = OPEN_IMAGES[session_id]
            session.cleanup()
            
            # Remove from open images
            del OPEN_IMAGES[session_id]
            
            return {
                "success": True,
                "message": f"Session {session_id} closed successfully"
            }
        else:
            return {
                "success": False,
                "message": f"Session {session_id} not found"
            }
    
    except Exception as e:
        logger.exception(f"Error closing MCP session: {e}")
        raise RuntimeError(f"Failed to close session: {str(e)}")

def cleanup_all_sessions():
    """Clean up all open sessions. Called when the server shuts down."""
    for session_id, session in OPEN_IMAGES.items():
        try:
            session.cleanup()
            logger.info(f"Cleaned up session {session_id}")
        except Exception as e:
            logger.error(f"Error cleaning up session {session_id}: {e}")
    
    OPEN_IMAGES.clear()
