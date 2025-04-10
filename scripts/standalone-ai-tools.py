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
