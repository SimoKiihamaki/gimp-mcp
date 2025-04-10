#!/usr/bin/env python3
"""
Socket-based MCP Server for GIMP AI Integration.

This implementation provides a socket-based alternative to the HTTP JSON-RPC server,
following the Model Context Protocol (MCP) standard. It's designed to be compatible
with the libreearth/gimp-mcp approach.
"""
import socket
import json
import threading
import logging
import os
import sys
import time
import asyncio  # Added for async support
from pathlib import Path

# Add the backend directory to the path so we can import from other modules
backend_dir = Path(__file__).parent.parent.absolute()
if str(backend_dir) not in sys.path:
    sys.path.append(str(backend_dir))

# Add the project root to the path
project_dir = backend_dir.parent.absolute()
if str(project_dir) not in sys.path:
    sys.path.append(str(project_dir))

# Import handlers from the existing implementation - handle both import styles
try:
    # Try local imports first
    from routes.json_rpc import get_handler
    from utils.auth import get_api_key
except ImportError:
    try:
        # Try from server package
        from server.routes.json_rpc import get_handler
        from server.utils.auth import get_api_key
    except ImportError:
        # Fallback implementation if we can't import
        logging.error("Could not import handlers from existing implementation")
        
        def get_handler(method):
            """Fallback handler that just returns a message."""
            def handler(params):
                return {"message": f"Socket server received call to method: {method}"}
            return handler
            
        def get_api_key():
            return os.environ.get("MCP_API_KEY")

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("GimpMCPSocketServer")

# Default host and port
DEFAULT_HOST = os.environ.get("MCP_SOCKET_HOST", "localhost")
DEFAULT_PORT = int(os.environ.get("MCP_SOCKET_PORT", "9876"))

class MCPSocketServer:
    """Socket-based MCP Server implementation."""
    
    def __init__(self, host=DEFAULT_HOST, port=DEFAULT_PORT):
        """Initialize the socket server."""
        self.host = host
        self.port = port
        self.sock = None
        self.running = False
        self.clients = []
        
    def _json_serializer(self, obj):
        """
        Custom serializer for JSON encoding that handles special types like datetime.
        
        Args:
            obj: The object to serialize
            
        Returns:
            A JSON-serializable representation of the object
        """
        import datetime
        
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        elif isinstance(obj, datetime.date):
            return obj.isoformat()
        elif isinstance(obj, set):
            return list(obj)
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        else:
            # Let the default serializer handle it or raise TypeError
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
        
    def start(self):
        """Start the socket server."""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.sock.bind((self.host, self.port))
            self.sock.listen(5)
            self.running = True
            
            logger.info(f"MCP socket server started on {self.host}:{self.port}")
            
            # Accept connections in the main thread
            while self.running:
                try:
                    client, addr = self.sock.accept()
                    logger.info(f"New connection from {addr}")
                    
                    # Start a new thread to handle this client
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client, addr),
                        daemon=True
                    )
                    client_thread.start()
                    self.clients.append((client, client_thread))
                    
                except KeyboardInterrupt:
                    logger.info("Server stopping due to keyboard interrupt")
                    self.stop()
                    break
                except Exception as e:
                    logger.error(f"Error accepting connection: {e}")
                    
        except Exception as e:
            logger.error(f"Failed to start server: {e}")
            if self.sock:
                self.sock.close()
            raise
    
    def stop(self):
        """Stop the socket server."""
        self.running = False
        
        # Close all client connections
        for client, _ in self.clients:
            try:
                client.close()
            except:
                pass
        
        # Close the server socket
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
            
        logger.info("Server stopped")
    
    def handle_client(self, client, addr):
        """Handle client connection."""
        buffer = b''
        
        try:
            while self.running:
                data = client.recv(4096)
                if not data:
                    logger.info(f"Client {addr} disconnected")
                    break
                    
                buffer += data
                
                # Try to parse the JSON message
                try:
                    # Find the end of a complete JSON object
                    message, buffer = self.extract_json(buffer)
                    
                    if message:
                        # Process the message
                        response = self.process_message(message)
                        
                        # Format response with proper JSON (handle datetime objects)
                        response_json = json.dumps(response, default=self._json_serializer)
                        
                        # Send the response with a newline delimiter
                        client.sendall(response_json.encode('utf-8') + b'\n')
                except json.JSONDecodeError:
                    # Not a complete JSON object yet, continue reading
                    continue
                except json.JSONDecodeError as json_err:
                    logger.error(f"JSON parsing error: {json_err}")
                    error_response = {
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32700,  # Parse error according to JSON-RPC spec
                            "message": f"Parse error: {str(json_err)}"
                        },
                        "id": None  # Unable to determine ID for malformed JSON
                    }
                    client.sendall(json.dumps(error_response).encode('utf-8') + b'\n')
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    error_response = {
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32000,
                            "message": str(e)
                        },
                        "id": None
                    }
                    client.sendall(json.dumps(error_response).encode('utf-8') + b'\n')
        
        except ConnectionResetError:
            logger.info(f"Connection reset by client {addr}")
        except Exception as e:
            logger.error(f"Error handling client {addr}: {e}")
        finally:
            client.close()
            
    def extract_json(self, buffer):
        """Extract a complete JSON object from the buffer."""
        # Simple implementation: try to parse from start to end
        try:
            decoded = buffer.decode('utf-8')
            
            # Check if there's a newline-delimited message
            if '\n' in decoded:
                message_str, remaining = decoded.split('\n', 1)
                return json.loads(message_str), remaining.encode('utf-8')
            
            # Try to parse the entire buffer as JSON
            message = json.loads(decoded)
            return message, b''
        except json.JSONDecodeError:
            # Not a complete JSON object yet
            return None, buffer
    
    def process_message(self, message):
        """Process an incoming JSON-RPC message."""
        if not isinstance(message, dict):
            return {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32600,
                    "message": "Invalid Request: not a JSON object"
                },
                "id": None
            }
            
        # Check if it's a valid JSON-RPC request
        if message.get("jsonrpc") != "2.0":
            return {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32600,
                    "message": "Invalid Request: not a JSON-RPC 2.0 request"
                },
                "id": message.get("id", None)
            }
            
        method = message.get("method")
        params = message.get("params", {})
        request_id = message.get("id")
        
        if not method:
            return {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32600,
                    "message": "Invalid Request: method not specified"
                },
                "id": request_id
            }
            
        # Get the appropriate handler
        handler = get_handler(method)
        if not handler:
            return {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32601,
                    "message": f"Method '{method}' not found"
                },
                "id": request_id
            }
            
        # Call the handler
        try:
            # Check if the handler is async
            if asyncio.iscoroutinefunction(handler):
                # Create a new event loop for this thread if needed
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                # Call the async handler
                result = loop.run_until_complete(handler(params))
                loop.close()
            else:
                # Call the synchronous handler
                result = handler(params)
                
            # Return the result
            return {
                "jsonrpc": "2.0",
                "result": result,
                "id": request_id
            }
        except Exception as e:
            logger.exception(f"Error handling request: {e}")
            return {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32000,
                    "message": str(e)
                },
                "id": request_id
            }


def main():
    """Start the socket server."""
    try:
        import asyncio
        
        # Parse command line arguments
        import argparse
        parser = argparse.ArgumentParser(description="Socket-based MCP Server for GIMP AI Integration")
        parser.add_argument("--host", default=DEFAULT_HOST, help=f"Host to bind to (default: {DEFAULT_HOST})")
        parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"Port to bind to (default: {DEFAULT_PORT})")
        args = parser.parse_args()
        
        # Start the server
        server = MCPSocketServer(args.host, args.port)
        server.start()
        
    except KeyboardInterrupt:
        logger.info("Server stopped by keyboard interrupt")
    except Exception as e:
        logger.error(f"Server error: {e}")
        
if __name__ == "__main__":
    main()
