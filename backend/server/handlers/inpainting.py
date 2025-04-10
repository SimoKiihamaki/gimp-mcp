"""
Inpainting handler for the MCP server.

This module handles inpainting requests from the GIMP plugin.
"""
import logging
import uuid
from typing import Dict, Any

# Import the LaMa inpainting model
from ..models.inpainting.lama import process_inpainting

# Import tasks_progress from app
from ..app import tasks_progress

logger = logging.getLogger(__name__)

async def handle_inpainting(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle an inpainting request.
    
    Args:
        params: Parameters for the request, including:
            - image_data (str): Base64-encoded image data
            - mask_data (str): Base64-encoded mask data (white indicates areas to inpaint)
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
        
        mask_data = params.get("mask_data")
        if not mask_data:
            raise ValueError("Missing required parameter: mask_data")
        
        use_gpu = params.get("use_gpu", True)
        
        # Generate a task ID for progress tracking if not provided
        task_id = params.get("task_id", str(uuid.uuid4()))
        
        logger.info(f"Processing inpainting request with use_gpu={use_gpu}, task_id={task_id}")
        
        # Initialize progress
        tasks_progress[task_id] = {"progress": 0.1, "status": "initializing"}
        
        # Update to loading model status
        tasks_progress[task_id] = {"progress": 0.2, "status": "loading model"}
        
        # Update to processing status
        tasks_progress[task_id] = {"progress": 0.4, "status": "processing"}
        
        # Process the inpainting
        result_image_data = process_inpainting(
            image_data=image_data,
            mask_data=mask_data,
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
        logger.exception(f"Error in inpainting: {e}")
        
        # Update progress to error state if task_id exists
        if 'task_id' in locals():
            tasks_progress[task_id] = {"progress": 1.0, "status": f"error: {str(e)}"}
        
        raise RuntimeError(f"Inpainting failed: {str(e)}")
