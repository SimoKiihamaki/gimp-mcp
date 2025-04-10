"""
Utilities for handling image data in the MCP server.

This module provides functions for encoding/decoding images and
performing common image operations.
"""
import base64
import io
import logging
from typing import Tuple, Optional, Union

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

def decode_base64_image(encoded_image: str) -> Image.Image:
    """
    Decode a base64-encoded image string to a PIL Image.
    
    Args:
        encoded_image: Base64-encoded image string
        
    Returns:
        PIL Image object
    """
    try:
        # Decode base64 string to bytes
        image_data = base64.b64decode(encoded_image)
        
        # Convert bytes to PIL Image
        image = Image.open(io.BytesIO(image_data))
        
        return image
    except Exception as e:
        logger.error(f"Error decoding base64 image: {e}")
        raise ValueError(f"Failed to decode image: {str(e)}")

def encode_image_to_base64(image: Union[Image.Image, np.ndarray], format: str = "PNG") -> str:
    """
    Encode a PIL Image or NumPy array to a base64 string.
    
    Args:
        image: PIL Image or NumPy array to encode
        format: Image format (e.g., "PNG", "JPEG")
        
    Returns:
        Base64-encoded image string
    """
    try:
        # Convert NumPy array to PIL Image if needed
        if isinstance(image, np.ndarray):
            if image.ndim == 2:
                # Grayscale image
                pil_image = Image.fromarray(image, 'L')
            elif image.ndim == 3 and image.shape[2] == 3:
                # RGB image
                pil_image = Image.fromarray(image, 'RGB')
            elif image.ndim == 3 and image.shape[2] == 4:
                # RGBA image
                pil_image = Image.fromarray(image, 'RGBA')
            else:
                raise ValueError(f"Unsupported array shape: {image.shape}")
        else:
            pil_image = image
        
        # Save image to bytes buffer
        buffer = io.BytesIO()
        pil_image.save(buffer, format=format)
        buffer.seek(0)
        
        # Encode bytes to base64 string
        encoded_string = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        return encoded_string
    except Exception as e:
        logger.error(f"Error encoding image to base64: {e}")
        raise ValueError(f"Failed to encode image: {str(e)}")

def pil_to_numpy(image: Image.Image) -> np.ndarray:
    """
    Convert a PIL Image to a NumPy array.
    
    Args:
        image: PIL Image object
        
    Returns:
        NumPy array
    """
    return np.array(image)

def numpy_to_pil(array: np.ndarray) -> Image.Image:
    """
    Convert a NumPy array to a PIL Image.
    
    Args:
        array: NumPy array
        
    Returns:
        PIL Image object
    """
    if array.ndim == 2:
        # Grayscale image
        return Image.fromarray(array, 'L')
    elif array.ndim == 3 and array.shape[2] == 3:
        # RGB image
        return Image.fromarray(array, 'RGB')
    elif array.ndim == 3 and array.shape[2] == 4:
        # RGBA image
        return Image.fromarray(array, 'RGBA')
    else:
        raise ValueError(f"Unsupported array shape: {array.shape}")

def resize_image(image: Image.Image, width: int, height: int) -> Image.Image:
    """
    Resize an image to the specified dimensions.
    
    Args:
        image: PIL Image to resize
        width: Target width
        height: Target height
        
    Returns:
        Resized PIL Image
    """
    return image.resize((width, height), Image.LANCZOS)
