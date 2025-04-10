#!/usr/bin/env python3
# GIMP 3.0 AI Tools Plugin
# Compatible version specifically for GIMP 3.0 on macOS

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

# Add the plugin directory to the Python path to find our modules
plugin_dir = os.path.dirname(os.path.abspath(__file__))
if plugin_dir not in sys.path:
    sys.path.append(plugin_dir)

# Make sure we can find client modules
client_dir = os.path.join(plugin_dir, 'client')
if client_dir not in sys.path:
    sys.path.append(client_dir)

# Message translation functions
def N_(message): return message
def _(message): return GLib.dgettext(None, message)

# Global constants
PLUGIN_VERSION = "0.1.0"
DEFAULT_SERVER_URL = "http://localhost:8000/jsonrpc"

class GimpAITools(Gimp.PlugIn):
    """Main plugin class for GIMP AI Integration."""
    
    ## PDB Name registration - CRITICAL for GIMP 3.0
    def do_query_procedures(self):
        """Register the plugin procedures."""
        return [
            "python-fu-ai-hello-world",
            "python-fu-ai-background-removal",
            "python-fu-ai-inpainting",
            "python-fu-ai-style-transfer",
            "python-fu-ai-upscale",
            "python-fu-ai-send-feedback",
            "python-fu-ai-assistant",
            "python-fu-ai-analyze-image"
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
            
        elif name == "python-fu-ai-send-feedback":
            procedure = Gimp.ImageProcedure.new(self, name, Gimp.PDBProcType.PLUGIN, 
                                              self.send_user_feedback, None)
            procedure.set_menu_label(_("Send Feedback"))
            procedure.set_documentation(_("Send Feedback"),
                                      _("Submit feedback, bug reports, or feature requests for GIMP AI Integration"),
                                      name)
            procedure.add_menu_path('<Image>/Filters/AI Tools/Send Feedback')
            procedure.set_image_types("*")
            
        elif name == "python-fu-ai-assistant":
            procedure = Gimp.ImageProcedure.new(self, name, Gimp.PDBProcType.PLUGIN, 
                                              self.ai_assistant, None)
            procedure.set_menu_label(_("AI Assistant"))
            procedure.set_documentation(_("AI Assistance for Image Editing"),
                                      _("Get interactive assistance from AI for image editing tasks"),
                                      name)
            procedure.add_menu_path('<Image>/Filters/AI Tools/AI Assistant')
            procedure.set_image_types("*")
            
        elif name == "python-fu-ai-analyze-image":
            procedure = Gimp.ImageProcedure.new(self, name, Gimp.PDBProcType.PLUGIN, 
                                              self.analyze_image, None)
            procedure.set_menu_label(_("Analyze Image"))
            procedure.set_documentation(_("Analyze Image with AI"),
                                      _("Uses AI to analyze the content of the current image"),
                                      name)
            procedure.add_menu_path('<Image>/Filters/AI Tools/Analyze Image')
            procedure.set_image_types("*")
        
        # Set general attributes for all procedures
        procedure.set_attribution("GIMP AI Integration Team", 
                                "GIMP AI Integration Team", "2025")
        
        return procedure
    
    def hello_world(self, procedure, run_mode, image, n_drawables, drawables, config, run_data):
        """Test function to verify the plugin and server connection."""
        # Initialize UI
        GimpUi.init("python-fu-ai-hello-world")
        
        # Import necessary modules here to avoid potential import errors
        try:
            import requests
            from client.mcp_client import send_request
        except ImportError as e:
            Gimp.message(f"Error importing required modules: {e}\nPlease check your Python environment.")
            return procedure.new_return_values(Gimp.PDBStatusType.EXECUTION_ERROR, GLib.Error())
        
        # Try to connect to the server
        try:
            server_url = os.environ.get("MCP_SERVER_URL", DEFAULT_SERVER_URL)
            Gimp.message(f"Checking connection to server at: {server_url}")
            
            response = send_request(server_url, "hello_world", {"name": "GIMP"})
            
            # Show success message
            if response and "message" in response:
                Gimp.message(f"Hello from GIMP AI Integration Plugin!\nServer response: {response['message']}")
            else:
                Gimp.message("Hello from GIMP AI Integration Plugin!\nReceived an unexpected response from the server")
        except Exception as e:
            Gimp.message(f"Hello from GIMP AI Integration Plugin!\nError connecting to MCP server: {str(e)}\n\nMake sure the server is running with: ./start_gimp_ai.sh")
        
        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())
    
    def background_removal(self, procedure, run_mode, image, n_drawables, drawables, config, run_data):
        """Remove the background from the current layer with AI."""
        # Initialize UI
        GimpUi.init("python-fu-ai-background-removal")
        Gimp.message("Background removal is not yet fully implemented for GIMP 3.0")
        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())
    
    def inpainting(self, procedure, run_mode, image, n_drawables, drawables, config, run_data):
        """Inpaint the selected region of an image with AI."""
        GimpUi.init("python-fu-ai-inpainting")
        Gimp.message("Inpainting is not yet fully implemented for GIMP 3.0")
        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())
    
    def style_transfer(self, procedure, run_mode, image, n_drawables, drawables, config, run_data):
        """Apply artistic style transfer to an image with AI."""
        GimpUi.init("python-fu-ai-style-transfer")
        Gimp.message("Style transfer is not yet fully implemented for GIMP 3.0")
        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())
    
    def upscale_image(self, procedure, run_mode, image, n_drawables, drawables, config, run_data):
        """Upscale an image to a higher resolution using AI."""
        GimpUi.init("python-fu-ai-upscale")
        Gimp.message("Image upscaling is not yet fully implemented for GIMP 3.0")
        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())
    
    def send_user_feedback(self, procedure, run_mode, image, n_drawables, drawables, config, run_data):
        """Send feedback about the GIMP AI Integration."""
        GimpUi.init("python-fu-ai-send-feedback")
        Gimp.message("Feedback form is not yet fully implemented for GIMP 3.0")
        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())
    
    def ai_assistant(self, procedure, run_mode, image, n_drawables, drawables, config, run_data):
        """Launch the AI Assistant dialog for interactive image editing assistance."""
        GimpUi.init("python-fu-ai-assistant")
        Gimp.message("AI Assistant is not yet fully implemented for GIMP 3.0")
        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())
    
    def analyze_image(self, procedure, run_mode, image, n_drawables, drawables, config, run_data):
        """Analyze the current image using AI."""
        GimpUi.init("python-fu-ai-analyze-image")
        Gimp.message("Image analysis is not yet fully implemented for GIMP 3.0")
        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())

# This is the main function that runs the plugin
Gimp.main(GimpAITools.__gtype__, sys.argv)
