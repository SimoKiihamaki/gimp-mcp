"""
Background removal handler for the MCP server.

This module handles background removal requests from the GIMP plugin.
"""
import logging
import uuid
import asyncio
from typing import Dict, Any

# Import the U2Net model
from ..models.background_removal.u2net import process_background_removal

# Import tasks_progress from app
from ..app import tasks_progress

logger = logging.getLogger(__name__)

async def handle_background_removal(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle a background removal request.
    
    Args:
        params: Parameters for the request, including:
            - image_data (str): Base64-encoded image data
            - threshold (float, optional): Threshold for mask binarization (default: 0.5)
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
        
        threshold = params.get("threshold", 0.5)
        use_gpu = params.get("use_gpu", True)
        
        # Generate a task ID for progress tracking if not provided
        task_id = params.get("task_id", str(uuid.uuid4()))
        
        logger.info(f"Processing background removal with threshold={threshold}, use_gpu={use_gpu}, task_id={task_id}")
        
        # Initialize progress
        tasks_progress[task_id] = {"progress": 0.1, "status": "initializing"}
        
        # Run the processing in a background task to allow for progress updates
        # For this example, we'll simulate progress updates
        tasks_progress[task_id] = {"progress": 0.2, "status": "loading model"}
        
        # Update to processing status
        tasks_progress[task_id] = {"progress": 0.4, "status": "processing"}
        
        # Process the image
        result_image_data = process_background_removal(
            image_data=image_data,
            threshold=threshold,
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
        logger.exception(f"Error in background removal: {e}")
        
        # Update progress to error state if task_id exists
        if 'task_id' in locals():
            tasks_progress[task_id] = {"progress": 1.0, "status": f"error: {str(e)}"}
        
        raise RuntimeError(f"Background removal failed: {str(e)}")
