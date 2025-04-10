"""
Image Analysis Handler for the MCP server.

This module provides functionality to analyze image content using AI models.
It helps the AI understand what's in the image to make better editing suggestions.
"""
import logging
import uuid
import base64
from io import BytesIO
from typing import Dict, Any, List

import numpy as np
from PIL import Image, ImageStat

# Import tasks_progress from app
from ..app import tasks_progress

logger = logging.getLogger(__name__)

async def handle_image_analysis(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle an image analysis request.
    
    Args:
        params: Parameters for the request, including:
            - image_state (dict): State of the GIMP image
            - analysis_type (str, optional): Type of analysis to perform (basic, detailed, etc.)
            - task_id (str, optional): Task ID for progress tracking
            
    Returns:
        dict: Response with analysis results
    """
    try:
        # Extract parameters
        image_state = params.get("image_state")
        if not image_state:
            raise ValueError("Missing required parameter: image_state")
        
        analysis_type = params.get("analysis_type", "basic")
        
        # Generate a task ID for progress tracking if not provided
        task_id = params.get("task_id", str(uuid.uuid4()))
        
        logger.info(f"Processing image analysis request, type={analysis_type}, task_id={task_id}")
        
        # Initialize progress
        tasks_progress[task_id] = {"progress": 0.1, "status": "initializing analysis"}
        
        # Get the active layer pixels for analysis
        layer_pixels = None
        if "layer_pixels" in image_state:
            active_layer_index = image_state["metadata"].get("active_layer_index", 0)
            if active_layer_index >= 0 and active_layer_index < len(image_state["layers"]):
                active_layer = image_state["layers"][active_layer_index]
                active_layer_id = str(active_layer["id"])
                if active_layer_id in image_state["layer_pixels"]:
                    layer_pixels = image_state["layer_pixels"][active_layer_id]
        
        # Update progress
        tasks_progress[task_id] = {"progress": 0.3, "status": "processing image data"}
        
        # Perform the analysis
        if analysis_type == "basic":
            analysis_results = await perform_basic_analysis(image_state, layer_pixels)
        elif analysis_type == "detailed":
            analysis_results = await perform_detailed_analysis(image_state, layer_pixels)
        else:
            analysis_results = await perform_basic_analysis(image_state, layer_pixels)
        
        # Update progress to complete
        tasks_progress[task_id] = {"progress": 1.0, "status": "completed"}
        
        # Return the result
        return {
            "analysis": analysis_results,
            "status": "success",
            "task_id": task_id
        }
    except Exception as e:
        logger.exception(f"Error in image analysis: {e}")
        
        # Update progress to error state if task_id exists
        if 'task_id' in locals():
            tasks_progress[task_id] = {"progress": 1.0, "status": f"error: {str(e)}"}
        
        raise RuntimeError(f"Image analysis failed: {str(e)}")

async def perform_basic_analysis(image_state: Dict[str, Any], layer_pixels: str = None) -> Dict[str, Any]:
    """
    Perform basic analysis of the image.
    
    Args:
        image_state: The state of the GIMP image
        layer_pixels: Base64-encoded pixel data for the active layer
        
    Returns:
        dict: Basic analysis results
    """
    results = {}
    
    # Extract basic metadata
    metadata = image_state.get("metadata", {})
    results["dimensions"] = {
        "width": metadata.get("width", 0),
        "height": metadata.get("height", 0),
        "aspect_ratio": round(metadata.get("width", 1) / max(metadata.get("height", 1), 1), 2)
    }
    
    results["color_mode"] = metadata.get("color_mode", "Unknown")
    
    # Count layers
    layers = image_state.get("layers", [])
    results["layer_count"] = len(layers)
    results["visible_layer_count"] = sum(1 for layer in layers if layer.get("visible", False))
    
    # Check if there's an active selection
    selection = image_state.get("selection", {})
    results["has_selection"] = selection.get("has_selection", False)
    
    if results["has_selection"]:
        bounds = selection.get("bounds", {})
        results["selection_size"] = {
            "width": bounds.get("width", 0),
            "height": bounds.get("height", 0),
            "area": bounds.get("width", 0) * bounds.get("height", 0)
        }
    
    # Analyze pixel data if available
    if layer_pixels:
        pixel_analysis = analyze_pixel_data(layer_pixels)
        results.update(pixel_analysis)
    
    return results

async def perform_detailed_analysis(image_state: Dict[str, Any], layer_pixels: str = None) -> Dict[str, Any]:
    """
    Perform detailed analysis of the image.
    
    Args:
        image_state: The state of the GIMP image
        layer_pixels: Base64-encoded pixel data for the active layer
        
    Returns:
        dict: Detailed analysis results
    """
    # Start with basic analysis
    results = await perform_basic_analysis(image_state, layer_pixels)
    
    # Add more detailed analysis
    # In a real implementation, this would use AI models for object detection,
    # scene understanding, etc.
    results["analysis_level"] = "detailed"
    
    # Dummy object detection (in a real implementation, this would use a ML model)
    if layer_pixels:
        results["detected_objects"] = [
            {"label": "unknown", "confidence": 0.0, "bbox": [0, 0, 0, 0]}
        ]
        results["scene_type"] = "unknown"
        results["style"] = "unknown"
    
    # Analyze layer structure
    layers = image_state.get("layers", [])
    layer_analysis = []
    
    for layer in layers:
        layer_info = {
            "name": layer.get("name", "Unnamed"),
            "visible": layer.get("visible", False),
            "opacity": layer.get("opacity", 100),
            "blend_mode": layer.get("mode_name", "Normal"),
            "is_group": layer.get("is_group", False),
            "size": {
                "width": layer.get("width", 0),
                "height": layer.get("height", 0)
            }
        }
        layer_analysis.append(layer_info)
    
    results["layer_analysis"] = layer_analysis
    
    return results

def analyze_pixel_data(base64_data: str) -> Dict[str, Any]:
    """
    Analyze the pixel data of an image.
    
    Args:
        base64_data: Base64-encoded image data
        
    Returns:
        dict: Analysis results
    """
    try:
        # Decode the base64 image
        image_data = base64.b64decode(base64_data)
        image = Image.open(BytesIO(image_data))
        
        # Convert to RGB if needed
        if image.mode != "RGB":
            image = image.convert("RGB")
        
        # Get image statistics
        stat = ImageStat.Stat(image)
        
        # Calculate average RGB
        avg_color = tuple(int(v) for v in stat.mean)
        
        # Calculate brightness
        brightness = sum(stat.mean) / 3
        
        # Calculate contrast (standard deviation)
        contrast = sum(stat.stddev) / 3
        
        # Check if the image is grayscale (approximately)
        is_grayscale = all(abs(avg_color[0] - avg_color[i]) < 5 for i in range(1, 3))
        
        # Analyze histogram for color distribution
        hist = image.histogram()
        r_hist = hist[0:256]
        g_hist = hist[256:512]
        b_hist = hist[512:768]
        
        # Determine dominant colors (simplified)
        color_ranges = [
            ("Red", (180, 0, 0)),
            ("Green", (0, 180, 0)),
            ("Blue", (0, 0, 180)),
            ("Yellow", (180, 180, 0)),
            ("Cyan", (0, 180, 180)),
            ("Magenta", (180, 0, 180)),
            ("White", (220, 220, 220)),
            ("Black", (35, 35, 35)),
            ("Gray", (128, 128, 128))
        ]
        
        # Very simplified dominant color detection
        dominant_colors = []
        for name, (r, g, b) in color_ranges:
            if (abs(avg_color[0] - r) < 50 and
                abs(avg_color[1] - g) < 50 and
                abs(avg_color[2] - b) < 50):
                dominant_colors.append(name)
        
        if not dominant_colors:
            dominant_colors = ["Mixed"]
        
        return {
            "color_analysis": {
                "average_color": {
                    "rgb": avg_color,
                    "hex": "#{:02x}{:02x}{:02x}".format(*avg_color)
                },
                "brightness": round(brightness, 2),
                "contrast": round(contrast, 2),
                "is_grayscale": is_grayscale,
                "dominant_colors": dominant_colors
            }
        }
    except Exception as e:
        logger.error(f"Error analyzing pixel data: {e}")
        return {
            "color_analysis": {
                "error": "Could not analyze pixel data",
                "reason": str(e)
            }
        }
