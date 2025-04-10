"""
AI Assistant Handler for the MCP server.

This module provides functionality for an AI assistant that can help with
image editing tasks and suggestions.
"""
import logging
import uuid
from typing import Dict, Any, List

# Import tasks_progress from app
from ..app import tasks_progress

logger = logging.getLogger(__name__)

async def handle_ai_assistant(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle an AI assistant request.
    
    Args:
        params: Parameters for the request, including:
            - message (str): User message
            - conversation_history (list, optional): Previous conversation
            - image_state (dict, optional): State of the GIMP image
            - analysis_results (dict, optional): Results of image analysis
            - task_id (str, optional): Task ID for progress tracking
            
    Returns:
        dict: Response with AI message and optional suggestions
    """
    try:
        # Extract parameters
        message = params.get("message")
        if not message:
            raise ValueError("Missing required parameter: message")
        
        conversation_history = params.get("conversation_history", [])
        image_state = params.get("image_state", {})
        analysis_results = params.get("analysis_results", {})
        
        # Generate a task ID for progress tracking if not provided
        task_id = params.get("task_id", str(uuid.uuid4()))
        
        logger.info(f"Processing AI assistant request, task_id={task_id}")
        
        # Initialize progress
        tasks_progress[task_id] = {"progress": 0.1, "status": "initializing assistant"}
        
        # Update progress
        tasks_progress[task_id] = {"progress": 0.3, "status": "generating response"}
        
        # Process the user message and generate a response
        # In a real implementation, this would call an actual AI model
        # Here we'll use a simple rule-based approach for demonstration
        
        response, suggestion = generate_response(message, conversation_history, image_state, analysis_results)
        
        # Update progress to complete
        tasks_progress[task_id] = {"progress": 1.0, "status": "completed"}
        
        # Return the result
        result = {
            "message": response,
            "status": "success",
            "task_id": task_id
        }
        
        # Add suggestion if available
        if suggestion:
            result["suggestion"] = suggestion
        
        return result
    except Exception as e:
        logger.exception(f"Error in AI assistant: {e}")
        
        # Update progress to error state if task_id exists
        if 'task_id' in locals():
            tasks_progress[task_id] = {"progress": 1.0, "status": f"error: {str(e)}"}
        
        raise RuntimeError(f"AI assistant failed: {str(e)}")

def generate_response(
    message: str, 
    conversation_history: List[Dict[str, str]], 
    image_state: Dict[str, Any], 
    analysis_results: Dict[str, Any]
) -> tuple:
    """
    Generate a response to the user message.
    
    Args:
        message: User message
        conversation_history: Previous conversation
        image_state: State of the GIMP image
        analysis_results: Results of image analysis
        
    Returns:
        tuple: (response, suggestion) where suggestion is None or a dict with operation details
    """
    # Lowercase the message for easier matching
    message_lower = message.lower()
    
    # Define some keywords to match
    brightness_keywords = ["bright", "brightness", "darker", "brighter", "dim", "light"]
    contrast_keywords = ["contrast", "flat", "dynamic range", "pop"]
    color_keywords = ["color", "saturation", "colorful", "vibrant", "desaturate", "grayscale", 
                    "black and white", "monochrome"]
    selection_keywords = ["select", "selection", "marquee", "rectangle", "ellipse", "circle"]
    crop_keywords = ["crop", "trim", "cut", "resize"]
    layer_keywords = ["layer", "duplicate", "merge", "new layer", "blend"]
    filter_keywords = ["blur", "sharpen", "noise", "smooth", "filter"]
    text_keywords = ["text", "write", "font", "typography"]
    
    # Check for analysis-related questions
    if any(word in message_lower for word in ["analyze", "analysis", "what do you see", "tell me about"]):
        if analysis_results:
            # Generate a response based on the analysis results
            return generate_analysis_response(analysis_results), None
        else:
            return "I don't have any analysis results for your image yet. Would you like me to analyze it?", None
    
    # Check for brightness/contrast adjustments
    elif any(word in message_lower for word in brightness_keywords + contrast_keywords):
        if "brightness" in message_lower:
            if any(word in message_lower for word in ["increase", "more", "higher", "brighter"]):
                return "I can increase the brightness of your image. Would you like me to do that?", {
                    "type": "adjustment",
                    "operation": "adjust_brightness_contrast",
                    "parameters": {
                        "brightness": 30,
                        "contrast": 0
                    }
                }
            elif any(word in message_lower for word in ["decrease", "less", "lower", "darker"]):
                return "I can decrease the brightness of your image. Would you like me to do that?", {
                    "type": "adjustment",
                    "operation": "adjust_brightness_contrast",
                    "parameters": {
                        "brightness": -30,
                        "contrast": 0
                    }
                }
        
        if "contrast" in message_lower:
            if any(word in message_lower for word in ["increase", "more", "higher"]):
                return "I can increase the contrast of your image. Would you like me to do that?", {
                    "type": "adjustment",
                    "operation": "adjust_brightness_contrast",
                    "parameters": {
                        "brightness": 0,
                        "contrast": 30
                    }
                }
            elif any(word in message_lower for word in ["decrease", "less", "lower"]):
                return "I can decrease the contrast of your image. Would you like me to do that?", {
                    "type": "adjustment",
                    "operation": "adjust_brightness_contrast",
                    "parameters": {
                        "brightness": 0,
                        "contrast": -30
                    }
                }
    
    # Check for color adjustments
    elif any(word in message_lower for word in color_keywords):
        if any(word in message_lower for word in ["grayscale", "black and white", "monochrome", "desaturate"]):
            return "I can convert your image to black and white. Would you like me to do that?", {
                "type": "adjustment",
                "operation": "desaturate",
                "parameters": {}
            }
        elif any(word in message_lower for word in ["saturate", "more color", "colorful", "vibrant"]):
            return "I can increase the saturation of your image to make it more vibrant. Would you like me to do that?", {
                "type": "adjustment",
                "operation": "adjust_hue_saturation",
                "parameters": {
                    "hue": 0,
                    "saturation": 30,
                    "lightness": 0
                }
            }
    
    # Check for blur/sharpen
    elif any(word in message_lower for word in filter_keywords):
        if "blur" in message_lower:
            return "I can apply a gaussian blur to your image. Would you like me to do that?", {
                "type": "filter",
                "operation": "apply_blur",
                "parameters": {
                    "blur_type": "gaussian",
                    "radius": 5.0
                }
            }
        elif "sharpen" in message_lower:
            return "I can sharpen your image to make it more crisp. Would you like me to do that?", {
                "type": "filter",
                "operation": "apply_sharpen",
                "parameters": {
                    "amount": 50.0
                }
            }
    
    # Check for selection operations
    elif any(word in message_lower for word in selection_keywords):
        if "rectangle" in message_lower:
            width = image_state.get("metadata", {}).get("width", 100)
            height = image_state.get("metadata", {}).get("height", 100)
            
            return "I can create a rectangular selection in the center of your image. Would you like me to do that?", {
                "type": "selection",
                "operation": "create_rectangle_selection",
                "parameters": {
                    "x": width // 4,
                    "y": height // 4,
                    "width": width // 2,
                    "height": height // 2
                }
            }
        elif any(word in message_lower for word in ["ellipse", "circle", "oval"]):
            width = image_state.get("metadata", {}).get("width", 100)
            height = image_state.get("metadata", {}).get("height", 100)
            
            return "I can create an elliptical selection in the center of your image. Would you like me to do that?", {
                "type": "selection",
                "operation": "create_ellipse_selection",
                "parameters": {
                    "x": width // 4,
                    "y": height // 4,
                    "width": width // 2,
                    "height": height // 2
                }
            }
        elif "select all" in message_lower:
            return "I can select the entire image. Would you like me to do that?", {
                "type": "selection",
                "operation": "select_all",
                "parameters": {}
            }
        elif "clear" in message_lower or "deselect" in message_lower:
            return "I can clear the current selection. Would you like me to do that?", {
                "type": "selection",
                "operation": "select_none",
                "parameters": {}
            }
    
    # Check for layer operations
    elif any(word in message_lower for word in layer_keywords):
        if "duplicate" in message_lower:
            return "I can duplicate the current layer. Would you like me to do that?", {
                "type": "layer",
                "operation": "duplicate_layer",
                "parameters": {}
            }
        elif "new" in message_lower:
            return "I can create a new transparent layer. Would you like me to do that?", {
                "type": "layer",
                "operation": "create_layer",
                "parameters": {
                    "name": "New Layer"
                }
            }
        elif "merge" in message_lower:
            return "I can merge all visible layers. Would you like me to do that?", {
                "type": "layer",
                "operation": "merge_layers",
                "parameters": {}
            }
    
    # Default response if no specific command is recognized
    else:
        return "I'm here to help with your image editing. I can adjust brightness, contrast, colors, apply filters, create selections, or work with layers. What would you like to do?", None

def generate_analysis_response(analysis_results: Dict[str, Any]) -> str:
    """
    Generate a response based on the analysis results.
    
    Args:
        analysis_results: Results of image analysis
        
    Returns:
        str: Response describing the image
    """
    try:
        # Get basic image information
        dimensions = analysis_results.get("dimensions", {})
        width = dimensions.get("width", 0)
        height = dimensions.get("height", 0)
        aspect_ratio = dimensions.get("aspect_ratio", 0)
        
        # Get color information
        color_analysis = analysis_results.get("color_analysis", {})
        brightness = color_analysis.get("brightness", 0)
        contrast = color_analysis.get("contrast", 0)
        is_grayscale = color_analysis.get("is_grayscale", False)
        dominant_colors = color_analysis.get("dominant_colors", [])
        
        # Build the response
        response = f"I've analyzed your image. It's {width}x{height} pixels with an aspect ratio of {aspect_ratio}. "
        
        # Add color information
        if is_grayscale:
            response += "It appears to be a grayscale image. "
        else:
            if dominant_colors:
                response += f"The dominant colors are {', '.join(dominant_colors)}. "
        
        # Add brightness/contrast assessment
        if brightness < 50:
            response += "The image is quite dark. I could help you increase the brightness. "
        elif brightness > 150:
            response += "The image is quite bright. I could help you reduce the brightness if needed. "
        
        if contrast < 30:
            response += "The image has low contrast. I could help you increase it to make details pop. "
        elif contrast > 100:
            response += "The image has high contrast. "
        
        # Add selection information
        if analysis_results.get("has_selection", False):
            selection_size = analysis_results.get("selection_size", {})
            selection_width = selection_size.get("width", 0)
            selection_height = selection_size.get("height", 0)
            response += f"You have an active selection of size {selection_width}x{selection_height} pixels. "
        
        # Add layer information
        layer_count = analysis_results.get("layer_count", 0)
        visible_layer_count = analysis_results.get("visible_layer_count", 0)
        response += f"The image has {layer_count} layers in total, with {visible_layer_count} visible. "
        
        # Add a question to prompt further interaction
        response += "How would you like me to help you edit this image?"
        
        return response
    except Exception as e:
        logger.error(f"Error generating analysis response: {e}")
        return "I've analyzed your image. How would you like me to help you edit it?"
