#!/bin/bash
# install_gimp_ai_plugin.sh
# Complete installation script for GIMP AI Integration Plugin on macOS

# Exit on error
set -e

# Get directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Print banner
echo "============================================"
echo "GIMP AI Integration - Complete Installation"
echo "============================================"
echo

# Check Python version
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
    echo "❌ Error: Python 3.8 or later is required."
    echo "Current version: $PYTHON_VERSION"
    echo "Please install a newer version of Python and try again."
    exit 1
fi

echo "✅ Python version $PYTHON_VERSION is supported."

# Step 1: Create and set up virtual environment
VENV_DIR="$SCRIPT_DIR/venv"
if [ -d "$VENV_DIR" ]; then
    echo "Virtual environment already exists at $VENV_DIR"
else
    echo "Creating virtual environment at $VENV_DIR..."
    python3 -m venv "$VENV_DIR"
    echo "✅ Virtual environment created successfully"
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"
echo "✅ Virtual environment activated"

# Install dependencies
echo "Installing backend dependencies..."
pip install -r "$SCRIPT_DIR/backend/requirements.txt"
echo "✅ Backend dependencies installed successfully"

echo "Installing frontend dependencies..."
pip install -r "$SCRIPT_DIR/frontend/requirements.txt"
echo "✅ Frontend dependencies installed successfully"

# Step 2: Set up plugin directories
echo
echo "Setting up GIMP plugin for macOS..."

# Define plugin paths
USER_PLUGIN_DIR="$HOME/Library/Application Support/GIMP/3.0/plug-ins"
PLUGIN_DEST="$USER_PLUGIN_DIR/gimp-ai-tools"

# Create necessary directories
mkdir -p "$USER_PLUGIN_DIR"
if [ -d "$PLUGIN_DEST" ]; then
    echo "Removing existing plugin..."
    rm -rf "$PLUGIN_DEST"
fi
mkdir -p "$PLUGIN_DEST"
mkdir -p "$PLUGIN_DEST/client"
mkdir -p "$PLUGIN_DEST/dialogs"
mkdir -p "$PLUGIN_DEST/utils"

# Step 3: Create the main plugin file
echo "Creating main plugin file..."
cat > "$PLUGIN_DEST/gimp-ai-tools.py" << 'EOF'
#!/usr/bin/env python3
# GIMP 3.0 AI Tools Plugin for macOS

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
gi.require_version('GimpUi', '3.0')
from gi.repository import GimpUi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from gi.repository import GLib
from gi.repository import Gio
import os
import sys
import json
import base64
import tempfile
import threading
from urllib.parse import urljoin

# Add the plugin directory to the Python path to find our modules
plugin_dir = os.path.dirname(os.path.abspath(__file__))
if plugin_dir not in sys.path:
    sys.path.append(plugin_dir)

# Import requests module (installed directly to the plugin directory)
import requests

# Message translation functions
def N_(message): return message
def _(message): return GLib.dgettext(None, message)

# Global constants
DEFAULT_SERVER_URL = "http://localhost:8000/jsonrpc"

class GimpAIPlugin(Gimp.PlugIn):
    """Main plugin class for GIMP AI Integration."""
    
    def do_query_procedures(self):
        """Register the plugin procedures."""
        return [
            "python-fu-ai-hello-world",
            "python-fu-ai-background-removal",
            "python-fu-ai-inpainting",
            "python-fu-ai-style-transfer",
            "python-fu-ai-upscale"
        ]
    
    def do_set_i18n(self, name):
        """Set internationalization support."""
        return False
    
    def do_create_procedure(self, name):
        """Create appropriate procedure based on name."""
        # Create procedure object based on name
        if name == "python-fu-ai-hello-world":
            procedure = Gimp.ImageProcedure.new(self, name, Gimp.PDBProcType.PLUGIN, 
                                               self.hello_world, None)
            procedure.set_menu_label(_("Hello World"))
            procedure.set_documentation(_("Test the AI Integration Plugin"),
                                      _("Tests the connection to the MCP server with a hello world message"),
                                      name)
            procedure.add_menu_path('<Image>/Filters/AI Tools/Hello World')
            procedure.set_image_types("*")
                
        elif name == "python-fu-ai-background-removal":
            procedure = Gimp.ImageProcedure.new(self, name, Gimp.PDBProcType.PLUGIN, 
                                               self.background_removal, None)
            procedure.set_menu_label(_("Remove Background"))
            procedure.set_documentation(_("Remove Background with AI"),
                                      _("Uses AI to remove the background from the current layer"),
                                      name)
            procedure.add_menu_path('<Image>/Filters/AI Tools/Remove Background')
            procedure.set_image_types("RGB*, RGBA*")
            
        elif name == "python-fu-ai-inpainting":
            procedure = Gimp.ImageProcedure.new(self, name, Gimp.PDBProcType.PLUGIN, 
                                               self.inpainting, None)
            procedure.set_menu_label(_("Inpainting"))
            procedure.set_documentation(_("Inpaint with AI"),
                                      _("Uses AI to inpaint the selected area of an image"),
                                      name)
            procedure.add_menu_path('<Image>/Filters/AI Tools/Inpainting')
            procedure.set_image_types("RGB*, RGBA*")
            
        elif name == "python-fu-ai-style-transfer":
            procedure = Gimp.ImageProcedure.new(self, name, Gimp.PDBProcType.PLUGIN, 
                                               self.style_transfer, None)
            procedure.set_menu_label(_("Style Transfer"))
            procedure.set_documentation(_("Apply Style Transfer with AI"),
                                      _("Uses AI to apply artistic styles to an image"),
                                      name)
            procedure.add_menu_path('<Image>/Filters/AI Tools/Style Transfer')
            procedure.set_image_types("RGB*, RGBA*")
            
        elif name == "python-fu-ai-upscale":
            procedure = Gimp.ImageProcedure.new(self, name, Gimp.PDBProcType.PLUGIN, 
                                               self.upscale_image, None)
            procedure.set_menu_label(_("Upscale Image"))
            procedure.set_documentation(_("Upscale Image with AI"),
                                      _("Uses AI to upscale an image to a higher resolution"),
                                      name)
            procedure.add_menu_path('<Image>/Filters/AI Tools/Upscale Image')
            procedure.set_image_types("RGB*, RGBA*")
        
        # Set general attributes for all procedures
        procedure.set_attribution("GIMP AI Integration Team", 
                                "GIMP AI Integration Team", "2025")
        
        return procedure
    
    def hello_world(self, procedure, run_mode, image, n_drawables, drawables, config, run_data):
        """Test function to verify the plugin and server connection."""
        # Initialize UI
        GimpUi.init("python-fu-ai-hello-world")
        
        # Try to connect to the server
        try:
            server_url = os.environ.get("MCP_SERVER_URL", DEFAULT_SERVER_URL)
            
            # Create a simple JSON-RPC request
            request_data = {
                "jsonrpc": "2.0",
                "method": "hello_world",
                "params": {"name": "GIMP"},
                "id": 1
            }
            
            # Send the request to the server
            Gimp.message(f"Connecting to MCP server at {server_url}...")
            
            # Send HTTP request
            headers = {"Content-Type": "application/json"}
            response = requests.post(server_url, json=request_data, headers=headers)
            
            # Check for errors
            response.raise_for_status()
            result = response.json()
            
            # Show success message
            if "result" in result and "message" in result["result"]:
                Gimp.message(f"Hello from GIMP AI Integration Plugin!\nServer response: {result['result']['message']}")
            else:
                Gimp.message("Hello from GIMP AI Integration Plugin!\nReceived an unexpected response from the server")
                
        except Exception as e:
            Gimp.message(f"Hello from GIMP AI Integration Plugin!\nError connecting to MCP server: {str(e)}\n\nMake sure the server is running with: ./start_gimp_ai.sh")
        
        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())
    
    def background_removal(self, procedure, run_mode, image, n_drawables, drawables, config, run_data):
        """Remove the background from the current layer with AI."""
        GimpUi.init("python-fu-ai-background-removal")
        Gimp.message("Background removal is coming soon!")
        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())
    
    def inpainting(self, procedure, run_mode, image, n_drawables, drawables, config, run_data):
        """Inpaint the selected region of an image with AI."""
        GimpUi.init("python-fu-ai-inpainting")
        Gimp.message("Inpainting is coming soon!")
        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())
    
    def style_transfer(self, procedure, run_mode, image, n_drawables, drawables, config, run_data):
        """Apply artistic style transfer to an image with AI."""
        GimpUi.init("python-fu-ai-style-transfer")
        Gimp.message("Style transfer is coming soon!")
        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())
    
    def upscale_image(self, procedure, run_mode, image, n_drawables, drawables, config, run_data):
        """Upscale an image to a higher resolution using AI."""
        GimpUi.init("python-fu-ai-upscale")
        Gimp.message("Image upscaling is coming soon!")
        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())

# This is the main function that runs the plugin
Gimp.main(GimpAIPlugin.__gtype__, sys.argv)
EOF

# Make the plugin file executable
chmod +x "$PLUGIN_DEST/gimp-ai-tools.py"

# Step 4: Create standalone plugin for better compatibility
echo "Creating standalone plugin..."
cat > "$USER_PLUGIN_DIR/standalone-ai-tools.py" << 'EOF'
#!/usr/bin/env python3
# Standalone GIMP 3.0 AI Tools Plugin
# This is a minimal version that doesn't depend on external imports

import os
import sys
import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
gi.require_version('GimpUi', '3.0')
from gi.repository import GimpUi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from gi.repository import GLib
from gi.repository import Gio
import json
import threading
import time
import random

def N_(message): return message
def _(message): return GLib.dgettext(None, message)

# Global constants
PLUGIN_VERSION = "0.1.0"
DEFAULT_SERVER_URL = "http://localhost:8000/jsonrpc"

# Simple logging function
def log_message(message):
    try:
        Gimp.message(str(message))
    except:
        print(message)

# Simple JSON-RPC client implementation
def send_request(server_url, method, params):
    """
    Simple implementation to send a JSON-RPC request to the MCP server.
    """
    try:
        import urllib.request
        import urllib.error
        
        # Create the JSON-RPC request
        request_id = random.randint(1, 10000)
        request_data = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": request_id
        }
        
        log_message(f"Sending request to {server_url}: {method}")
        
        # Convert request to JSON and encode as bytes
        json_data = json.dumps(request_data).encode('utf-8')
        
        # Create the request object
        req = urllib.request.Request(
            server_url,
            data=json_data,
            headers={"Content-Type": "application/json"}
        )
        
        # Send the request
        with urllib.request.urlopen(req) as response:
            # Read and decode the response
            response_data = response.read().decode('utf-8')
            result = json.loads(response_data)
            
            # Check for JSON-RPC errors
            if "error" in result:
                error_message = result["error"].get("message", "Unknown error")
                log_message(f"JSON-RPC error: {error_message}")
                return None
            
            # Return the result
            return result.get("result")
    except Exception as e:
        log_message(f"Error in send_request: {str(e)}")
        return None

class GimpAITools(Gimp.PlugIn):
    """Main plugin class for GIMP AI Integration."""
    
    ## PDB Name registration
    def do_query_procedures(self):
        """Register the plugin procedures."""
        return [
            "python-fu-ai-hello-world-standalone",
            "python-fu-ai-background-removal-standalone"
        ]
    
    def do_set_i18n(self, name):
        """Set internationalization support."""
        return False
    
    def do_create_procedure(self, name):
        """Create appropriate procedure based on name."""
        # Create procedure object based on name
        if name == "python-fu-ai-hello-world-standalone":
            procedure = Gimp.ImageProcedure.new(self, name, Gimp.PDBProcType.PLUGIN, 
                                              self.hello_world, None)
            procedure.set_menu_label(_("Hello World (Standalone)"))
            procedure.set_documentation(_("Test the AI Integration Plugin - Standalone Version"),
                                      _("Tests the connection to the MCP server with a hello world message"),
                                      name)
            procedure.add_menu_path('<Image>/Filters/AI Tools/Hello World (Standalone)')
            procedure.set_image_types("*")
                
        elif name == "python-fu-ai-background-removal-standalone":
            procedure = Gimp.ImageProcedure.new(self, name, Gimp.PDBProcType.PLUGIN, 
                                              self.background_removal, None)
            procedure.set_menu_label(_("Remove Background (Standalone)"))
            procedure.set_documentation(_("Remove Background with AI - Standalone Version"),
                                      _("Uses AI to remove the background from the current layer"),
                                      name)
            procedure.add_menu_path('<Image>/Filters/AI Tools/Remove Background (Standalone)')
            procedure.set_image_types("RGB*, RGBA*")
        
        # Set general attributes for all procedures
        procedure.set_attribution("GIMP AI Integration Team", 
                                "GIMP AI Integration Team", "2025")
        
        return procedure
    
    def hello_world(self, procedure, run_mode, image, n_drawables, drawables, config, run_data):
        """Test function to verify the plugin and server connection."""
        # Initialize UI
        GimpUi.init("python-fu-ai-hello-world-standalone")
        
        # Show dialog with connection test options
        dialog = GimpUi.Dialog(title="AI Integration Test", role="ai-hello-world-dialog")
        dialog.add_button(_("_Cancel"), Gtk.ResponseType.CANCEL)
        dialog.add_button(_("_Test Connection"), Gtk.ResponseType.OK)
        
        # Get content area
        content_area = dialog.get_content_area()
        
        # Create label
        label = Gtk.Label(label="Test connection to the MCP server")
        content_area.add(label)
        
        # Create server URL entry
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        url_label = Gtk.Label(label="Server URL:")
        hbox.pack_start(url_label, False, False, 0)
        
        url_entry = Gtk.Entry()
        url_entry.set_text(os.environ.get("MCP_SERVER_URL", DEFAULT_SERVER_URL))
        url_entry.set_width_chars(30)
        hbox.pack_start(url_entry, True, True, 0)
        
        content_area.add(hbox)
        
        # Show dialog
        dialog.show_all()
        response = dialog.run()
        
        if response == Gtk.ResponseType.OK:
            server_url = url_entry.get_text()
            
            # Close dialog
            dialog.destroy()
            
            # Try to connect to the server
            try:
                # Display progress dialog
                progress_dialog = GimpUi.Dialog(title="Testing Connection", role="ai-progress-dialog")
                progress_content = progress_dialog.get_content_area()
                progress_label = Gtk.Label(label=f"Testing connection to: {server_url}\nPlease wait...")
                progress_content.add(progress_label)
                progress_dialog.show_all()
                
                # Process GTK events to show the dialog
                while Gtk.events_pending():
                    Gtk.main_iteration()
                
                # Try to send a request
                response = send_request(server_url, "hello_world", {"name": "GIMP"})
                
                # Close progress dialog
                progress_dialog.destroy()
                
                # Show result
                if response and "message" in response:
                    Gimp.message(f"Success! Server response: {response['message']}")
                else:
                    Gimp.message("Connected to server but received unexpected response. Check server logs.")
            except Exception as e:
                Gimp.message(f"Error connecting to MCP server: {str(e)}\n\nMake sure the server is running with: ./start_gimp_ai.sh")
                
                # Close progress dialog if it's still open
                try:
                    progress_dialog.destroy()
                except:
                    pass
        else:
            dialog.destroy()
        
        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())
    
    def background_removal(self, procedure, run_mode, image, n_drawables, drawables, config, run_data):
        """Remove the background from the current layer with AI."""
        # Initialize UI
        GimpUi.init("python-fu-ai-background-removal-standalone")
        Gimp.message("Background removal (standalone) is not yet implemented for GIMP 3.0")
        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())

# This is the main function that runs the plugin
Gimp.main(GimpAITools.__gtype__, sys.argv)
EOF

# Make the standalone plugin executable
chmod +x "$USER_PLUGIN_DIR/standalone-ai-tools.py"

# Step 5: Install dependencies directly to the plugin directory
echo "Installing Python dependencies directly to the plugin directory..."
python3 -m pip install --target "$PLUGIN_DEST" requests

# Step 6: Create necessary __init__.py files
echo "Creating necessary __init__.py files..."
touch "$PLUGIN_DEST/__init__.py"
touch "$PLUGIN_DEST/client/__init__.py"
touch "$PLUGIN_DEST/dialogs/__init__.py"
touch "$PLUGIN_DEST/utils/__init__.py"

# Step 7: Create unified server start script
echo "Creating server start script..."
cat > "$SCRIPT_DIR/start_gimp_ai.sh" << 'EOF'
#!/bin/bash
# start_gimp_ai.sh
# Script to start the GIMP AI Integration server(s)

# Get directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Activate virtual environment if it exists
if [ -d "$SCRIPT_DIR/venv" ]; then
    source "$SCRIPT_DIR/venv/bin/activate"
    echo "✅ Virtual environment activated"
else
    echo "⚠️ Virtual environment not found. Using system Python."
fi

# Set environment variables
export MCP_SERVER_URL=http://localhost:8000/jsonrpc
export MCP_SERVER_HOST=localhost
export MCP_SERVER_PORT=8000
export MCP_SOCKET_HOST=localhost
export MCP_SOCKET_PORT=9876
export MCP_PREFER_SOCKET=true

# Determine protocol mode from arguments
PROTOCOL="both"  # Default: start both HTTP and Socket servers
VERBOSE=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --http-only)
            PROTOCOL="http"
            shift
            ;;
        --socket-only)
            PROTOCOL="socket"
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            echo "Usage: $0 [--http-only|--socket-only] [--verbose]"
            echo ""
            echo "Options:"
            echo "  --http-only    Start only the HTTP JSON-RPC server"
            echo "  --socket-only  Start only the Socket JSON-RPC server"
            echo "  --verbose      Enable verbose logging"
            echo "  --help         Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Create log directory if it doesn't exist
mkdir -p "$SCRIPT_DIR/logs"

# Start servers based on protocol mode
if [ "$PROTOCOL" = "http" ] || [ "$PROTOCOL" = "both" ]; then
    echo "Starting HTTP JSON-RPC server on $MCP_SERVER_HOST:$MCP_SERVER_PORT..."
    if [ "$PROTOCOL" = "both" ]; then
        # Start in background
        if [ "$VERBOSE" = true ]; then
            python "$SCRIPT_DIR/backend/server/app.py" 2>&1 | tee "$SCRIPT_DIR/logs/http_server.log" &
        else
            python "$SCRIPT_DIR/backend/server/app.py" > "$SCRIPT_DIR/logs/http_server.log" 2>&1 &
        fi
        HTTP_PID=$!
        echo "✅ HTTP server started (PID: $HTTP_PID)"
    else
        # Start in foreground
        if [ "$VERBOSE" = true ]; then
            python "$SCRIPT_DIR/backend/server/app.py" 2>&1 | tee "$SCRIPT_DIR/logs/http_server.log"
        else
            python "$SCRIPT_DIR/backend/server/app.py"
        fi
    fi
fi

if [ "$PROTOCOL" = "socket" ] || [ "$PROTOCOL" = "both" ]; then
    echo "Starting Socket JSON-RPC server on $MCP_SOCKET_HOST:$MCP_SOCKET_PORT..."
    if [ "$PROTOCOL" = "both" ]; then
        # Start in background
        if [ "$VERBOSE" = true ]; then
            python "$SCRIPT_DIR/backend/server/socket_server.py" 2>&1 | tee "$SCRIPT_DIR/logs/socket_server.log" &
        else
            python "$SCRIPT_DIR/backend/server/socket_server.py" > "$SCRIPT_DIR/logs/socket_server.log" 2>&1 &
        fi
        SOCKET_PID=$!
        echo "✅ Socket server started (PID: $SOCKET_PID)"
    else
        # Start in foreground
        if [ "$VERBOSE" = true ]; then
            python "$SCRIPT_DIR/backend/server/socket_server.py" 2>&1 | tee "$SCRIPT_DIR/logs/socket_server.log"
        else
            python "$SCRIPT_DIR/backend/server/socket_server.py"
        fi
    fi
fi

# If both servers are running, wait for either to exit
if [ "$PROTOCOL" = "both" ]; then
    echo ""
    echo "Both servers are now running."
    echo "To test the connection from GIMP, launch GIMP and select:"
    echo "  Filters > AI Tools > Hello World"
    echo ""
    echo "Press Ctrl+C to stop all servers."
    echo "Logs are saved in $SCRIPT_DIR/logs/"
    echo ""
    
    # Wait for Ctrl+C
    trap "echo 'Stopping servers...'; kill $HTTP_PID $SOCKET_PID 2>/dev/null; exit 0" INT TERM
    wait $HTTP_PID $SOCKET_PID
fi
EOF

# Make the server start script executable
chmod +x "$SCRIPT_DIR/start_gimp_ai.sh"

# Remove redundant scripts
echo "Removing redundant scripts..."
rm -f "$SCRIPT_DIR/fix_gimp3_plugin.sh" 2>/dev/null || true
rm -f "$SCRIPT_DIR/fix_gimp3_plugin_complete.sh" 2>/dev/null || true
rm -f "$SCRIPT_DIR/install_gimp_ai.sh" 2>/dev/null || true
rm -f "$SCRIPT_DIR/start_mcp_server.sh" 2>/dev/null || true
rm -f "$SCRIPT_DIR/scripts/fix_gimp3_plugin.sh" 2>/dev/null || true

# Print final instructions
echo
echo "============================================"
echo "GIMP AI Integration - Setup Complete!"
echo "============================================"
echo
echo "To start the MCP server:"
echo "  $SCRIPT_DIR/start_gimp_ai.sh"
echo
echo "Then launch GIMP and use the AI features under:"
echo "  Filters > AI Tools"
echo
echo "To test the connection, try the 'Hello World' option first."
echo
echo "Troubleshooting:"
echo "1. If the plugin doesn't appear in GIMP's menu:"
echo "   - Restart GIMP"
echo "   - Check that the plugin is in the correct directory:"
echo "     GIMP 3.0: $PLUGIN_DEST"
echo
echo "2. If the server won't start:"
echo "   - Check that Python and all dependencies are installed"
echo "   - Try running with --verbose flag for more details"
echo "   - Check logs in the logs/ directory"
echo
echo "3. If the plugin can't connect to the server:"
echo "   - Make sure both servers are running"
echo "   - Check that no firewall is blocking connections"
echo "   - Try using the socket server with --socket-only flag"
echo "   - Try the standalone version at Filters > AI Tools > Hello World (Standalone)"
echo
echo "Additional flags for start_gimp_ai.sh:"
echo "  --http-only: Use only HTTP server"
echo "  --socket-only: Use only socket server"
echo "  --verbose: Show detailed logs"
echo
echo "Enjoy using GIMP AI Integration!"
echo "============================================"
