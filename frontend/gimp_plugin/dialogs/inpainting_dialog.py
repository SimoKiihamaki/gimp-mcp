"""
Inpainting Dialog for GIMP.

This module provides a dialog for configuring inpainting options.
"""
from gimpfu import *

def inpainting_dialog():
    """
    Show a dialog for inpainting options.
    
    Returns:
        dict: Parameters for the inpainting operation, or None if canceled.
    """
    # Create dialog
    dialog = gimp.Dialog("AI Inpainting", "inpainting-dialog",
                       None, 0, None, None)
    
    # Create a vertical box for the dialog content
    vbox = dialog.vbox
    
    # Add help text about selection
    label = gtk.Label("Inpaint the selected area with AI-generated content.")
    vbox.pack_start(label, False, False, 5)
    label.show()
    
    # Add a label about making a selection
    selection_label = gtk.Label("Please make a selection before using this tool.\n"
                             "White areas in the selection will be replaced with AI-generated content.")
    selection_label.set_justify(gtk.JUSTIFY_CENTER)
    vbox.pack_start(selection_label, False, False, 10)
    selection_label.show()
    
    # Add section for mask refinement
    frame = gtk.Frame("Mask Options")
    vbox.pack_start(frame, False, False, 5)
    frame_vbox = gtk.VBox(False, 5)
    frame.add(frame_vbox)
    
    # Add a checkbox for expanding the mask
    expand_check = gtk.CheckButton("Expand mask slightly (helps with edges)")
    expand_check.set_active(True)  # Default to True
    frame_vbox.pack_start(expand_check, False, False, 5)
    expand_check.show()
    
    # Add a checkbox for GPU usage
    use_gpu_check = gtk.CheckButton("Use GPU if available")
    use_gpu_check.set_active(True)  # Default to using GPU
    vbox.pack_start(use_gpu_check, False, False, 10)
    use_gpu_check.show()
    
    # Add a checkbox for creating a new layer with the result
    new_layer_check = gtk.CheckButton("Create new layer with result")
    new_layer_check.set_active(True)  # Default to True
    vbox.pack_start(new_layer_check, False, False, 5)
    new_layer_check.show()
    
    # Show all widgets in the frame
    frame.show_all()
    
    # Add buttons for OK and Cancel
    dialog.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
    dialog.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
    
    # Show the dialog
    dialog.show_all()
    
    # Run the dialog and get the response
    response = dialog.run()
    
    if response == gtk.RESPONSE_OK:
        # Get the values
        expand_mask = expand_check.get_active()
        use_gpu = use_gpu_check.get_active()
        new_layer = new_layer_check.get_active()
        
        # Destroy the dialog
        dialog.destroy()
        
        # Return the parameters
        return {
            "expand_mask": expand_mask,
            "use_gpu": use_gpu,
            "new_layer": new_layer
        }
    else:
        # Destroy the dialog
        dialog.destroy()
        return None
