"""
Style transfer handler for the MCP server.

This module handles style transfer requests from the GIMP plugin.
"""
import logging
import uuid
from typing import Dict, Any, List, Optional

# Import the style transfer models
from ..models.style_transfer.fast_style_impl import process_style_transfer, get_available_styles
from ..models.style_transfer.diffusion_style_impl import process_diffusion_style_transfer, get_available_models as get_available_diffusion_models

# Import tasks_progress from app
from ..app import tasks_progress

logger = logging.getLogger(__name__)

async def handle_style_transfer(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle a style transfer request.
    
    Args:
        params: Parameters for the request, including:
            - image_data (str): Base64-encoded image data
            - method (str, optional): "classic" or "diffusion" (default: "classic")
            - style_name (str, optional): Name of the style to apply for classic method
            - style_type (str, optional): "text" or "image" for diffusion method
            - style_prompt (str, optional): Text prompt for diffusion method with text style
            - style_image_data (str, optional): Base64-encoded style image for diffusion with image style
            - model_id (str, optional): Model ID for diffusion method
            - strength (float, optional): Style strength (0.0-1.0, default: 1.0)
            - guidance_scale (float, optional): Guidance scale for diffusion method (default: 7.5)
            - num_inference_steps (int, optional): Number of steps for diffusion (default: 30)
            - seed (int, optional): Random seed for diffusion (default: None)
            - use_gpu (bool, optional): Whether to use GPU for inference (default: True)
            - use_half_precision (bool, optional): Use half precision for diffusion (default: True)
            - task_id (str, optional): Task ID for progress tracking
            
    Returns:
        dict: Response with processed image data
    """
    try:
        # Extract parameters
        image_data = params.get("image_data")
        if not image_data:
            raise ValueError("Missing required parameter: image_data")
        
        # Method selection (classic or diffusion)
        method = params.get("method", "classic")
        
        # Generate a task ID for progress tracking if not provided
        task_id = params.get("task_id", str(uuid.uuid4()))
        
        # Initialize progress
        tasks_progress[task_id] = {"progress": 0.1, "status": "initializing"}
        
        # Update to loading model status
        tasks_progress[task_id] = {"progress": 0.2, "status": "loading model"}
        
        # Update to processing status
        tasks_progress[task_id] = {"progress": 0.4, "status": "applying style"}
        
        if method == "classic":
            # Classic style transfer parameters
            style_name = params.get("style_name", "mosaic")
            strength = float(params.get("strength", 1.0))
            use_gpu = params.get("use_gpu", True)
            
            # Validate parameters
            if strength < 0.0 or strength > 1.0:
                raise ValueError("Style strength must be between 0.0 and 1.0")
            
            logger.info(f"Processing classic style transfer with style={style_name}, strength={strength}, use_gpu={use_gpu}")
            
            # Process the style transfer
            result_image_data = process_style_transfer(
                image_data=image_data,
                style_name=style_name,
                strength=strength,
                use_gpu=use_gpu
            )
        elif method == "diffusion":
            # Diffusion style transfer parameters
            style_type = params.get("style_type", "text")
            style_prompt = params.get("style_prompt", "Oil painting in the style of Van Gogh")
            style_image_data = params.get("style_image_data")
            model_id = params.get("model_id", "sd1.5")
            strength = float(params.get("strength", 0.75))
            guidance_scale = float(params.get("guidance_scale", 7.5))
            num_inference_steps = int(params.get("num_inference_steps", 30))
            seed = params.get("seed")
            if seed is not None:
                seed = int(seed)
            use_gpu = params.get("use_gpu", True)
            use_half_precision = params.get("use_half_precision", True)
            
            # Validate parameters
            if strength < 0.0 or strength > 1.0:
                raise ValueError("Style strength must be between 0.0 and 1.0")
            if style_type == "image" and not style_image_data:
                raise ValueError("style_image_data is required when style_type is 'image'")
            
            logger.info(f"Processing diffusion style transfer with model={model_id}, style_type={style_type}")
            
            # Process the diffusion style transfer
            result_image_data = process_diffusion_style_transfer(
                image_data=image_data,
                style_type=style_type,
                style_prompt=style_prompt,
                style_image_data=style_image_data,
                model_id=model_id,
                strength=strength,
                guidance_scale=guidance_scale,
                num_inference_steps=num_inference_steps,
                seed=seed,
                use_gpu=use_gpu,
                use_half_precision=use_half_precision
            )
        else:
            raise ValueError(f"Unknown method: {method}. Must be 'classic' or 'diffusion'")
        
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
        params: Parameters for the request
            - method (str, optional): "classic" or "diffusion" (default: "classic")
            
    Returns:
        dict: Response with available styles
    """
    try:
        # Get method type
        method = params.get("method", "classic")
        
        if method == "classic":
            # Get classic styles
            styles = get_available_styles()
            return {
                "styles": styles,
                "method": "classic",
                "status": "success"
            }
        elif method == "diffusion":
            # Get diffusion models
            models = get_available_diffusion_models()
            return {
                "models": models,
                "method": "diffusion",
                "status": "success"
            }
        else:
            raise ValueError(f"Unknown method: {method}. Must be 'classic' or 'diffusion'")
    except Exception as e:
        logger.exception(f"Error getting styles: {e}")
        raise RuntimeError(f"Failed to get styles: {str(e)}")

async def handle_get_all_style_options(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle a request to get all available style options for both methods.
    
    Args:
        params: Parameters for the request (not used)
            
    Returns:
        dict: Response with all style options
    """
    try:
        # Get classic styles
        classic_styles = get_available_styles()
        
        # Get diffusion models
        diffusion_models = get_available_diffusion_models()
        
        # Return all options
        return {
            "classic_styles": classic_styles,
            "diffusion_models": diffusion_models,
            "status": "success"
        }
    except Exception as e:
        logger.exception(f"Error getting style options: {e}")
        raise RuntimeError(f"Failed to get style options: {str(e)}")
