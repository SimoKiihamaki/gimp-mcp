#!/usr/bin/env python3
"""
Socket-based MCP Client for GIMP plugin.

This module provides an alternative to the HTTP JSON-RPC client,
using a direct socket connection for better compatibility with the
Model Context Protocol (MCP) standard and the libreearth/gimp-mcp approach.
"""
import json
import logging
import socket
import random
import os
import threading
import time
from typing import Dict, Any, Optional, Callable

# Setup logging - use GIMP's console if available
try:
    # First try GIMP 2.10 interface
    try:
        from gimpfu import pdb, gimp
        def log_message(message):
            pdb.gimp_message(str(message))
    except ImportError:
        # Then try GIMP 3.0 interface
        try:
            import gi
            gi.require_version('Gimp', '3.0')
            from gi.repository import Gimp
            def log_message(message):
                Gimp.message(str(message))
        except ImportError:
            # Fallback to standard logging
            logging.basicConfig(level=logging.INFO)
            logger = logging.getLogger(__name__)
            def log_message(message):
                logger.info(message)
except ImportError:
    # Fallback to standard logging if not running in GIMP
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    def log_message(message):
        logger.info(message)

# Default socket server settings
DEFAULT_HOST = os.environ.get("MCP_SOCKET_HOST", "localhost")
DEFAULT_PORT = int(os.environ.get("MCP_SOCKET_PORT", "9876"))

# Authentication key if available
API_KEY = os.environ.get("MCP_API_KEY", None)

class MCPSocketClient:
    """Socket-based MCP client for GIMP plugin."""
    
    def __init__(self, host=DEFAULT_HOST, port=DEFAULT_PORT):
        """Initialize the socket client."""
        self.host = host
        self.port = port
        self.sock = None
        self.connected = False
        self.lock = threading.Lock()  # Thread lock for socket operations
        
    def connect(self):
        """Connect to the MCP socket server."""
        if self.connected and self.sock:
            return True
            
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.host, self.port))
            self.connected = True
            log_message(f"Connected to MCP server at {self.host}:{self.port}")
            return True
        except Exception as e:
            log_message(f"Failed to connect to MCP server: {e}")
            self.sock = None
            self.connected = False
            return False
            
    def disconnect(self):
        """Disconnect from the MCP socket server."""
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
            self.sock = None
            self.connected = False
            
    def send_request(self, method: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Send a request to the MCP server.
        
        Args:
            method: The method name to call
            params: The parameters for the method
            
        Returns:
            The result or None if the request failed
        """
        with self.lock:  # Ensure thread safety
            if not self.connected:
                if not self.connect():
                    return None
                
            # Create the JSON-RPC request
            request_id = random.randint(1, 10000)
            request = {
                "jsonrpc": "2.0",
                "method": method,
                "params": params,
                "id": request_id
            }
            
            # Add API key if available
            if API_KEY:
                request["auth"] = {"api_key": API_KEY}
                
            # Convert to JSON and add newline
            request_str = json.dumps(request) + "\n"
            
            try:
                # Send the request
                self.sock.sendall(request_str.encode('utf-8'))
                
                # Receive the response
                response_data = b''
                while True:
                    data = self.sock.recv(4096)
                    if not data:
                        log_message("Connection closed by server")
                        self.disconnect()
                        return None
                        
                    response_data += data
                    
                    try:
                        # Try to decode the response
                        response_str = response_data.decode('utf-8')
                        
                        # Check if we have a complete response (ends with newline)
                        if '\n' in response_str:
                            response_json = response_str.split('\n')[0]
                            response = json.loads(response_json)
                            break
                    except json.JSONDecodeError:
                        # Not a complete response yet, keep reading
                        continue
                
                # Check for errors
                if "error" in response:
                    error = response["error"]
                    log_message(f"Error from MCP server: {error.get('message', 'Unknown error')}")
                    return None
                    
                # Return the result
                return response.get("result")
                
            except Exception as e:
                log_message(f"Error communicating with MCP server: {e}")
                self.disconnect()
                return None

# Create a global client instance
_client = None

def get_client(host=DEFAULT_HOST, port=DEFAULT_PORT) -> MCPSocketClient:
    """Get the global client instance."""
    global _client
    if _client is None:
        _client = MCPSocketClient(host, port)
    return _client

def send_socket_request(method: str, params: Dict[str, Any], 
                 host=DEFAULT_HOST, port=DEFAULT_PORT) -> Optional[Dict[str, Any]]:
    """
    Send a request to the MCP server using the socket protocol.
    
    Args:
        method: The method name to call
        params: The parameters for the method
        host: The server host (default: from MCP_SOCKET_HOST or localhost)
        port: The server port (default: from MCP_SOCKET_PORT or 9876)
        
    Returns:
        The result or None if the request failed
    """
    client = get_client(host, port)
    return client.send_request(method, params)

def check_socket_server_status(host=DEFAULT_HOST, port=DEFAULT_PORT) -> bool:
    """
    Check if the MCP socket server is running.
    
    Args:
        host: The server host
        port: The server port
        
    Returns:
        True if the server is running, False otherwise
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)  # 2 second timeout
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False
        
# Close the client connection when the module is unloaded
import atexit
def cleanup():
    global _client
    if _client:
        _client.disconnect()
atexit.register(cleanup)
