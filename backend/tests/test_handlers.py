"""
Tests for the request handlers in the MCP server.
"""
import base64
import io
import os
import pytest
from PIL import Image
import numpy as np

import sys
import os
# Add the parent directory to sys.path to allow imports from the backend
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from server.handlers.hello_world import handle_hello_world
from server.handlers.background_removal import handle_background_removal
from server.handlers.inpainting import handle_inpainting
from server.handlers.style_transfer import handle_style_transfer
from server.handlers.upscale import handle_upscale

# Mock the tasks_progress dictionary
sys.modules['server.app'] = type('MockApp', (), {'tasks_progress': {}})

# Helper function to create a test image and return base64 data
def create_test_image(width=100, height=100, color=(255, 0, 0)):
    """Create a test image and return its base64 representation."""
    img = Image.new('RGB', (width, height), color=color)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    base64_string = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return base64_string

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
    return base64_string

@pytest.mark.asyncio
async def test_hello_world():
    """Test the hello_world handler."""
    # Test with name parameter
    result = await handle_hello_world({"name": "Test"})
    assert "message" in result
    assert "Test" in result["message"]
    assert result["status"] == "success"
    
    # Test without name parameter (should use default)
    result = await handle_hello_world({})
    assert "message" in result
    assert "World" in result["message"]
    assert result["status"] == "success"

@pytest.mark.asyncio
async def test_background_removal():
    """Test the background_removal handler."""
    # Create a test image
    image_data = create_test_image()
    
    # Mock the process_background_removal function to avoid actual processing
    import server.handlers.background_removal as bg_module
    original_func = bg_module.process_background_removal
    
    try:
        # Replace with a mock function
        bg_module.process_background_removal = lambda image_data, threshold, use_gpu: image_data
        
        # Test with basic parameters
        result = await handle_background_removal({
            "image_data": image_data,
            "threshold": 0.5,
            "use_gpu": False,
            "task_id": "test-task"
        })
        
        assert "image_data" in result
        assert result["status"] == "success"
        assert "task_id" in result
        
        # Test error handling (missing image_data)
        with pytest.raises(ValueError):
            await handle_background_removal({
                "threshold": 0.5
            })
    finally:
        # Restore the original function
        bg_module.process_background_removal = original_func

@pytest.mark.asyncio
async def test_inpainting():
    """Test the inpainting handler."""
    # Create a test image and mask
    image_data = create_test_image()
    mask_data = create_test_mask()
    
    # Mock the process_inpainting function to avoid actual processing
    import server.handlers.inpainting as inpaint_module
    original_func = inpaint_module.process_inpainting
    
    try:
        # Replace with a mock function
        inpaint_module.process_inpainting = lambda image_data, mask_data, use_gpu: image_data
        
        # Test with basic parameters
        result = await handle_inpainting({
            "image_data": image_data,
            "mask_data": mask_data,
            "use_gpu": False,
            "task_id": "test-task"
        })
        
        assert "image_data" in result
        assert result["status"] == "success"
        assert "task_id" in result
        
        # Test error handling (missing image_data)
        with pytest.raises(ValueError):
            await handle_inpainting({
                "mask_data": mask_data
            })
        
        # Test error handling (missing mask_data)
        with pytest.raises(ValueError):
            await handle_inpainting({
                "image_data": image_data
            })
    finally:
        # Restore the original function
        inpaint_module.process_inpainting = original_func

@pytest.mark.asyncio
async def test_style_transfer():
    """Test the style_transfer handler."""
    # Create a test image
    image_data = create_test_image()
    
    # Mock the process_style_transfer function to avoid actual processing
    import server.handlers.style_transfer as style_module
    original_func = style_module.process_style_transfer
    
    try:
        # Replace with a mock function
        style_module.process_style_transfer = lambda image_data, style_name, strength, use_gpu: image_data
        
        # Test with basic parameters
        result = await handle_style_transfer({
            "image_data": image_data,
            "style_name": "starry_night",
            "strength": 0.8,
            "use_gpu": False,
            "task_id": "test-task"
        })
        
        assert "image_data" in result
        assert result["status"] == "success"
        assert "task_id" in result
        
        # Test with default parameters
        result = await handle_style_transfer({
            "image_data": image_data
        })
        
        assert "image_data" in result
        assert result["status"] == "success"
        
        # Test error handling (missing image_data)
        with pytest.raises(ValueError):
            await handle_style_transfer({
                "style_name": "starry_night"
            })
        
        # Test error handling (invalid strength)
        with pytest.raises(ValueError):
            await handle_style_transfer({
                "image_data": image_data,
                "strength": 1.5  # Should be between 0.0 and 1.0
            })
    finally:
        # Restore the original function
        style_module.process_style_transfer = original_func

@pytest.mark.asyncio
async def test_upscale():
    """Test the upscale handler."""
    # Create a test image
    image_data = create_test_image()
    
    # Mock the process_upscaling function to avoid actual processing
    import server.handlers.upscale as upscale_module
    original_func = upscale_module.process_upscaling
    
    try:
        # Replace with a mock function
        upscale_module.process_upscaling = lambda image_data, scale_factor, denoise_level, sharpen, use_gpu: image_data
        
        # Test with basic parameters
        result = await handle_upscale({
            "image_data": image_data,
            "scale_factor": 2,
            "denoise_level": 0.5,
            "sharpen": True,
            "use_gpu": False,
            "task_id": "test-task"
        })
        
        assert "image_data" in result
        assert result["status"] == "success"
        assert "task_id" in result
        
        # Test with default parameters
        result = await handle_upscale({
            "image_data": image_data
        })
        
        assert "image_data" in result
        assert result["status"] == "success"
        
        # Test error handling (missing image_data)
        with pytest.raises(ValueError):
            await handle_upscale({
                "scale_factor": 2
            })
        
        # Test error handling (invalid scale_factor)
        with pytest.raises(ValueError):
            await handle_upscale({
                "image_data": image_data,
                "scale_factor": 3  # Should be 2, 4, or 8
            })
        
        # Test error handling (invalid denoise_level)
        with pytest.raises(ValueError):
            await handle_upscale({
                "image_data": image_data,
                "denoise_level": 1.5  # Should be between 0.0 and 1.0
            })
    finally:
        # Restore the original function
        upscale_module.process_upscaling = original_func
