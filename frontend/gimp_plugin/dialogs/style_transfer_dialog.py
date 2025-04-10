"""
Style Transfer Dialog for GIMP.

This module provides a dialog for configuring style transfer options.
"""
from gimpfu import *
import os
import random

# Import our client module
from ..client.mcp_client import send_request
from ..utils.image_utils import get_layer_as_base64, load_image_from_file

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
    
    # Fetch available style options from the server
    classic_styles = []
    diffusion_models = []
    try:
        response = send_request(server_url, "get_all_style_options", {})
        if response and "classic_styles" in response and "diffusion_models" in response:
            classic_styles = response["classic_styles"]
            diffusion_models = response["diffusion_models"]
        else:
            pdb.gimp_message("Failed to fetch style options from the server. Using default options.")
            # Provide some default styles in case server request fails
            classic_styles = [
                {"id": "mosaic", "name": "Mosaic"},
                {"id": "candy", "name": "Candy"},
                {"id": "rain_princess", "name": "Rain Princess"},
                {"id": "udnie", "name": "Udnie"},
                {"id": "la_muse", "name": "La Muse"},
                {"id": "feathers", "name": "Feathers"},
                {"id": "the_scream", "name": "The Scream"}
            ]
            diffusion_models = [
                {"id": "sd1.5", "name": "Stable Diffusion 1.5", "description": "Balanced quality and speed"},
                {"id": "sd2.1", "name": "Stable Diffusion 2.1", "description": "Higher quality, slower inference"}
            ]
    except Exception as e:
        pdb.gimp_message(f"Error fetching style options: {str(e)}. Using default options.")
        # Provide some default styles in case server request fails
        classic_styles = [
            {"id": "mosaic", "name": "Mosaic"},
            {"id": "candy", "name": "Candy"},
            {"id": "rain_princess", "name": "Rain Princess"},
            {"id": "udnie", "name": "Udnie"},
            {"id": "la_muse", "name": "La Muse"},
            {"id": "feathers", "name": "Feathers"},
            {"id": "the_scream", "name": "The Scream"}
        ]
        diffusion_models = [
            {"id": "sd1.5", "name": "Stable Diffusion 1.5", "description": "Balanced quality and speed"},
            {"id": "sd2.1", "name": "Stable Diffusion 2.1", "description": "Higher quality, slower inference"}
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
    
    # Add notebook for tabs
    notebook = gtk.Notebook()
    notebook.set_tab_pos(gtk.POS_TOP)
    vbox.pack_start(notebook, True, True, 0)
    
    # Tab 1: Classic Style Transfer
    classic_tab = gtk.VBox(False, 5)
    classic_label = gtk.Label("Classic")
    notebook.append_page(classic_tab, classic_label)
    
    # Classic style selection dropdown
    classic_style_frame = gtk.Frame("Style")
    classic_tab.pack_start(classic_style_frame, False, False, 5)
    classic_style_box = gtk.VBox(False, 5)
    classic_style_frame.add(classic_style_box)
    
    classic_style_combo = gtk.combo_box_new_text()
    for style in classic_styles:
        classic_style_combo.append_text(style["name"])
    # Select first style by default
    classic_style_combo.set_active(0)
    classic_style_box.pack_start(classic_style_combo, False, False, 5)
    classic_style_frame.show_all()
    
    # Classic strength slider
    classic_strength_frame = gtk.Frame("Style Strength")
    classic_tab.pack_start(classic_strength_frame, False, False, 5)
    classic_strength_box = gtk.VBox(False, 5)
    classic_strength_frame.add(classic_strength_box)
    
    # Create an adjustment for the scale (initial value, min, max, step, page, page_size)
    classic_adjustment = gtk.Adjustment(1.0, 0.1, 1.0, 0.1, 0.2, 0)
    
    # Create a horizontal scale with the adjustment
    classic_scale = gtk.HScale(classic_adjustment)
    classic_scale.set_value_pos(gtk.POS_RIGHT)
    classic_scale.set_digits(1)
    classic_strength_box.pack_start(classic_scale, False, False, 5)
    classic_strength_frame.show_all()
    
    # Tab 2: Diffusion Style Transfer
    diffusion_tab = gtk.VBox(False, 5)
    diffusion_label = gtk.Label("Diffusion")
    notebook.append_page(diffusion_tab, diffusion_label)
    
    # Diffusion model selection
    diffusion_model_frame = gtk.Frame("Diffusion Model")
    diffusion_tab.pack_start(diffusion_model_frame, False, False, 5)
    diffusion_model_box = gtk.VBox(False, 5)
    diffusion_model_frame.add(diffusion_model_box)
    
    diffusion_model_combo = gtk.combo_box_new_text()
    for model in diffusion_models:
        diffusion_model_combo.append_text(f"{model['name']} - {model['description']}")
    # Select first model by default
    diffusion_model_combo.set_active(0)
    diffusion_model_box.pack_start(diffusion_model_combo, False, False, 5)
    diffusion_model_frame.show_all()
    
    # Style input method selection (text or image)
    style_input_frame = gtk.Frame("Style Input Method")
    diffusion_tab.pack_start(style_input_frame, False, False, 5)
    style_input_box = gtk.VBox(False, 5)
    style_input_frame.add(style_input_box)
    
    # Radio buttons for style input method
    style_text_radio = gtk.RadioButton(None, "Text prompt")
    style_input_box.pack_start(style_text_radio, False, False, 2)
    style_image_radio = gtk.RadioButton(style_text_radio, "Reference image")
    style_input_box.pack_start(style_image_radio, False, False, 2)
    
    # Text prompt input
    prompt_frame = gtk.Frame("Style Text Prompt")
    diffusion_tab.pack_start(prompt_frame, False, False, 5)
    prompt_box = gtk.VBox(False, 5)
    prompt_frame.add(prompt_box)
    
    prompt_entry = gtk.Entry()
    prompt_entry.set_text("Oil painting in the style of Van Gogh with vibrant colors and swirling patterns")
    prompt_box.pack_start(prompt_entry, False, False, 5)
    prompt_frame.show_all()
    
    # Reference image selection
    ref_image_frame = gtk.Frame("Reference Style Image")
    diffusion_tab.pack_start(ref_image_frame, False, False, 5)
    ref_image_box = gtk.VBox(False, 5)
    ref_image_frame.add(ref_image_box)
    
    ref_image_path_label = gtk.Label("No file selected")
    ref_image_box.pack_start(ref_image_path_label, False, False, 2)
    
    ref_image_hbox = gtk.HBox(False, 5)
    ref_image_box.pack_start(ref_image_hbox, False, False, 5)
    
    ref_image_button = gtk.Button("Browse...")
    ref_image_hbox.pack_start(ref_image_button, False, False, 5)
    ref_image_frame.show_all()
    ref_image_frame.set_sensitive(False)  # Initially disabled
    
    # Reference image path storage
    ref_image_path = [None]  # Using a list to store a mutable reference
    
    # Function to handle file selection
    def on_ref_image_button_clicked(widget):
        file_chooser = gtk.FileChooserDialog(
            title="Select Style Reference Image",
            action=gtk.FILE_CHOOSER_ACTION_OPEN,
            buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK)
        )
        
        # Add filters for image files
        filter_images = gtk.FileFilter()
        filter_images.set_name("Image files")
        filter_images.add_pattern("*.png")
        filter_images.add_pattern("*.jpg")
        filter_images.add_pattern("*.jpeg")
        file_chooser.add_filter(filter_images)
        
        response = file_chooser.run()
        if response == gtk.RESPONSE_OK:
            selected_path = file_chooser.get_filename()
            ref_image_path[0] = selected_path
            ref_image_path_label.set_text(os.path.basename(selected_path))
        
        file_chooser.destroy()
    
    # Connect the button click event
    ref_image_button.connect("clicked", on_ref_image_button_clicked)
    
    # Show/hide reference image frame based on radio button selection
    def on_style_input_toggled(widget):
        if style_text_radio.get_active():
            prompt_frame.set_sensitive(True)
            ref_image_frame.set_sensitive(False)
        else:
            prompt_frame.set_sensitive(False)
            ref_image_frame.set_sensitive(True)
    
    # Connect the radio button toggle events
    style_text_radio.connect("toggled", on_style_input_toggled)
    style_image_radio.connect("toggled", on_style_input_toggled)
    
    # Diffusion parameters
    diffusion_params_frame = gtk.Frame("Diffusion Parameters")
    diffusion_tab.pack_start(diffusion_params_frame, False, False, 5)
    diffusion_params_box = gtk.VBox(False, 5)
    diffusion_params_frame.add(diffusion_params_box)
    
    # Strength slider (noise level)
    strength_label = gtk.Label("Strength (more = more stylized, less = more faithful to content)")
    diffusion_params_box.pack_start(strength_label, False, False, 2)
    
    # Create an adjustment for strength (initial value, min, max, step, page, page_size)
    strength_adjustment = gtk.Adjustment(0.75, 0.2, 0.95, 0.05, 0.1, 0)
    
    # Create a horizontal scale
    strength_scale = gtk.HScale(strength_adjustment)
    strength_scale.set_value_pos(gtk.POS_RIGHT)
    strength_scale.set_digits(2)
    diffusion_params_box.pack_start(strength_scale, False, False, 5)
    
    # Guidance scale slider
    guidance_label = gtk.Label("Style Guidance Scale (more = more accurate to style prompt)")
    diffusion_params_box.pack_start(guidance_label, False, False, 2)
    
    # Create an adjustment for guidance (initial value, min, max, step, page, page_size)
    guidance_adjustment = gtk.Adjustment(7.5, 1.0, 15.0, 0.5, 1.0, 0)
    
    # Create a horizontal scale
    guidance_scale = gtk.HScale(guidance_adjustment)
    guidance_scale.set_value_pos(gtk.POS_RIGHT)
    guidance_scale.set_digits(1)
    diffusion_params_box.pack_start(guidance_scale, False, False, 5)
    
    # Steps slider
    steps_label = gtk.Label("Steps (more = higher quality but slower)")
    diffusion_params_box.pack_start(steps_label, False, False, 2)
    
    # Create an adjustment for steps (initial value, min, max, step, page, page_size)
    steps_adjustment = gtk.Adjustment(30, 10, 50, 5, 10, 0)
    
    # Create a horizontal scale
    steps_scale = gtk.HScale(steps_adjustment)
    steps_scale.set_value_pos(gtk.POS_RIGHT)
    steps_scale.set_digits(0)
    diffusion_params_box.pack_start(steps_scale, False, False, 5)
    
    # Seed input
    seed_hbox = gtk.HBox(False, 5)
    diffusion_params_box.pack_start(seed_hbox, False, False, 5)
    
    seed_label = gtk.Label("Seed (for reproducibility, leave empty for random):")
    seed_hbox.pack_start(seed_label, False, False, 5)
    
    seed_entry = gtk.Entry()
    seed_hbox.pack_start(seed_entry, True, True, 5)
    
    random_seed_button = gtk.Button("Random")
    seed_hbox.pack_start(random_seed_button, False, False, 5)
    
    # Function to generate a random seed
    def on_random_seed_button_clicked(widget):
        random_seed = random.randint(1, 2147483647)
        seed_entry.set_text(str(random_seed))
    
    # Connect the random seed button click event
    random_seed_button.connect("clicked", on_random_seed_button_clicked)
    
    diffusion_params_frame.show_all()
    
    # Common options (for both tabs)
    common_frame = gtk.Frame("Common Options")
    vbox.pack_start(common_frame, False, False, 5)
    common_box = gtk.VBox(False, 5)
    common_frame.add(common_box)
    
    # Add a checkbox for creating a new layer with the result
    new_layer_check = gtk.CheckButton("Create new layer with result")
    new_layer_check.set_active(True)  # Default to True
    common_box.pack_start(new_layer_check, False, False, 5)
    
    # Add a checkbox for GPU usage
    use_gpu_check = gtk.CheckButton("Use GPU if available")
    use_gpu_check.set_active(True)  # Default to using GPU
    common_box.pack_start(use_gpu_check, False, False, 5)
    
    # Add checkbox for half precision (only relevant for diffusion, but can be in common section)
    half_precision_check = gtk.CheckButton("Use half precision (faster but slightly lower quality)")
    half_precision_check.set_active(True)  # Default to True
    common_box.pack_start(half_precision_check, False, False, 5)
    
    common_frame.show_all()
    
    # Add buttons for OK and Cancel
    dialog.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
    dialog.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
    
    # Show the dialog
    dialog.show_all()
    
    # Run the dialog and get the response
    response = dialog.run()
    
    if response == gtk.RESPONSE_OK:
        # Get the common values
        new_layer = new_layer_check.get_active()
        use_gpu = use_gpu_check.get_active()
        use_half_precision = half_precision_check.get_active()
        
        # Get the method based on active tab
        current_page = notebook.get_current_page()
        
        if current_page == 0:  # Classic tab
            # Get classic style transfer parameters
            style_index = classic_style_combo.get_active()
            if style_index >= 0 and style_index < len(classic_styles):
                style_id = classic_styles[style_index]["id"]
            else:
                style_id = "mosaic"  # Default style
            
            classic_strength = classic_adjustment.get_value()
            
            # Destroy the dialog
            dialog.destroy()
            
            # Return the parameters for classic style transfer
            return {
                "method": "classic",
                "style_name": style_id,
                "strength": classic_strength,
                "new_layer": new_layer,
                "use_gpu": use_gpu
            }
        else:  # Diffusion tab
            # Get diffusion style transfer parameters
            model_index = diffusion_model_combo.get_active()
            if model_index >= 0 and model_index < len(diffusion_models):
                model_id = diffusion_models[model_index]["id"]
            else:
                model_id = "sd1.5"  # Default model
            
            # Get style input method
            style_type = "text" if style_text_radio.get_active() else "image"
            
            # Get text prompt if applicable
            style_prompt = prompt_entry.get_text()
            
            # Get reference image if applicable
            style_image_data = None
            if style_type == "image" and ref_image_path[0]:
                try:
                    style_image_data = load_image_from_file(ref_image_path[0])
                except Exception as e:
                    pdb.gimp_message(f"Error loading reference image: {str(e)}")
                    # Fall back to text method if image fails
                    style_type = "text"
            
            # Get diffusion parameters
            strength = strength_adjustment.get_value()
            guidance_scale = guidance_adjustment.get_value()
            num_inference_steps = int(steps_adjustment.get_value())
            
            # Get seed (if provided)
            seed = None
            seed_text = seed_entry.get_text().strip()
            if seed_text:
                try:
                    seed = int(seed_text)
                except ValueError:
                    pdb.gimp_message("Invalid seed value. Using random seed.")
            
            # Destroy the dialog
            dialog.destroy()
            
            # Return the parameters for diffusion style transfer
            result = {
                "method": "diffusion",
                "model_id": model_id,
                "style_type": style_type,
                "style_prompt": style_prompt,
                "strength": strength,
                "guidance_scale": guidance_scale,
                "num_inference_steps": num_inference_steps,
                "seed": seed,
                "new_layer": new_layer,
                "use_gpu": use_gpu,
                "use_half_precision": use_half_precision
            }
            
            # Only include style_image_data if it exists
            if style_image_data:
                result["style_image_data"] = style_image_data
                
            return result
    else:
        # Destroy the dialog
        dialog.destroy()
        return None
