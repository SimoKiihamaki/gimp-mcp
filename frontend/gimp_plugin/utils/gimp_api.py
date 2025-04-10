"""
Enhanced GIMP API Wrapper

This module provides a comprehensive wrapper around GIMP's Python API,
making it easier to programmatically manipulate images, layers, selections, etc.
"""
import os
import logging
from typing import Dict, Any, List, Tuple, Optional, Union

import gimp
from gimpfu import *

# Set up logging
logger = logging.getLogger(__name__)

# Configure logging to use GIMP's message system
def log(message, level="INFO"):
    if level == "ERROR":
        pdb.gimp_message(f"ERROR: {message}")
    else:
        pdb.gimp_message(message)

# Layer Operations
def create_layer(image, name: str, width: int = None, height: int = None, 
                 type_id: int = RGBA_IMAGE, opacity: float = 100.0, 
                 mode: int = NORMAL_MODE, position: int = 0) -> Any:
    """
    Create a new layer in the specified image.
    
    Args:
        image: The GIMP image object
        name: Name for the new layer
        width: Width of the new layer (default: image width)
        height: Height of the new layer (default: image height)
        type_id: Type of layer (RGBA_IMAGE, RGB_IMAGE, GRAY_IMAGE, etc.)
        opacity: Layer opacity (0-100)
        mode: Blend mode (NORMAL_MODE, MULTIPLY_MODE, etc.)
        position: Position in the layer stack (0 = top)
        
    Returns:
        The newly created layer
    """
    try:
        # Use image dimensions if not specified
        if width is None:
            width = image.width
        if height is None:
            height = image.height
            
        # Create the layer
        layer = gimp.Layer(image, name, width, height, type_id, opacity, mode)
        
        # Add to the image
        image.add_layer(layer, position)
        
        return layer
    except Exception as e:
        log(f"Error creating layer: {str(e)}", "ERROR")
        raise

def duplicate_layer(image, layer) -> Any:
    """
    Duplicate the specified layer.
    
    Args:
        image: The GIMP image object
        layer: The layer to duplicate
        
    Returns:
        The newly created duplicate layer
    """
    try:
        # Duplicate the layer
        new_layer = pdb.gimp_layer_copy(layer, True)  # True = with alpha channel
        
        # Add to the image
        position = image.layers.index(layer)
        image.add_layer(new_layer, position)
        
        return new_layer
    except Exception as e:
        log(f"Error duplicating layer: {str(e)}", "ERROR")
        raise

def merge_layers(image, merge_type: int = CLIP_TO_IMAGE) -> Any:
    """
    Merge visible layers in the image.
    
    Args:
        image: The GIMP image object
        merge_type: Type of merge (CLIP_TO_IMAGE, CLIP_TO_BOTTOM_LAYER, etc.)
        
    Returns:
        The merged layer
    """
    try:
        merged_layer = pdb.gimp_image_merge_visible_layers(image, merge_type)
        return merged_layer
    except Exception as e:
        log(f"Error merging layers: {str(e)}", "ERROR")
        raise

def get_layer_by_name(image, name: str) -> Optional[Any]:
    """
    Get a layer by its name.
    
    Args:
        image: The GIMP image object
        name: Name of the layer to find
        
    Returns:
        The layer if found, None otherwise
    """
    for layer in image.layers:
        if layer.name == name:
            return layer
    return None

def get_layer_by_id(image, layer_id: int) -> Optional[Any]:
    """
    Get a layer by its ID.
    
    Args:
        image: The GIMP image object
        layer_id: ID of the layer to find
        
    Returns:
        The layer if found, None otherwise
    """
    for layer in image.layers:
        if layer.ID == layer_id:
            return layer
    return None

# Selection Operations
def create_rectangle_selection(image, x: int, y: int, width: int, height: int, 
                              operation: int = CHANNEL_OP_REPLACE, feather: float = 0.0):
    """
    Create a rectangular selection.
    
    Args:
        image: The GIMP image object
        x: X coordinate of the top-left corner
        y: Y coordinate of the top-left corner
        width: Width of the selection
        height: Height of the selection
        operation: Selection operation (CHANNEL_OP_REPLACE, CHANNEL_OP_ADD, etc.)
        feather: Feather radius
    """
    try:
        pdb.gimp_image_select_rectangle(image, operation, x, y, width, height)
        
        if feather > 0:
            pdb.gimp_selection_feather(image, feather)
    except Exception as e:
        log(f"Error creating rectangle selection: {str(e)}", "ERROR")
        raise

def create_ellipse_selection(image, x: int, y: int, width: int, height: int, 
                            operation: int = CHANNEL_OP_REPLACE, feather: float = 0.0):
    """
    Create an elliptical selection.
    
    Args:
        image: The GIMP image object
        x: X coordinate of the top-left corner
        y: Y coordinate of the top-left corner
        width: Width of the selection
        height: Height of the selection
        operation: Selection operation (CHANNEL_OP_REPLACE, CHANNEL_OP_ADD, etc.)
        feather: Feather radius
    """
    try:
        pdb.gimp_image_select_ellipse(image, operation, x, y, width, height)
        
        if feather > 0:
            pdb.gimp_selection_feather(image, feather)
    except Exception as e:
        log(f"Error creating ellipse selection: {str(e)}", "ERROR")
        raise

def select_none(image):
    """
    Clear the current selection.
    
    Args:
        image: The GIMP image object
    """
    try:
        pdb.gimp_selection_none(image)
    except Exception as e:
        log(f"Error clearing selection: {str(e)}", "ERROR")
        raise

def select_all(image):
    """
    Select the entire image.
    
    Args:
        image: The GIMP image object
    """
    try:
        pdb.gimp_selection_all(image)
    except Exception as e:
        log(f"Error selecting all: {str(e)}", "ERROR")
        raise

def invert_selection(image):
    """
    Invert the current selection.
    
    Args:
        image: The GIMP image object
    """
    try:
        pdb.gimp_selection_invert(image)
    except Exception as e:
        log(f"Error inverting selection: {str(e)}", "ERROR")
        raise

def grow_selection(image, pixels: int):
    """
    Grow the current selection by the specified number of pixels.
    
    Args:
        image: The GIMP image object
        pixels: Number of pixels to grow the selection
    """
    try:
        pdb.gimp_selection_grow(image, pixels)
    except Exception as e:
        log(f"Error growing selection: {str(e)}", "ERROR")
        raise

def shrink_selection(image, pixels: int):
    """
    Shrink the current selection by the specified number of pixels.
    
    Args:
        image: The GIMP image object
        pixels: Number of pixels to shrink the selection
    """
    try:
        pdb.gimp_selection_shrink(image, pixels)
    except Exception as e:
        log(f"Error shrinking selection: {str(e)}", "ERROR")
        raise

# Filter Operations
def apply_blur(drawable, blur_type: str, radius: float):
    """
    Apply a blur filter to the drawable.
    
    Args:
        drawable: The GIMP drawable object
        blur_type: Type of blur ('gaussian', 'motion', etc.)
        radius: Blur radius
    """
    try:
        if blur_type.lower() == 'gaussian':
            pdb.plug_in_gauss(pdb.gimp_item_get_image(drawable), drawable, radius, radius, 0)
        elif blur_type.lower() == 'motion':
            pdb.plug_in_mblur(pdb.gimp_item_get_image(drawable), drawable, 0, radius, 0, 0, 0)
        elif blur_type.lower() == 'pixelize':
            pdb.plug_in_pixelize(pdb.gimp_item_get_image(drawable), drawable, radius)
        else:
            raise ValueError(f"Unsupported blur type: {blur_type}")
    except Exception as e:
        log(f"Error applying blur: {str(e)}", "ERROR")
        raise

def apply_sharpen(drawable, amount: float):
    """
    Apply a sharpen filter to the drawable.
    
    Args:
        drawable: The GIMP drawable object
        amount: Sharpen amount
    """
    try:
        pdb.plug_in_sharpen(pdb.gimp_item_get_image(drawable), drawable, amount)
    except Exception as e:
        log(f"Error applying sharpen: {str(e)}", "ERROR")
        raise

# Color Operations
def adjust_brightness_contrast(drawable, brightness: float, contrast: float):
    """
    Adjust brightness and contrast of the drawable.
    
    Args:
        drawable: The GIMP drawable object
        brightness: Brightness adjustment (-127 to 127)
        contrast: Contrast adjustment (-127 to 127)
    """
    try:
        pdb.gimp_brightness_contrast(drawable, brightness, contrast)
    except Exception as e:
        log(f"Error adjusting brightness/contrast: {str(e)}", "ERROR")
        raise

def adjust_hue_saturation(drawable, hue: float, saturation: float, lightness: float):
    """
    Adjust hue, saturation, and lightness of the drawable.
    
    Args:
        drawable: The GIMP drawable object
        hue: Hue adjustment (-180 to 180)
        saturation: Saturation adjustment (-100 to 100)
        lightness: Lightness adjustment (-100 to 100)
    """
    try:
        pdb.gimp_hue_saturation(drawable, 0, hue, lightness, saturation)
    except Exception as e:
        log(f"Error adjusting hue/saturation: {str(e)}", "ERROR")
        raise

def desaturate(drawable, desaturate_mode: int = DESATURATE_LIGHTNESS):
    """
    Desaturate the drawable.
    
    Args:
        drawable: The GIMP drawable object
        desaturate_mode: Desaturation mode (DESATURATE_LIGHTNESS, DESATURATE_LUMINOSITY, DESATURATE_AVERAGE)
    """
    try:
        pdb.gimp_desaturate_full(drawable, desaturate_mode)
    except Exception as e:
        log(f"Error desaturating: {str(e)}", "ERROR")
        raise

# Drawing Operations
def fill_selection(image, drawable, fill_type: int = FOREGROUND_FILL):
    """
    Fill the current selection with the specified fill type.
    
    Args:
        image: The GIMP image object
        drawable: The drawable to fill
        fill_type: Fill type (FOREGROUND_FILL, BACKGROUND_FILL, WHITE_FILL, etc.)
    """
    try:
        pdb.gimp_edit_fill(drawable, fill_type)
    except Exception as e:
        log(f"Error filling selection: {str(e)}", "ERROR")
        raise

def draw_brush_stroke(drawable, stroke_points: List[Tuple[float, float]], 
                     brush_name: str, brush_size: float, color: Tuple[float, float, float]):
    """
    Draw a brush stroke on the drawable.
    
    Args:
        drawable: The GIMP drawable object
        stroke_points: List of (x, y) coordinates for the stroke
        brush_name: Name of the brush to use
        brush_size: Size of the brush
        color: (R, G, B) color tuple for the stroke
    """
    try:
        image = pdb.gimp_item_get_image(drawable)
        
        # Save current context
        old_brush = pdb.gimp_context_get_brush()
        old_fg = pdb.gimp_context_get_foreground()
        
        # Set new context
        pdb.gimp_context_set_brush(brush_name)
        pdb.gimp_context_set_brush_size(brush_size)
        pdb.gimp_context_set_foreground(color)
        
        # Flatten the stroke points into a single list [x1, y1, x2, y2, ...]
        flat_points = []
        for point in stroke_points:
            flat_points.extend(point)
        
        # Draw the stroke
        pdb.gimp_paintbrush_default(drawable, len(flat_points), flat_points)
        
        # Restore context
        pdb.gimp_context_set_brush(old_brush)
        pdb.gimp_context_set_foreground(old_fg)
    except Exception as e:
        log(f"Error drawing brush stroke: {str(e)}", "ERROR")
        raise

# Text Operations
def add_text_layer(image, text: str, font: str, size: float, 
                  color: Tuple[float, float, float], x: int, y: int) -> Any:
    """
    Add a text layer to the image.
    
    Args:
        image: The GIMP image object
        text: The text to add
        font: Font name
        size: Font size
        color: (R, G, B) color tuple
        x: X position for the text
        y: Y position for the text
        
    Returns:
        The newly created text layer
    """
    try:
        # Save current context
        old_fg = pdb.gimp_context_get_foreground()
        
        # Set text color
        pdb.gimp_context_set_foreground(color)
        
        # Create the text layer
        text_layer = pdb.gimp_text_fontname(
            image, None, x, y, text, 0, True, size, PIXELS, font
        )
        
        # Restore context
        pdb.gimp_context_set_foreground(old_fg)
        
        return text_layer
    except Exception as e:
        log(f"Error adding text layer: {str(e)}", "ERROR")
        raise

# Transform Operations
def resize_image(image, width: int, height: int, offset_x: int = 0, offset_y: int = 0):
    """
    Resize the image to the specified dimensions.
    
    Args:
        image: The GIMP image object
        width: New width
        height: New height
        offset_x: X offset
        offset_y: Y offset
    """
    try:
        pdb.gimp_image_resize(image, width, height, offset_x, offset_y)
    except Exception as e:
        log(f"Error resizing image: {str(e)}", "ERROR")
        raise

def scale_image(image, width: int, height: int, interpolation: int = INTERPOLATION_LINEAR):
    """
    Scale the image to the specified dimensions.
    
    Args:
        image: The GIMP image object
        width: New width
        height: New height
        interpolation: Interpolation method
    """
    try:
        pdb.gimp_image_scale(image, width, height)
    except Exception as e:
        log(f"Error scaling image: {str(e)}", "ERROR")
        raise

def scale_layer(drawable, width: int, height: int, interpolation: int = INTERPOLATION_LINEAR):
    """
    Scale the drawable to the specified dimensions.
    
    Args:
        drawable: The GIMP drawable object
        width: New width
        height: New height
        interpolation: Interpolation method
    """
    try:
        pdb.gimp_layer_scale(drawable, width, height, True)
    except Exception as e:
        log(f"Error scaling layer: {str(e)}", "ERROR")
        raise

def rotate_layer(drawable, angle: float, center_x: Optional[float] = None, 
               center_y: Optional[float] = None):
    """
    Rotate the drawable by the specified angle.
    
    Args:
        drawable: The GIMP drawable object
        angle: Rotation angle (in degrees)
        center_x: X coordinate of rotation center (default: center of drawable)
        center_y: Y coordinate of rotation center (default: center of drawable)
    """
    try:
        if center_x is None:
            center_x = drawable.width / 2
        if center_y is None:
            center_y = drawable.height / 2
            
        # Convert angle to radians (GIMP uses radians for rotation)
        angle_rad = angle * (3.14159265358979323846 / 180.0)
        
        pdb.gimp_item_transform_rotate(drawable, angle_rad, True, center_x, center_y)
    except Exception as e:
        log(f"Error rotating layer: {str(e)}", "ERROR")
        raise

# Utility Functions
def get_active_image():
    """
    Get the currently active image.
    
    Returns:
        The active GIMP image or None if no image is open
    """
    try:
        return gimp.image_list()[0] if gimp.image_list() else None
    except Exception as e:
        log(f"Error getting active image: {str(e)}", "ERROR")
        raise

def get_active_drawable(image = None):
    """
    Get the currently active drawable.
    
    Args:
        image: The GIMP image object (if None, use active image)
        
    Returns:
        The active drawable or None if no drawable is active
    """
    try:
        if image is None:
            image = get_active_image()
            
        if image:
            return image.active_drawable
        return None
    except Exception as e:
        log(f"Error getting active drawable: {str(e)}", "ERROR")
        raise

def undo_group_start(image):
    """
    Start an undo group.
    
    Args:
        image: The GIMP image object
    """
    try:
        pdb.gimp_image_undo_group_start(image)
    except Exception as e:
        log(f"Error starting undo group: {str(e)}", "ERROR")
        raise

def undo_group_end(image):
    """
    End an undo group.
    
    Args:
        image: The GIMP image object
    """
    try:
        pdb.gimp_image_undo_group_end(image)
    except Exception as e:
        log(f"Error ending undo group: {str(e)}", "ERROR")
        raise

def copy_to_clipboard(drawable):
    """
    Copy the drawable to the clipboard.
    
    Args:
        drawable: The GIMP drawable object
    """
    try:
        pdb.gimp_edit_copy(drawable)
    except Exception as e:
        log(f"Error copying to clipboard: {str(e)}", "ERROR")
        raise

def paste_from_clipboard(drawable, as_new_layer: bool = True):
    """
    Paste from the clipboard.
    
    Args:
        drawable: The GIMP drawable object to paste into
        as_new_layer: Whether to paste as a new layer
        
    Returns:
        The floating selection or new layer
    """
    try:
        image = pdb.gimp_item_get_image(drawable)
        floating = pdb.gimp_edit_paste(drawable, False)
        
        if not as_new_layer:
            pdb.gimp_floating_sel_anchor(floating)
            return None
        
        return floating
    except Exception as e:
        log(f"Error pasting from clipboard: {str(e)}", "ERROR")
        raise

def set_foreground_color(color: Tuple[float, float, float]):
    """
    Set the foreground color.
    
    Args:
        color: (R, G, B) color tuple
    """
    try:
        pdb.gimp_context_set_foreground(color)
    except Exception as e:
        log(f"Error setting foreground color: {str(e)}", "ERROR")
        raise

def set_background_color(color: Tuple[float, float, float]):
    """
    Set the background color.
    
    Args:
        color: (R, G, B) color tuple
    """
    try:
        pdb.gimp_context_set_background(color)
    except Exception as e:
        log(f"Error setting background color: {str(e)}", "ERROR")
        raise
