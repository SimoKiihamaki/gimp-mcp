"""
Background Removal Dialog for GIMP.

This module provides a dialog for configuring background removal options.
"""
from gimpfu import *

def background_removal_dialog():
    """
    Show a dialog for background removal options.
    
    Returns:
        dict: Parameters for the background removal operation, or None if canceled.
    """
    # Create dialog
    dialog = gimp.Dialog("Background Removal", "background-removal-dialog",
                       None, 0, None, None)
    
    # Create a vertical box for the dialog content
    vbox = dialog.vbox
    
    # Add a horizontal scale for threshold
    label = gtk.Label("Threshold (lower means more aggressive removal):")
    vbox.pack_start(label, False, False, 0)
    label.show()
    
    # Create an adjustment for the scale (initial value, min, max, step, page, page_size)
    adjustment = gtk.Adjustment(0.5, 0.1, 0.9, 0.05, 0.1, 0)
    
    # Create a horizontal scale with the adjustment
    scale = gtk.HScale(adjustment)
    scale.set_value_pos(gtk.POS_RIGHT)
    scale.set_digits(2)
    vbox.pack_start(scale, False, False, 0)
    scale.show()
    
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
        threshold = adjustment.get_value()
        use_gpu = use_gpu_check.get_active()
        
        # Destroy the dialog
        dialog.destroy()
        
        # Return the parameters
        return {
            "threshold": threshold,
            "use_gpu": use_gpu
        }
    else:
        # Destroy the dialog
        dialog.destroy()
        return None
