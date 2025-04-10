"""
Claude Desktop Helper Library for GIMP MCP Integration.

This library provides a simple interface for Claude Desktop to interact
with the GIMP MCP API for image creation and editing tasks.
"""
import requests
import json
import base64
import os
from typing import Dict, Any, List, Optional, Union, Tuple

class GimpMCPClient:
    """
    Client for the GIMP MCP API.
    
    This class provides a simple interface for Claude Desktop to interact
    with the GIMP MCP API for image creation and editing tasks.
    """
    
    def __init__(self, server_url: str = "http://localhost:8000/jsonrpc", api_key: Optional[str] = None):
        """
        Initialize the GIMP MCP client.
        
        Args:
            server_url: URL of the MCP server
            api_key: API key for authentication
        """
        self.server_url = server_url
        self.api_key = api_key
        self.session_id = None
    
    def _send_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send a JSON-RPC request to the MCP server.
        
        Args:
            method: JSON-RPC method name
            params: Parameters for the method
            
        Returns:
            Response data or raises an exception
        """
        # Create the JSON-RPC request
        request_id = 1  # Use a fixed ID for simplicity
        request_data = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": request_id
        }
        
        # Prepare headers
        headers = {"Content-Type": "application/json"}
        
        # Add API key header if available
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        
        # Send the request
        response = requests.post(
            self.server_url,
            json=request_data,
            headers=headers
        )
        
        # Check for HTTP errors
        response.raise_for_status()
        
        # Parse the response
        result = response.json()
        
        # Check for JSON-RPC errors
        if "error" in result:
            error_message = result["error"].get("message", "Unknown error")
            raise Exception(f"JSON-RPC error: {error_message}")
        
        # Return the result
        return result.get("result")
    
    def create_new_image(self, width: int = 1000, height: int = 1000, 
                       color: Tuple[int, int, int, int] = (255, 255, 255, 255)) -> str:
        """
        Create a new image.
        
        Args:
            width: Width of the new image
            height: Height of the new image
            color: RGBA color tuple for the background
            
        Returns:
            Session ID for the new image
        """
        result = self._send_request("mcp_operation", {
            "operation": "create_new_image",
            "width": width,
            "height": height,
            "color": color
        })
        
        # Save the session ID
        self.session_id = result.get("session_id")
        
        return self.session_id
    
    def open_image(self, image_path: str) -> str:
        """
        Open an existing image.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Session ID for the opened image
        """
        # Read the image file
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")
        
        # Send the request
        result = self._send_request("mcp_operation", {
            "operation": "open_image",
            "image_data": image_data
        })
        
        # Save the session ID
        self.session_id = result.get("session_id")
        
        return self.session_id
    
    def save_image(self, output_path: str, format: str = "PNG", quality: int = 95) -> bool:
        """
        Save the current image.
        
        Args:
            output_path: Path to save the image
            format: Image format (PNG, JPEG, etc.)
            quality: Image quality (1-100)
            
        Returns:
            True if successful
        """
        if not self.session_id:
            raise Exception("No active session. Create or open an image first.")
        
        # Send the request
        result = self._send_request("mcp_operation", {
            "operation": "save_image",
            "session_id": self.session_id,
            "format": format,
            "quality": quality
        })
        
        # Get the image data
        image_data = result.get("image_data")
        if not image_data:
            raise Exception("No image data returned")
        
        # Save the image
        image_bytes = base64.b64decode(image_data)
        with open(output_path, "wb") as f:
            f.write(image_bytes)
        
        return True
    
    def analyze_image(self, analysis_type: str = "detailed") -> Dict[str, Any]:
        """
        Analyze the current image.
        
        Args:
            analysis_type: Type of analysis to perform (basic, detailed)
            
        Returns:
            Analysis results
        """
        if not self.session_id:
            raise Exception("No active session. Create or open an image first.")
        
        # Send the request
        result = self._send_request("image_analysis", {
            "session_id": self.session_id,
            "analysis_type": analysis_type
        })
        
        return result.get("analysis", {})
    
    def execute_commands(self, commands: List[Dict[str, Any]], include_image_data: bool = False) -> Dict[str, Any]:
        """
        Execute a sequence of commands.
        
        Args:
            commands: List of commands to execute
            include_image_data: Whether to include the resulting image data
            
        Returns:
            Execution results
        """
        params = {
            "commands": commands,
            "include_image_data": include_image_data
        }
        
        # Add session ID if available
        if self.session_id:
            params["session_id"] = self.session_id
        
        # Send the request
        result = self._send_request("execute_gimp_commands", params)
        
        # Update session ID if a new one was created
        if "session_id" in result:
            self.session_id = result["session_id"]
        
        return result
    
    def close_session(self) -> bool:
        """
        Close the current session.
        
        Returns:
            True if successful
        """
        if not self.session_id:
            return True  # No session to close
        
        # Send the request
        result = self._send_request("mcp_close_session", {
            "session_id": self.session_id
        })
        
        # Clear the session ID
        self.session_id = None
        
        return result.get("success", False)
    
    def get_ai_assistance(self, message: str, include_image_state: bool = True) -> Dict[str, Any]:
        """
        Get AI assistance for image editing.
        
        Args:
            message: User message
            include_image_state: Whether to include the current image state
            
        Returns:
            AI response with suggestions
        """
        params = {
            "message": message
        }
        
        # Add session ID if available
        if self.session_id and include_image_state:
            params["session_id"] = self.session_id
        
        # Send the request
        result = self._send_request("ai_assistant", params)
        
        return result
    
    def apply_suggestion(self, suggestion: Dict[str, Any]) -> bool:
        """
        Apply a suggestion from the AI assistant.
        
        Args:
            suggestion: Suggestion from AI assistant
            
        Returns:
            True if successful
        """
        if not self.session_id:
            raise Exception("No active session. Create or open an image first.")
        
        # Extract operation and parameters
        operation = suggestion.get("operation")
        parameters = suggestion.get("parameters", {})
        
        if not operation:
            raise Exception("Invalid suggestion. No operation specified.")
        
        # Add session ID to parameters
        parameters["session_id"] = self.session_id
        
        # Send the request
        result = self._send_request("mcp_operation", {
            "operation": operation,
            **parameters
        })
        
        return result.get("success", False)
    
    # Helper methods for common operations
    
    def resize_image(self, width: int, height: int) -> bool:
        """
        Resize the current image.
        
        Args:
            width: New width
            height: New height
            
        Returns:
            True if successful
        """
        if not self.session_id:
            raise Exception("No active session. Create or open an image first.")
        
        # Send the request
        result = self._send_request("mcp_operation", {
            "operation": "resize_image",
            "session_id": self.session_id,
            "width": width,
            "height": height
        })
        
        return result.get("success", False)
    
    def apply_blur(self, radius: float = 5.0) -> bool:
        """
        Apply a Gaussian blur to the image.
        
        Args:
            radius: Blur radius
            
        Returns:
            True if successful
        """
        if not self.session_id:
            raise Exception("No active session. Create or open an image first.")
        
        # Send the request
        result = self._send_request("mcp_operation", {
            "operation": "apply_blur",
            "session_id": self.session_id,
            "radius": radius
        })
        
        return result.get("success", False)
    
    def adjust_brightness_contrast(self, brightness: int = 0, contrast: int = 0) -> bool:
        """
        Adjust brightness and contrast.
        
        Args:
            brightness: Brightness adjustment (-100 to 100)
            contrast: Contrast adjustment (-100 to 100)
            
        Returns:
            True if successful
        """
        if not self.session_id:
            raise Exception("No active session. Create or open an image first.")
        
        # Send the request
        result = self._send_request("mcp_operation", {
            "operation": "adjust_brightness_contrast",
            "session_id": self.session_id,
            "brightness": brightness,
            "contrast": contrast
        })
        
        return result.get("success", False)
    
    def add_text(self, text: str, x: int, y: int, font: str = "Arial", 
               size: int = 24, color: Tuple[int, int, int] = (0, 0, 0)) -> bool:
        """
        Add text to the image.
        
        Args:
            text: Text content
            x: X position
            y: Y position
            font: Font name
            size: Font size
            color: RGB color tuple
            
        Returns:
            True if successful
        """
        if not self.session_id:
            raise Exception("No active session. Create or open an image first.")
        
        # Send the request
        result = self._send_request("mcp_operation", {
            "operation": "add_text_layer",
            "session_id": self.session_id,
            "text": text,
            "x": x,
            "y": y,
            "font": font,
            "size": size,
            "color": color
        })
        
        return result.get("success", False)

# Example usage:
if __name__ == "__main__":
    # Create a client
    client = GimpMCPClient()
    
    try:
        # Create a new image
        session_id = client.create_new_image(800, 600)
        print(f"Created new image with session ID: {session_id}")
        
        # Add some text
        client.add_text("Hello, Claude Desktop!", 100, 300)
        
        # Apply a blur
        client.apply_blur(10.0)
        
        # Save the image
        client.save_image("output.png")
        print("Image saved to output.png")
        
        # Analyze the image
        analysis = client.analyze_image()
        print("Image analysis:", json.dumps(analysis, indent=2))
        
        # Get AI assistance
        response = client.get_ai_assistance("Can you make this image brighter?")
        print("AI response:", response.get("message"))
        
        # Apply the suggestion if available
        if "suggestion" in response:
            client.apply_suggestion(response["suggestion"])
            print("Applied AI suggestion")
            
            # Save the updated image
            client.save_image("output_bright.png")
            print("Updated image saved to output_bright.png")
        
    finally:
        # Close the session
        client.close_session()
        print("Session closed")
