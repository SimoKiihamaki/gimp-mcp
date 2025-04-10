"""
Image State Capture Module

This module provides functions to capture the current state of a GIMP image,
including layers, selections, channels, and pixel data.
"""
import os
import base64
from io import BytesIO
from typing import Dict, Any, List, Optional, Tuple

import gimp
from gimpfu import *

def capture_image_metadata(image) -> Dict[str, Any]:
    """
    Capture basic metadata about the GIMP image.
    
    Args:
        image: The GIMP image object
        
    Returns:
        Dict containing image metadata (width, height, resolution, color mode, etc.)
    """
    metadata = {
        "width": image.width,
        "height": image.height,
        "filename": image.filename or "Untitled",
        "basename": os.path.basename(image.filename) if image.filename else "Untitled",
        "base_type": image.base_type,  # RGB, GRAY, INDEXED
        "x_resolution": image.resolution[0],
        "y_resolution": image.resolution[1],
        "num_layers": len(image.layers),
        "active_layer_index": image.layers.index(image.active_layer) if image.active_layer in image.layers else -1
    }
    
    # Add color mode name for better readability
    base_type_names = {
        RGB: "RGB",
        GRAY: "Grayscale",
        INDEXED: "Indexed"
    }
    metadata["color_mode"] = base_type_names.get(image.base_type, "Unknown")
    
    return metadata

def capture_layer_data(image) -> List[Dict[str, Any]]:
    """
    Capture information about all layers in the image.
    
    Args:
        image: The GIMP image object
        
    Returns:
        List of dictionaries containing layer information
    """
    layers_data = []
    
    for layer in image.layers:
        layer_info = {
            "name": layer.name,
            "id": layer.ID,
            "width": layer.width,
            "height": layer.height,
            "visible": layer.visible,
            "opacity": layer.opacity,
            "mode": layer.mode,  # NORMAL_MODE, MULTIPLY_MODE, etc.
            "offsets": (layer.offsets[0], layer.offsets[1]),
            "mask": bool(layer.mask),
            "is_active": layer == image.active_layer,
            "is_text_layer": hasattr(layer, 'text_layer') and layer.text_layer,
            "has_alpha": layer.has_alpha,
            "type": layer.type,  # RGB_IMAGE, RGBA_IMAGE, etc.
        }
        
        # Get layer mode name
        mode_names = {
            NORMAL_MODE: "Normal",
            MULTIPLY_MODE: "Multiply",
            SCREEN_MODE: "Screen",
            OVERLAY_MODE: "Overlay",
            DIFFERENCE_MODE: "Difference",
            ADDITION_MODE: "Addition",
            SUBTRACT_MODE: "Subtract",
            DARKEN_ONLY_MODE: "Darken Only",
            LIGHTEN_ONLY_MODE: "Lighten Only",
            HUE_MODE: "Hue",
            SATURATION_MODE: "Saturation",
            COLOR_MODE: "Color",
            VALUE_MODE: "Value"
        }
        layer_info["mode_name"] = mode_names.get(layer.mode, "Unknown")
        
        # Handle layer groups
        if hasattr(layer, 'children'):
            layer_info["is_group"] = True
            layer_info["children"] = [child.ID for child in layer.children]
        else:
            layer_info["is_group"] = False
            layer_info["children"] = []
        
        layers_data.append(layer_info)
    
    return layers_data

def capture_selection(image) -> Dict[str, Any]:
    """
    Capture information about the current selection in the image.
    
    Args:
        image: The GIMP image object
        
    Returns:
        Dict containing selection information (bounds, mask, etc.)
    """
    # Check if there's an active selection
    has_selection, x1, y1, x2, y2 = pdb.gimp_selection_bounds(image)
    
    if not has_selection:
        return {
            "has_selection": False
        }
    
    # Basic selection info
    selection_info = {
        "has_selection": True,
        "bounds": {
            "x1": x1,
            "y1": y1,
            "x2": x2,
            "y2": y2,
            "width": x2 - x1,
            "height": y2 - y1,
        }
    }
    
    # If requested, we could also capture the selection mask by saving to a channel
    # This is optional as it increases the data size significantly
    channel = pdb.gimp_selection_save(image)
    selection_info["channel_id"] = channel.ID if channel else None
    
    return selection_info

def capture_channels(image) -> List[Dict[str, Any]]:
    """
    Capture information about the channels in the image.
    
    Args:
        image: The GIMP image object
        
    Returns:
        List of dictionaries containing channel information
    """
    channels_data = []
    
    for channel in image.channels:
        channel_info = {
            "name": channel.name,
            "id": channel.ID,
            "width": channel.width,
            "height": channel.height,
            "visible": channel.visible,
            "opacity": channel.opacity,
            "color": list(channel.color) if hasattr(channel, "color") else None,
            "is_selection": channel == image.selection
        }
        channels_data.append(channel_info)
    
    return channels_data

def capture_layer_pixels(drawable, include_alpha: bool = True) -> str:
    """
    Capture pixel data from a drawable (layer).
    
    Args:
        drawable: The GIMP drawable object
        include_alpha: Whether to include alpha channel data
        
    Returns:
        Base64-encoded PNG representation of the layer
    """
    # Create a temporary file
    temp_dir = gimp.temporary_directory()
    temp_file = os.path.join(temp_dir, f"temp_layer_{drawable.ID}.png")
    
    try:
        # Save the drawable to a PNG file
        pdb.gimp_file_save(
            pdb.gimp_item_get_image(drawable), 
            drawable, 
            temp_file, 
            temp_file
        )
        
        # Read the file and convert to base64
        with open(temp_file, "rb") as f:
            image_data = f.read()
        
        # Return base64-encoded data
        return base64.b64encode(image_data).decode('utf-8')
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_file):
            os.remove(temp_file)

def capture_current_state(image, include_pixels: bool = True) -> Dict[str, Any]:
    """
    Capture the complete state of the current GIMP image.
    
    Args:
        image: The GIMP image object
        include_pixels: Whether to include pixel data for layers
        
    Returns:
        Dict containing the complete image state
    """
    # Start with image metadata
    state = {
        "metadata": capture_image_metadata(image),
        "layers": capture_layer_data(image),
        "selection": capture_selection(image),
        "channels": capture_channels(image)
    }
    
    # Add pixel data for each layer if requested
    if include_pixels:
        layer_pixels = {}
        for layer in image.layers:
            if not layer.visible:
                continue  # Skip invisible layers to save bandwidth
            if hasattr(layer, 'children') and layer.children:
                continue  # Skip layer groups
            layer_pixels[str(layer.ID)] = capture_layer_pixels(layer)
        
        state["layer_pixels"] = layer_pixels
    
    return state

def serialize_image_state(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Serialize the image state to a JSON-compatible format.
    
    Args:
        state: The image state dictionary
        
    Returns:
        JSON-serializable dictionary
    """
    # Most of our data is already JSON-serializable, but let's ensure it
    serialized = {}
    
    # Handle metadata
    serialized["metadata"] = state["metadata"]
    
    # Handle layers
    serialized["layers"] = []
    for layer in state["layers"]:
        serialized_layer = dict(layer)
        # Convert any non-serializable types
        serialized_layer["offsets"] = list(serialized_layer["offsets"])
        serialized["layers"].append(serialized_layer)
    
    # Handle selection and channels
    serialized["selection"] = state["selection"]
    serialized["channels"] = state["channels"]
    
    # Handle pixel data if present
    if "layer_pixels" in state:
        serialized["layer_pixels"] = state["layer_pixels"]
    
    return serialized
