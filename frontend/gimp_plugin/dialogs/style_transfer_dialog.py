"""
Style Transfer Dialog for GIMP.

This module provides a dialog for configuring style transfer options.
"""
from gimpfu import *
import os

# Import our client module
from ..client.mcp_client import send_request

# Global constants
DEFAULT_SERVER_URL = "http://localhost:8000/jsonrpc"

def style_transfer_dialog(server_url=None):
    """
    Show a dialog for style transfer options.
    
    Args:
        server_url (str, optional): URL of the MCP server
        
    Returns:
        dict: Parameters for the style transfer operation, or None if canceled.
    """
    # Get the server URL
    if server_url is None:
        server_url = os.environ.get("MCP_SERVER_URL", DEFAULT_SERVER_URL)
    
    # Fetch available styles from the server
    styles = []
    try:
        response = send_request(server_url, "get_available_styles", {})
        if response and "styles" in response:
            styles = response["styles"]
        else:
            pdb.gimp_message("Failed to fetch styles from the server. Using default styles.")
            # Provide some default styles in case server request fails
            styles = [
                {"id": "starry_night", "name": "Starry Night (Van Gogh)"},
                {"id": "mosaic", "name": "Mosaic"},
                {"id": "candy", "name": "Candy"},
                {"id": "udnie", "name": "Udnie"}
            ]
    except Exception as e:
        pdb.gimp_message(f"Error fetching styles: {str(e)}. Using default styles.")
        # Provide some default styles in case server request fails
        styles = [
            {"id": "starry_night", "name": "Starry Night (Van Gogh)"},
            {"id": "mosaic", "name": "Mosaic"},
            {"id": "candy", "name": "Candy"},
            {"id": "udnie", "name": "Udnie"}
        ]
    
    # Create dialog
    dialog = gimp.Dialog("Style Transfer", "style-transfer-dialog",
                       None, 0, None, None)
    
    # Create a vertical box for the dialog content
    vbox = dialog.vbox
    
    # Add help text
    label = gtk.Label("Apply artistic styles to your image using AI.")
    vbox.pack_start(label, False, False, 5)
    label.show()
    
    # Add a style selection dropdown
    style_frame = gtk.Frame("Style")
    vbox.pack_start(style_frame, False, False, 5)
    style_box = gtk.VBox(False, 5)
    style_frame.add(style_box)
    
    style_combo = gtk.combo_box_new_text()
    for style in styles:
        style_combo.append_text(style["name"])
    # Select first style by default
    style_combo.set_active(0)
    style_box.pack_start(style_combo, False, False, 5)
    style_frame.show_all()
    
    # Add strength slider
    strength_frame = gtk.Frame("Style Strength")
    vbox.pack_start(strength_frame, False, False, 5)
    strength_box = gtk.VBox(False, 5)
    strength_frame.add(strength_box)
    
    # Create an adjustment for the scale (initial value, min, max, step, page, page_size)
    adjustment = gtk.Adjustment(1.0, 0.1, 1.0, 0.1, 0.2, 0)
    
    # Create a horizontal scale with the adjustment
    scale = gtk.HScale(adjustment)
    scale.set_value_pos(gtk.POS_RIGHT)
    scale.set_digits(1)
    strength_box.pack_start(scale, False, False, 5)
    strength_frame.show_all()
    
    # Add a checkbox for creating a new layer with the result
    new_layer_check = gtk.CheckButton("Create new layer with result")
    new_layer_check.set_active(True)  # Default to True
    vbox.pack_start(new_layer_check, False, False, 5)
    new_layer_check.show()
    
    # Add a checkbox for GPU usage
    use_gpu_check = gtk.CheckButton("Use GPU if available")
    use_gpu_check.set_active(True)  # Default to using GPU
    vbox.pack_start(use_gpu_check, False, False, 10)
    use_gpu_check.show()
    
    # Add buttons for OK and Cancel
    dialog.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
    dialog.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
    
    # Show the dialog
    dialog.show_all()
    
    # Run the dialog and get the response
    response = dialog.run()
    
    if response == gtk.RESPONSE_OK:
        # Get the values
        style_index = style_combo.get_active()
        if style_index >= 0 and style_index < len(styles):
            style_id = styles[style_index]["id"]
        else:
            style_id = "starry_night"  # Default style
        
        strength = adjustment.get_value()
        new_layer = new_layer_check.get_active()
        use_gpu = use_gpu_check.get_active()
        
        # Destroy the dialog
        dialog.destroy()
        
        # Return the parameters
        return {
            "style_name": style_id,
            "strength": strength,
            "new_layer": new_layer,
            "use_gpu": use_gpu
        }
    else:
        # Destroy the dialog
        dialog.destroy()
        return None
