"""
Tests for the AI models used in the MCP server.
"""
import base64
import io
import os
import pytest
from PIL import Image
import numpy as np
import unittest.mock as mock

import sys
import os
# Add the parent directory to sys.path to allow imports from the backend
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import models to test
from server.models.background_removal.u2net import load_image_from_base64, image_to_base64, ESRGANModel, process_background_removal
from server.models.inpainting.lama import load_image_from_base64, image_to_base64, LamaInpaintingModel, process_inpainting
from server.models.style_transfer.fast_style_impl import get_available_styles, process_style_transfer
from server.models.upscale.esrgan import load_image_from_base64, image_to_base64, ESRGANModel, process_upscaling

# Helper function to create a test image and return base64 data
def create_test_image(width=100, height=100, color=(255, 0, 0)):
    """Create a test image and return its base64 representation."""
    img = Image.new('RGB', (width, height), color=color)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    base64_string = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return base64_string, img

# Helper function to create a test mask
def create_test_mask(width=100, height=100, circle_radius=30):
    """Create a test mask with a circle in the center and return its base64 representation."""
    img = Image.new('L', (width, height), color=0)
    # Draw a circle in the center
    center_x, center_y = width // 2, height // 2
    for x in range(width):
        for y in range(height):
            if (x - center_x) ** 2 + (y - center_y) ** 2 < circle_radius ** 2:
                img.putpixel((x, y), 255)
    
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    base64_string = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return base64_string, img

def test_image_conversion_functions():
    """Test the image conversion utility functions used across models."""
    # Generate a test image and convert to base64
    base64_string, original_img = create_test_image(50, 50, (0, 255, 0))
    
    # Test loading image from base64
    loaded_img = load_image_from_base64(base64_string)
    assert isinstance(loaded_img, Image.Image)
    assert loaded_img.size == (50, 50)
    
    # Test converting image back to base64
    new_base64 = image_to_base64(loaded_img)
    assert isinstance(new_base64, str)
    
    # Test loading an image with the data URL prefix
    data_url = f"data:image/png;base64,{base64_string}"
    loaded_img2 = load_image_from_base64(data_url)
    assert isinstance(loaded_img2, Image.Image)
    assert loaded_img2.size == (50, 50)

def test_background_removal():
    """Test the background removal model's basic functionality."""
    # Create a test image
    base64_string, original_img = create_test_image()
    
    # Mock the U2NetModel class to avoid loading actual weights
    with mock.patch('server.models.background_removal.u2net.U2NetModel') as MockModel:
        # Configure the mock to return a simple mask when predict is called
        mock_instance = MockModel.return_value
        mock_instance.remove_background.return_value = original_img
        
        # Test the process_background_removal function
        result_base64 = process_background_removal(
            image_data=base64_string,
            threshold=0.5,
            use_gpu=False
        )
        
        # Verify that the result is a base64 string
        assert isinstance(result_base64, str)
        
        # Verify that the model was called with the correct parameters
        mock_instance.remove_background.assert_called_once()
        args, kwargs = mock_instance.remove_background.call_args
        assert isinstance(args[0], Image.Image)
        assert kwargs.get('threshold') == 0.5

def test_inpainting():
    """Test the inpainting model's basic functionality."""
    # Create a test image and mask
    image_base64, original_img = create_test_image()
    mask_base64, mask_img = create_test_mask()
    
    # Mock the LamaInpaintingModel class to avoid loading actual weights
    with mock.patch('server.models.inpainting.lama.LamaInpaintingModel') as MockModel:
        # Configure the mock to return a simple inpainted image
        mock_instance = MockModel.return_value
        mock_instance.inpaint.return_value = original_img
        
        # Test the process_inpainting function
        result_base64 = process_inpainting(
            image_data=image_base64,
            mask_data=mask_base64,
            use_gpu=False
        )
        
        # Verify that the result is a base64 string
        assert isinstance(result_base64, str)
        
        # Verify that the model was called with the correct parameters
        mock_instance.inpaint.assert_called_once()
        args, kwargs = mock_instance.inpaint.call_args
        assert isinstance(args[0], Image.Image)  # image
        assert isinstance(args[1], Image.Image)  # mask

def test_style_transfer():
    """Test the style transfer functionality."""
    # Create a test image
    image_base64, original_img = create_test_image()
    
    # Mock the fast_style_impl module to avoid loading actual models
    with mock.patch('server.models.style_transfer.fast_style_impl.apply_style') as mock_apply_style:
        # Configure the mock to return a simple styled image
        mock_apply_style.return_value = original_img
        
        # Test the process_style_transfer function
        result_base64 = process_style_transfer(
            image_data=image_base64,
            style_name="mosaic",
            strength=0.8,
            use_gpu=False
        )
        
        # Verify that the result is a base64 string
        assert isinstance(result_base64, str)
        
        # Verify that the apply_style function was called with the correct parameters
        mock_apply_style.assert_called_once()
        args, kwargs = mock_apply_style.call_args
        assert isinstance(args[0], Image.Image)  # image
        assert args[1] == "mosaic"  # style_name
        assert kwargs.get('strength') == 0.8
        assert kwargs.get('use_gpu') is False

def test_get_available_styles():
    """Test the get_available_styles function."""
    # Call the function
    styles = get_available_styles()
    
    # Verify that it returns a list of styles
    assert isinstance(styles, list)
    assert len(styles) > 0
    
    # Verify that each style has an id and name
    for style in styles:
        assert "id" in style
        assert "name" in style
        assert isinstance(style["id"], str)
        assert isinstance(style["name"], str)

def test_upscaling():
    """Test the upscaling model's basic functionality."""
    # Create a test image
    image_base64, original_img = create_test_image()
    
    # Mock the ESRGANModel class to avoid loading actual weights
    with mock.patch('server.models.upscale.esrgan.ESRGANModel') as MockModel:
        # Configure the mock to return a simple upscaled image
        mock_instance = MockModel.return_value
        mock_instance.upscale.return_value = original_img
        
        # Test the process_upscaling function
        result_base64 = process_upscaling(
            image_data=image_base64,
            scale_factor=2,
            denoise_level=0.5,
            sharpen=True,
            use_gpu=False
        )
        
        # Verify that the result is a base64 string
        assert isinstance(result_base64, str)
        
        # Verify that the model was called with the correct parameters
        mock_instance.upscale.assert_called_once()
        args, kwargs = mock_instance.upscale.call_args
        assert isinstance(args[0], Image.Image)  # image
        assert kwargs.get('scale_factor') == 2
        assert kwargs.get('denoise_level') == 0.5
        assert kwargs.get('sharpen') is True
