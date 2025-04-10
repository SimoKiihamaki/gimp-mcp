"""
MCP Client for GIMP plugin.

This module handles communication with the MCP server using JSON-RPC.
"""
import json
import logging
import random
import time
import threading
from typing import Dict, Any, Optional, Callable

import requests

# Setup logging - use GIMP's console if available
try:
    from gimpfu import pdb, gimp
    def log_message(message):
        pdb.gimp_message(str(message))
except ImportError:
    # Fallback to standard logging if not running in GIMP
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    def log_message(message):
        logger.info(message)

# Get API key from environment if available
API_KEY = os.environ.get("MCP_API_KEY", None)

def send_request(server_url: str, method: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Send a JSON-RPC request to the MCP server.
    
    Args:
        server_url: URL of the MCP server
        method: JSON-RPC method name
        params: Parameters for the method
        
    Returns:
        Response data or None if the request failed
    """
    try:
        # Create the JSON-RPC request
        request_id = random.randint(1, 10000)  # Generate a random request ID
        request_data = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": request_id
        }
        
        log_message(f"Sending request to {server_url}: {method}")
        
        # Prepare headers
        headers = {"Content-Type": "application/json"}
        
        # Add API key header if available
        if API_KEY:
            headers["X-API-Key"] = API_KEY
        
        # Send the request
        response = requests.post(
            server_url,
            json=request_data,
            headers=headers,
            verify=not os.environ.get("MCP_DISABLE_SSL_VERIFY", "false").lower() == "true"  # Allow disabling SSL verification for self-signed certs
        )
        
        # Check for HTTP errors
        response.raise_for_status()
        
        # Parse the response
        result = response.json()
        
        # Check for JSON-RPC errors
        if "error" in result:
            error_message = result["error"].get("message", "Unknown error")
            log_message(f"JSON-RPC error: {error_message}")
            return None
        
        # Return the result
        return result.get("result")
    except requests.exceptions.RequestException as e:
        log_message(f"Network error: {str(e)}")
        return None
    except json.JSONDecodeError:
        log_message("Invalid JSON response from server")
        return None
    except Exception as e:
        log_message(f"Unexpected error: {str(e)}")
        return None

def check_server_status(server_url: str) -> bool:
    """
    Check if the MCP server is running.
    
    Args:
        server_url: URL of the MCP server
        
    Returns:
        True if the server is running, False otherwise
    """
    try:
        # Extract base URL without the JSON-RPC endpoint
        base_url = server_url.rsplit('/', 1)[0]
        
        # Send a GET request to the root endpoint
        response = requests.get(base_url)
        
        # Check if the response is successful
        return response.status_code == 200
    except Exception:
        return False

def monitor_progress(server_url: str, task_id: str, 
                     update_callback: Callable[[Dict[str, Any]], None], 
                     check_interval: float = 0.5,
                     timeout: float = 300.0) -> None:
    """
    Monitor the progress of a long-running task using polling.
    
    Args:
        server_url: URL of the MCP server
        task_id: ID of the task to monitor
        update_callback: Function to call with progress updates
        check_interval: How often to check for updates (seconds)
        timeout: Maximum time to wait for completion (seconds)
    """
    # Extract base URL without the JSON-RPC endpoint
    base_url = server_url.rsplit('/', 1)[0]
    progress_url = f"{base_url}/progress/{task_id}"
    
    def _monitor_thread():
        start_time = time.time()
        try:
            while True:
                # Check for timeout
                if time.time() - start_time > timeout:
                    update_callback({
                        "progress": 1.0,
                        "status": "error: operation timed out"
                    })
                    break
                
                # Get progress update
                try:
                    response = requests.get(progress_url)
                    if response.status_code == 200:
                        data = response.json()
                        update_callback(data)
                        
                        # Check if task is completed or failed
                        if data.get("status") in ["completed", "error"]:
                            break
                except Exception as e:
                    log_message(f"Error checking progress: {e}")
                
                # Wait before next check
                time.sleep(check_interval)
        except Exception as e:
            log_message(f"Error in progress monitor thread: {e}")
    
    # Start a background thread to monitor progress
    thread = threading.Thread(target=_monitor_thread)
    thread.daemon = True
    thread.start()
