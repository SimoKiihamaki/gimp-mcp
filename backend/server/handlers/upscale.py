"""
Image Upscaling handler for the MCP server.

This module handles image upscaling requests from the GIMP plugin.
"""
import logging
import uuid
from typing import Dict, Any

# Import the upscaling model
from ..models.upscale.esrgan import process_upscaling

# Import tasks_progress from app
from ..app import tasks_progress

logger = logging.getLogger(__name__)

async def handle_upscale(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle an image upscaling request.
    
    Args:
        params: Parameters for the request, including:
            - image_data (str): Base64-encoded image data
            - scale_factor (int, optional): Scale factor (2, 4, or 8, default: 2)
            - denoise_level (float, optional): Denoise level (0.0-1.0, default: 0.0)
            - sharpen (bool, optional): Whether to apply sharpening (default: False)
            - use_gpu (bool, optional): Whether to use GPU for inference (default: True)
            - task_id (str, optional): Task ID for progress tracking
            
    Returns:
        dict: Response with upscaled image data
    """
    try:
        # Extract parameters
        image_data = params.get("image_data")
        if not image_data:
            raise ValueError("Missing required parameter: image_data")
        
        scale_factor = int(params.get("scale_factor", 2))
        if scale_factor not in [2, 4, 8]:
            raise ValueError("Scale factor must be 2, 4, or 8")
        
        denoise_level = float(params.get("denoise_level", 0.0))
        if denoise_level < 0.0 or denoise_level > 1.0:
            raise ValueError("Denoise level must be between 0.0 and 1.0")
        
        sharpen = bool(params.get("sharpen", False))
        use_gpu = bool(params.get("use_gpu", True))
        
        # Generate a task ID for progress tracking if not provided
        task_id = params.get("task_id", str(uuid.uuid4()))
        
        logger.info(f"Processing upscaling with scale_factor={scale_factor}, denoise_level={denoise_level}, "
                   f"sharpen={sharpen}, use_gpu={use_gpu}, task_id={task_id}")
        
        # Initialize progress
        tasks_progress[task_id] = {"progress": 0.1, "status": "initializing"}
        
        # Update to loading model status
        tasks_progress[task_id] = {"progress": 0.2, "status": "loading model"}
        
        # Update to processing status
        tasks_progress[task_id] = {"progress": 0.4, "status": "upscaling image"}
        
        # Process the upscaling
        result_image_data = process_upscaling(
            image_data=image_data,
            scale_factor=scale_factor,
            denoise_level=denoise_level,
            sharpen=sharpen,
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
        logger.exception(f"Error in upscaling: {e}")
        
        # Update progress to error state if task_id exists
        if 'task_id' in locals():
            tasks_progress[task_id] = {"progress": 1.0, "status": f"error: {str(e)}"}
        
        raise RuntimeError(f"Upscaling failed: {str(e)}")
