#!/usr/bin/env python
"""
Integration test script for GIMP AI Integration.

This script tests the integration between the MCP server and various components,
including API endpoints, model loading, and basic functionality.
"""
import os
import sys
import time
import json
import base64
import unittest
import subprocess
import tempfile
import threading
import requests
from pathlib import Path

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent.absolute()

# Add the project root to the Python path
sys.path.insert(0, str(PROJECT_ROOT))

# Test server port
TEST_SERVER_PORT = 8765

class MCP_ServerThread(threading.Thread):
    """Thread class for running the MCP server in the background."""
    
    def __init__(self):
        threading.Thread.__init__(self)
        self.daemon = True
        self.server_process = None
        self.running = False
        
    def run(self):
        """Run the MCP server."""
        self.running = True
        
        # Set environment variables for the test server
        env = os.environ.copy()
        env["MCP_SERVER_PORT"] = str(TEST_SERVER_PORT)
        env["MCP_SERVER_HOST"] = "127.0.0.1"
        env["MCP_ENABLE_AUTH"] = "false"
        
        # Start the server process
        server_script = os.path.join(PROJECT_ROOT, "backend", "server", "app.py")
        self.server_process = subprocess.Popen(
            [sys.executable, server_script],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for the server to start
        time.sleep(3)  # Allow time for the server to start
        
    def stop(self):
        """Stop the MCP server."""
        if self.server_process:
            self.server_process.terminate()
            self.server_process.wait()
        self.running = False

class IntegrationTest(unittest.TestCase):
    """Integration test for GIMP AI Integration."""
    
    @classmethod
    def setUpClass(cls):
        """Set up the integration test."""
        # Start the MCP server
        cls.server_thread = MCP_ServerThread()
        cls.server_thread.start()
        
        # Wait for the server to start
        time.sleep(3)
        
        # Base URL for the server
        cls.base_url = f"http://127.0.0.1:{TEST_SERVER_PORT}"
        cls.jsonrpc_url = f"{cls.base_url}/jsonrpc"
        
        # Create a test image
        cls.test_image_path = os.path.join(tempfile.gettempdir(), "test_image.png")
        cls.create_test_image(cls.test_image_path)
        
    @classmethod
    def tearDownClass(cls):
        """Tear down the integration test."""
        # Stop the server
        cls.server_thread.stop()
        
        # Clean up test files
        if os.path.exists(cls.test_image_path):
            os.remove(cls.test_image_path)
    
    @classmethod
    def create_test_image(cls, path, width=300, height=200):
        """
        Create a simple test image.
        
        Args:
            path (str): Path to save the image
            width (int): Image width
            height (int): Image height
        """
        try:
            # Try to import PIL
            from PIL import Image, ImageDraw
            
            # Create a new image
            image = Image.new("RGB", (width, height), color=(255, 255, 255))
            
            # Draw something on the image
            draw = ImageDraw.Draw(image)
            draw.rectangle([(50, 50), (width - 50, height - 50)], outline=(0, 0, 0), width=2)
            draw.ellipse([(100, 75), (200, 125)], fill=(255, 0, 0))
            
            # Save the image
            image.save(path)
        except ImportError:
            # If PIL is not available, create a simple file
            with open(path, "wb") as f:
                f.write(b"Test image data")
    
    def send_jsonrpc_request(self, method, params):
        """
        Send a JSON-RPC request to the server.
        
        Args:
            method (str): Method name
            params (dict): Method parameters
            
        Returns:
            dict: Response data
        """
        request_data = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": 1
        }
        
        headers = {"Content-Type": "application/json"}
        response = requests.post(self.jsonrpc_url, json=request_data, headers=headers)
        
        # Check for HTTP errors
        response.raise_for_status()
        
        # Parse the response
        return response.json()
    
    def test_server_health(self):
        """Test the server health endpoint."""
        response = requests.get(self.base_url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertIn("message", data)
    
    def test_hello_world(self):
        """Test the hello_world endpoint."""
        response = self.send_jsonrpc_request("hello_world", {"name": "Integration Test"})
        self.assertIn("result", response)
        self.assertIn("message", response["result"])
        self.assertIn("Integration Test", response["result"]["message"])
    
    def test_get_available_styles(self):
        """Test the get_available_styles endpoint."""
        response = self.send_jsonrpc_request("get_available_styles", {})
        self.assertIn("result", response)
        self.assertIn("styles", response["result"])
        styles = response["result"]["styles"]
        self.assertIsInstance(styles, list)
        self.assertGreater(len(styles), 0)
        
        # Check the structure of each style
        for style in styles:
            self.assertIn("id", style)
            self.assertIn("name", style)
    
    def test_background_removal(self):
        """Test the ai_background_removal endpoint."""
        # Load the test image
        with open(self.test_image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")
        
        # Send the request
        response = self.send_jsonrpc_request("ai_background_removal", {
            "image_data": image_data,
            "threshold": 0.5,
            "use_gpu": False
        })
        
        # Check the response
        self.assertIn("result", response)
        self.assertIn("image_data", response["result"])
        self.assertIn("status", response["result"])
        self.assertEqual(response["result"]["status"], "success")
        
        # Decode the result image
        result_data = base64.b64decode(response["result"]["image_data"])
        self.assertGreater(len(result_data), 0)
    
    def test_inpainting(self):
        """Test the ai_inpainting endpoint."""
        # Load the test image
        with open(self.test_image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")
        
        # Create a simple mask (white rectangle in the center)
        from PIL import Image, ImageDraw
        mask = Image.new("L", (300, 200), color=0)
        draw = ImageDraw.Draw(mask)
        draw.rectangle([(100, 75), (200, 125)], fill=255)
        
        # Save and encode the mask
        mask_path = os.path.join(tempfile.gettempdir(), "test_mask.png")
        mask.save(mask_path)
        with open(mask_path, "rb") as f:
            mask_data = base64.b64encode(f.read()).decode("utf-8")
        
        # Send the request
        response = self.send_jsonrpc_request("ai_inpainting", {
            "image_data": image_data,
            "mask_data": mask_data,
            "use_gpu": False
        })
        
        # Check the response
        self.assertIn("result", response)
        self.assertIn("image_data", response["result"])
        self.assertIn("status", response["result"])
        self.assertEqual(response["result"]["status"], "success")
        
        # Clean up
        if os.path.exists(mask_path):
            os.remove(mask_path)
    
    def test_style_transfer(self):
        """Test the ai_style_transfer endpoint."""
        # Load the test image
        with open(self.test_image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")
        
        # Send the request
        response = self.send_jsonrpc_request("ai_style_transfer", {
            "image_data": image_data,
            "style_name": "starry_night",
            "strength": 0.8,
            "use_gpu": False
        })
        
        # Check the response
        self.assertIn("result", response)
        self.assertIn("image_data", response["result"])
        self.assertIn("status", response["result"])
        self.assertEqual(response["result"]["status"], "success")
    
    def test_upscale(self):
        """Test the ai_upscale endpoint."""
        # Load the test image
        with open(self.test_image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")
        
        # Send the request
        response = self.send_jsonrpc_request("ai_upscale", {
            "image_data": image_data,
            "scale_factor": 2,
            "denoise_level": 0.5,
            "sharpen": True,
            "use_gpu": False
        })
        
        # Check the response
        self.assertIn("result", response)
        self.assertIn("image_data", response["result"])
        self.assertIn("status", response["result"])
        self.assertEqual(response["result"]["status"], "success")
    
    def test_feedback_submission(self):
        """Test the submit_feedback endpoint."""
        # Create test feedback data
        feedback_data = {
            "type": "General Feedback",
            "category": "General",
            "subject": "Integration Test",
            "description": "This is a test feedback submission from the integration test.",
            "system_info": "Test system",
            "name": "Test User",
            "email": "test@example.com",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Send the request
        response = self.send_jsonrpc_request("submit_feedback", {
            "feedback": feedback_data
        })
        
        # Check the response
        self.assertIn("result", response)
        self.assertIn("status", response["result"])
        self.assertEqual(response["result"]["status"], "success")
        self.assertIn("feedback_id", response["result"])

if __name__ == "__main__":
    unittest.main()
