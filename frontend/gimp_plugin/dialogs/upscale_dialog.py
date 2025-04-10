"""
Image Upscaling Dialog for GIMP.

This module provides a dialog for configuring image upscaling options.
"""
from gimpfu import *

def upscale_dialog():
    """
    Show a dialog for image upscaling options.
    
    Returns:
        dict: Parameters for the upscaling operation, or None if canceled.
    """
    # Create dialog
    dialog = gimp.Dialog("AI Image Upscaling", "upscale-dialog",
                       None, 0, None, None)
    
    # Create a vertical box for the dialog content
    vbox = dialog.vbox
    
    # Add help text
    label = gtk.Label("Upscale your image to a higher resolution with AI.")
    vbox.pack_start(label, False, False, 5)
    label.show()
    
    # Add information warning about high resolution images
    warning_label = gtk.Label("Note: Upscaling large images may require significant memory and processing time.")
    warning_label.set_justify(gtk.JUSTIFY_CENTER)
    vbox.pack_start(warning_label, False, False, 10)
    warning_label.show()
    
    # Add scale factor selection
    scale_factor_frame = gtk.Frame("Scale Factor")
    vbox.pack_start(scale_factor_frame, False, False, 5)
    scale_factor_box = gtk.VBox(False, 5)
    scale_factor_frame.add(scale_factor_box)
    
    # Create a radio button for each scale factor
    scale_2x_radio = gtk.RadioButton(None, "2x (Recommended for large images)")
    scale_factor_box.pack_start(scale_2x_radio, False, False, 0)
    
    scale_4x_radio = gtk.RadioButton(scale_2x_radio, "4x (Medium quality/performance)")
    scale_factor_box.pack_start(scale_4x_radio, False, False, 0)
    
    scale_8x_radio = gtk.RadioButton(scale_2x_radio, "8x (May produce artifacts)")
    scale_factor_box.pack_start(scale_8x_radio, False, False, 0)
    
    # Select 2x by default
    scale_2x_radio.set_active(True)
    
    scale_factor_frame.show_all()
    
    # Add denoise level slider
    denoise_frame = gtk.Frame("Denoise Level")
    vbox.pack_start(denoise_frame, False, False, 5)
    denoise_box = gtk.VBox(False, 5)
    denoise_frame.add(denoise_box)
    
    # Create an adjustment for the scale (initial value, min, max, step, page, page_size)
    denoise_adjustment = gtk.Adjustment(0.0, 0.0, 1.0, 0.1, 0.2, 0)
    
    # Create a horizontal scale with the adjustment
    denoise_scale = gtk.HScale(denoise_adjustment)
    denoise_scale.set_value_pos(gtk.POS_RIGHT)
    denoise_scale.set_digits(1)
    denoise_scale.set_size_request(300, -1)  # Set width
    denoise_box.pack_start(denoise_scale, False, False, 5)
    
    # Add labels for the scale
    denoise_labels_box = gtk.HBox(True, 0)
    denoise_box.pack_start(denoise_labels_box, False, False, 0)
    
    off_label = gtk.Label("Off")
    off_label.set_alignment(0, 0.5)
    denoise_labels_box.pack_start(off_label, True, True, 0)
    
    strong_label = gtk.Label("Strong")
    strong_label.set_alignment(1, 0.5)
    denoise_labels_box.pack_start(strong_label, True, True, 0)
    
    denoise_frame.show_all()
    
    # Add sharpen checkbox
    sharpen_check = gtk.CheckButton("Apply sharpening after upscaling")
    sharpen_check.set_active(False)  # Default to False
    vbox.pack_start(sharpen_check, False, False, 5)
    sharpen_check.show()
    
    # Add a checkbox for creating a new image with the result
    new_image_check = gtk.CheckButton("Create new image with result (recommended)")
    new_image_check.set_active(True)  # Default to True
    vbox.pack_start(new_image_check, False, False, 5)
    new_image_check.show()
    
    # Add a checkbox for GPU usage
    use_gpu_check = gtk.CheckButton("Use GPU if available (faster)")
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
        # Get the scale factor
        if scale_2x_radio.get_active():
            scale_factor = 2
        elif scale_4x_radio.get_active():
            scale_factor = 4
        elif scale_8x_radio.get_active():
            scale_factor = 8
        else:
            scale_factor = 2  # Default
        
        # Get other values
        denoise_level = denoise_adjustment.get_value()
        sharpen = sharpen_check.get_active()
        new_image = new_image_check.get_active()
        use_gpu = use_gpu_check.get_active()
        
        # Destroy the dialog
        dialog.destroy()
        
        # Return the parameters
        return {
            "scale_factor": scale_factor,
            "denoise_level": denoise_level,
            "sharpen": sharpen,
            "new_image": new_image,
            "use_gpu": use_gpu
        }
    else:
        # Destroy the dialog
        dialog.destroy()
        return None
