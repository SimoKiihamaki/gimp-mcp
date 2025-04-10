"""
Style transfer handler for the MCP server.

This module handles style transfer requests from the GIMP plugin.
"""
import logging
import uuid
from typing import Dict, Any

# Import the style transfer model
from ..models.style_transfer.fast_style_impl import process_style_transfer, get_available_styles

# Import tasks_progress from app
from ..app import tasks_progress

logger = logging.getLogger(__name__)

async def handle_style_transfer(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle a style transfer request.
    
    Args:
        params: Parameters for the request, including:
            - image_data (str): Base64-encoded image data
            - style_name (str): Name of the style to apply (e.g., "starry_night")
            - strength (float, optional): Style strength (0.0-1.0, default: 1.0)
            - use_gpu (bool, optional): Whether to use GPU for inference (default: True)
            - task_id (str, optional): Task ID for progress tracking
            
    Returns:
        dict: Response with processed image data
    """
    try:
        # Extract parameters
        image_data = params.get("image_data")
        if not image_data:
            raise ValueError("Missing required parameter: image_data")
        
        style_name = params.get("style_name", "starry_night")
        strength = float(params.get("strength", 1.0))
        use_gpu = params.get("use_gpu", True)
        
        # Validate parameters
        if strength < 0.0 or strength > 1.0:
            raise ValueError("Style strength must be between 0.0 and 1.0")
        
        # Generate a task ID for progress tracking if not provided
        task_id = params.get("task_id", str(uuid.uuid4()))
        
        logger.info(f"Processing style transfer with style={style_name}, strength={strength}, use_gpu={use_gpu}, task_id={task_id}")
        
        # Initialize progress
        tasks_progress[task_id] = {"progress": 0.1, "status": "initializing"}
        
        # Update to loading model status
        tasks_progress[task_id] = {"progress": 0.2, "status": "loading model"}
        
        # Update to processing status
        tasks_progress[task_id] = {"progress": 0.4, "status": "applying style"}
        
        # Process the style transfer
        result_image_data = process_style_transfer(
            image_data=image_data,
            style_name=style_name,
            strength=strength,
            use_gpu=use_gpu
        )
        
        # Update progress to complete
        tasks_progress[task_id] = {"progress": 1.0, "status": "completed"}
        
        # Return the result
        return {
            "image_data": result_image_data,
            "status": "success",
            "task_id": task_id
        }
    except Exception as e:
        logger.exception(f"Error in style transfer: {e}")
        
        # Update progress to error state if task_id exists
        if 'task_id' in locals():
            tasks_progress[task_id] = {"progress": 1.0, "status": f"error: {str(e)}"}
        
        raise RuntimeError(f"Style transfer failed: {str(e)}")

async def handle_get_styles(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle a request to get available styles.
    
    Args:
        params: Parameters for the request (not used)
            
    Returns:
        dict: Response with available styles
    """
    try:
        # Get available styles
        styles = get_available_styles()
        
        # Return the result
        return {
            "styles": styles,
            "status": "success"
        }
    except Exception as e:
        logger.exception(f"Error getting styles: {e}")
        raise RuntimeError(f"Failed to get styles: {str(e)}")
