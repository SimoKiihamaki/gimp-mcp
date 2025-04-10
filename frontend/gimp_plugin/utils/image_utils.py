"""
Utilities for handling image data in the GIMP plugin.

This module provides functions for converting between GIMP drawables and
base64-encoded images for sending to the MCP server.
"""
import base64
import io
import os
from typing import Tuple, Optional

import numpy as np
from gimpfu import *
from PIL import Image

def drawable_to_pil(drawable):
    """
    Convert a GIMP drawable to a PIL Image.
    
    Args:
        drawable: GIMP drawable (layer)
        
    Returns:
        PIL Image object
    """
    # Get the drawable's dimensions
    width = drawable.width
    height = drawable.height
    
    # Get the pixel data from GIMP
    pixel_region = drawable.get_pixel_rgn(0, 0, width, height, False, False)
    pixel_data = pixel_region[:, :]
    
    # Create a PIL Image from the pixel data
    if drawable.bpp == 4:  # RGBA
        mode = "RGBA"
    elif drawable.bpp == 3:  # RGB
        mode = "RGB"
    else:  # Grayscale or indexed
        mode = "L"
    
    # Convert to a PIL Image
    pil_image = Image.frombytes(mode, (width, height), pixel_data)
    
    return pil_image

def pil_to_drawable(image, drawable):
    """
    Apply a PIL Image to a GIMP drawable.
    
    Args:
        image: PIL Image object
        drawable: GIMP drawable (layer)
    """
    # Convert the PIL Image to raw pixel data
    if image.mode == "RGBA":
        mode = "RGBA"
    elif image.mode == "RGB":
        mode = "RGB"
    else:
        mode = "L"
    
    # Get the raw pixel data
    pixel_data = image.tobytes()
    
    # Get the drawable's dimensions
    width = drawable.width
    height = drawable.height
    
    # Update the pixel data in GIMP
    pixel_region = drawable.get_pixel_rgn(0, 0, width, height, True, True)
    pixel_region[:, :] = pixel_data
    
    # Update the drawable
    drawable.flush()
    drawable.merge_shadow(True)
    drawable.update(0, 0, width, height)

def drawable_to_base64(drawable, format="PNG"):
    """
    Convert a GIMP drawable to a base64-encoded image string.
    
    Args:
        drawable: GIMP drawable (layer)
        format: Image format (e.g., "PNG", "JPEG")
        
    Returns:
        Base64-encoded image string
    """
    # Convert to PIL Image
    pil_image = drawable_to_pil(drawable)
    
    # Save to a buffer
    buffer = io.BytesIO()
    pil_image.save(buffer, format=format)
    buffer.seek(0)
    
    # Encode to base64
    encoded_image = base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    return encoded_image

def base64_to_new_layer(image, base64_image, layer_name="AI Result"):
    """
    Create a new layer in a GIMP image from a base64-encoded image.
    
    Args:
        image: GIMP image
        base64_image: Base64-encoded image string
        layer_name: Name for the new layer
        
    Returns:
        The new GIMP layer
    """
    try:
        # Decode base64 to bytes
        image_data = base64.b64decode(base64_image)
        
        # Create a PIL Image
        pil_image = Image.open(io.BytesIO(image_data))
        
        # Create a new layer in GIMP
        new_layer = gimp.Layer(image, layer_name, pil_image.width, pil_image.height,
                               RGBA_IMAGE, 100, NORMAL_MODE)
        
        # Add the layer to the image
        image.add_layer(new_layer, 0)  # Add at the top
        
        # Apply the PIL image to the new layer
        pil_to_drawable(pil_image, new_layer)
        
        # Return the new layer
        return new_layer
    except Exception as e:
        pdb.gimp_message(f"Error creating new layer: {str(e)}")
        return None

def get_layer_as_base64(layer, format="PNG"):
    """
    Get the current layer as a base64-encoded string.
    
    Args:
        layer: GIMP layer
        format: Image format (PNG, JPEG, etc.)
        
    Returns:
        Base64-encoded string
    """
    return drawable_to_base64(layer, format)

def load_image_from_file(file_path):
    """
    Load an image from file and return it as a base64-encoded string.
    
    Args:
        file_path: Path to the image file
        
    Returns:
        Base64-encoded image string
    """
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            raise ValueError(f"File not found: {file_path}")
        
        # Open the image using PIL
        with open(file_path, "rb") as f:
            image_data = f.read()
        
        # Convert to base64
        return base64.b64encode(image_data).decode("utf-8")
    except Exception as e:
        pdb.gimp_message(f"Error loading image from file: {str(e)}")
        raise
