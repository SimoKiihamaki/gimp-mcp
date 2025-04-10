#!/usr/bin/env python

"""
GIMP AI Integration Plugin - Main Entry Point

This plugin adds AI-powered image editing capabilities to GIMP through
the "Filters > AI Tools" menu.
"""

import os
import sys
import base64
from gimpfu import *

# Add the plugin directory to the Python path to find our modules
plugin_dir = os.path.dirname(os.path.abspath(__file__))
if plugin_dir not in sys.path:
    sys.path.append(plugin_dir)

# Import our modules
from client.mcp_client import send_request, monitor_progress
from dialogs.background_removal_dialog import background_removal_dialog
from dialogs.inpainting_dialog import inpainting_dialog
from dialogs.style_transfer_dialog import style_transfer_dialog
from dialogs.upscale_dialog import upscale_dialog
from dialogs.feedback_dialog import feedback_dialog, submit_feedback
from dialogs.ai_interaction_dialog import ai_interaction_dialog
from dialogs.analysis_results_dialog import show_analysis_results
from utils.image_state import capture_current_state, serialize_image_state

# Global constants
PLUGIN_VERSION = "0.1.0"
DEFAULT_SERVER_URL = "http://localhost:8000/jsonrpc"

def hello_world(image, drawable):
    """
    Simple "Hello World" test function to verify the plugin and server connection.
    
    Args:
        image: The current GIMP image
        drawable: The current drawable (layer)
    """
    # Display a message to confirm the plugin is loaded
    pdb.gimp_message("Hello from GIMP AI Integration Plugin!")
    
    try:
        # Get the server URL from an environment variable or use the default
        server_url = os.environ.get("MCP_SERVER_URL", DEFAULT_SERVER_URL)
        
        # Send a test request to the server
        response = send_request(server_url, "hello_world", {"name": "GIMP"})
        
        # Display the response
        if response and "message" in response:
            pdb.gimp_message(response["message"])
        else:
            pdb.gimp_message("Received an unexpected response from the server")
    except Exception as e:
        pdb.gimp_message(f"Error connecting to MCP server: {str(e)}")

def background_removal(image, drawable):
    """
    Remove the background from the current layer.
    
    Args:
        image: The current GIMP image
        drawable: The current drawable (layer)
    """
    # Get the server URL
    server_url = os.environ.get("MCP_SERVER_URL", DEFAULT_SERVER_URL)
    
    # Show a dialog to get parameters
    params = background_removal_dialog()
    if not params:
        return  # User canceled
    
    # Start the progress bar
    gimp.progress_init("Removing background...")
    
    try:
        # Get the image data
        temp_file = os.path.join(gimp.temporary_directory(), "temp_image.png")
        pdb.gimp_file_save(image, drawable, temp_file, temp_file)
        
        # Read the image file and convert to base64
        with open(temp_file, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")
        
        # Clean up the temporary file
        os.remove(temp_file)
        
        # Update progress
        gimp.progress_update(0.1)
        
        # Display message that we're processing
        pdb.gimp_message("Processing background removal, this may take a moment...")
        
        # Create the request parameters
        request_params = {
            "image_data": image_data,
            "threshold": params["threshold"],
            "use_gpu": params["use_gpu"]
        }
        
        # Create a progress update function
        def update_progress(progress_data):
            if "progress" in progress_data:
                progress = progress_data["progress"]
                status = progress_data.get("status", "")
                
                # Update the GIMP progress bar
                gimp.progress_update(progress)
                
                # If there's a status message, display it
                if status and status.startswith("error"):
                    pdb.gimp_message(f"Error: {status}")
        
        # Send the request
        response = send_request(server_url, "ai_background_removal", request_params)
        
        if response and "image_data" in response and "task_id" in response:
            # Start monitoring progress if a task_id is provided
            task_id = response["task_id"]
            monitor_progress(server_url, task_id, update_progress)
            
            # Create a new layer for the result
            new_layer = gimp.Layer(image, "Background Removed", drawable.width, 
                                  drawable.height, RGBA_IMAGE, 100, NORMAL_MODE)
            
            # Add the new layer to the image
            image.add_layer(new_layer, 0)  # Add at the top
            
            # Decode the base64 image
            result_data = base64.b64decode(response["image_data"])
            
            # Save to a temporary file
            temp_result_file = os.path.join(gimp.temporary_directory(), "temp_result.png")
            with open(temp_result_file, "wb") as f:
                f.write(result_data)
            
            # Load the temporary file into the new layer
            new_drawable = pdb.gimp_file_load_layer(image, temp_result_file)
            image.add_layer(new_drawable, 0)  # Add at the top
            
            # Clean up
            os.remove(temp_result_file)
            
            # Update the display
            gimp.displays_flush()
            
            # Display success message
            pdb.gimp_message("Background removal completed successfully")
        else:
            pdb.gimp_message("Background removal failed. No valid response from server.")
    
    except Exception as e:
        pdb.gimp_message(f"Error in background removal: {str(e)}")
    
    finally:
        # End the progress bar
        gimp.progress_end()

def upscale_image(image, drawable):
    """
    Upscale an image to a higher resolution using AI.
    
    Args:
        image: The current GIMP image
        drawable: The current drawable (layer)
    """
    # Get the server URL
    server_url = os.environ.get("MCP_SERVER_URL", DEFAULT_SERVER_URL)
    
    # Show a dialog to get parameters
    params = upscale_dialog()
    if not params:
        return  # User canceled
    
    # Start the progress bar
    gimp.progress_init("Upscaling image...")
    
    try:
        # Get the image data
        temp_file = os.path.join(gimp.temporary_directory(), "temp_upscale_image.png")
        pdb.gimp_file_save(image, drawable, temp_file, temp_file)
        
        # Read the image file and convert to base64
        with open(temp_file, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")
        
        # Clean up the temporary file
        os.remove(temp_file)
        
        # Update progress
        gimp.progress_update(0.1)
        
        # Display message that we're processing
        factor = params["scale_factor"]
        pdb.gimp_message(f"Upscaling image by {factor}x, this may take a moment...")
        
        # Create the request parameters
        request_params = {
            "image_data": image_data,
            "scale_factor": params["scale_factor"],
            "denoise_level": params["denoise_level"],
            "sharpen": params["sharpen"],
            "use_gpu": params["use_gpu"]
        }
        
        # Create a progress update function
        def update_progress(progress_data):
            if "progress" in progress_data:
                progress = progress_data["progress"]
                status = progress_data.get("status", "")
                
                # Update the GIMP progress bar
                gimp.progress_update(progress)
                
                # If there's a status message, display it
                if status and status.startswith("error"):
                    pdb.gimp_message(f"Error: {status}")
        
        # Send the request
        response = send_request(server_url, "ai_upscale", request_params)
        
        if response and "image_data" in response and "task_id" in response:
            # Start monitoring progress if a task_id is provided
            task_id = response["task_id"]
            monitor_progress(server_url, task_id, update_progress)
            
            # Decode the base64 image
            result_data = base64.b64decode(response["image_data"])
            
            # Save to a temporary file
            temp_result_file = os.path.join(gimp.temporary_directory(), "temp_upscale_result.png")
            with open(temp_result_file, "wb") as f:
                f.write(result_data)
            
            # Load the temporary file
            if params["new_image"]:
                # Create a new image
                orig_width, orig_height = drawable.width, drawable.height
                new_width = orig_width * params["scale_factor"]
                new_height = orig_height * params["scale_factor"]
                
                # Load the upscaled image
                result_image = pdb.gimp_file_load(temp_result_file, temp_result_file)
                result_layer = pdb.gimp_image_get_active_layer(result_image)
                
                # Set appropriate name
                new_name = f"{image.name}_upscaled_{params['scale_factor']}x"
                result_image.filename = new_name
                
                # Display the new image
                pdb.gimp_display_new(result_image)
            else:
                # Resize the current image
                orig_width, orig_height = drawable.width, drawable.height
                new_width = orig_width * params["scale_factor"]
                new_height = orig_height * params["scale_factor"]
                
                # Resize the image
                pdb.gimp_image_resize(image, new_width, new_height, 0, 0)
                
                # Create a new layer for the upscaled result
                new_layer = gimp.Layer(image, "Upscaled", new_width, new_height, 
                                      drawable.type, 100, NORMAL_MODE)
                image.add_layer(new_layer, 0)  # Add at the top
                
                # Load the upscaled image
                result_image = pdb.gimp_file_load(temp_result_file, temp_result_file)
                result_layer = pdb.gimp_image_get_active_layer(result_image)
                
                # Copy to the new layer
                pdb.gimp_edit_copy(result_layer)
                floating_sel = pdb.gimp_edit_paste(new_layer, True)
                pdb.gimp_floating_sel_anchor(floating_sel)
                
                # Clean up the temporary image
                gimp.delete(result_image)
            
            # Clean up the temporary file
            os.remove(temp_result_file)
            
            # Update the display
            gimp.displays_flush()
            
            # Display success message
            pdb.gimp_message(f"Image successfully upscaled by {params['scale_factor']}x")
        else:
            pdb.gimp_message("Upscaling failed. No valid response from server.")
    
    except Exception as e:
        pdb.gimp_message(f"Error in upscaling: {str(e)}")
    
    finally:
        # End the progress bar
        gimp.progress_end()

# Register the plugins with GIMP
def inpainting(image, drawable):
    """
    Inpaint the selected region of an image.
    
    Args:
        image: The current GIMP image
        drawable: The current drawable (layer)
    """
    # Check if there's an active selection
    has_selection, x1, y1, x2, y2 = pdb.gimp_selection_bounds(image)
    if not has_selection:
        pdb.gimp_message("Please make a selection first. The selected area will be inpainted.")
        return
    
    # Get the server URL
    server_url = os.environ.get("MCP_SERVER_URL", DEFAULT_SERVER_URL)
    
    # Show a dialog to get parameters
    params = inpainting_dialog()
    if not params:
        return  # User canceled
    
    # Start the progress bar
    gimp.progress_init("Inpainting selected area...")
    
    try:
        # Create a temporary image to store the selection as a mask
        temp_mask = gimp.Image(drawable.width, drawable.height, GRAY)
        mask_layer = gimp.Layer(temp_mask, "Mask", drawable.width, drawable.height, GRAY_IMAGE, 100, NORMAL_MODE)
        temp_mask.add_layer(mask_layer, 0)
        
        # Fill the selection with white in the mask
        pdb.gimp_edit_fill(mask_layer, WHITE_FILL)
        
        # If expand_mask is true, grow the selection slightly
        if params["expand_mask"]:
            # Save the selection to a channel
            channel = pdb.gimp_selection_save(temp_mask)
            # Grow the selection by 2-5 pixels (adjust as needed)
            pdb.gimp_selection_grow(temp_mask, 3)
            # Fill the expanded selection
            pdb.gimp_edit_fill(mask_layer, WHITE_FILL)
        
        # Save the image and mask to temporary files
        temp_image_file = os.path.join(gimp.temporary_directory(), "temp_inpaint_image.png")
        temp_mask_file = os.path.join(gimp.temporary_directory(), "temp_inpaint_mask.png")
        
        pdb.gimp_file_save(image, drawable, temp_image_file, temp_image_file)
        pdb.gimp_file_save(temp_mask, mask_layer, temp_mask_file, temp_mask_file)
        
        # Read the files and convert to base64
        with open(temp_image_file, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")
        
        with open(temp_mask_file, "rb") as f:
            mask_data = base64.b64encode(f.read()).decode("utf-8")
        
        # Clean up the temporary files and image
        os.remove(temp_image_file)
        os.remove(temp_mask_file)
        gimp.delete(temp_mask)
        
        # Update progress
        gimp.progress_update(0.3)
        
        # Display message that we're processing
        pdb.gimp_message("Processing inpainting, this may take a moment...")
        
        # Send the request to the server
        request_params = {
            "image_data": image_data,
            "mask_data": mask_data,
            "use_gpu": params["use_gpu"]
        }
        
        # Create a progress update function
        def update_progress(progress_data):
            if "progress" in progress_data:
                progress = progress_data["progress"]
                status = progress_data.get("status", "")
                
                # Update the GIMP progress bar
                gimp.progress_update(progress)
                
                # If there's a status message, display it
                if status and status.startswith("error"):
                    pdb.gimp_message(f"Error: {status}")
        
        # Send the request
        response = send_request(server_url, "ai_inpainting", request_params)
        
        if response and "image_data" in response and "task_id" in response:
            # Start monitoring progress if a task_id is provided
            task_id = response["task_id"]
            monitor_progress(server_url, task_id, update_progress)
            
            # Create a new layer for the result if requested
            if params["new_layer"]:
                # Create a new layer
                new_layer = gimp.Layer(image, "Inpainted", drawable.width, 
                                      drawable.height, drawable.type, 100, NORMAL_MODE)
                
                # Add the new layer to the image
                image.add_layer(new_layer, 0)  # Add at the top
                
                # Make the new layer the active drawable
                target_drawable = new_layer
            else:
                # Use the current layer
                target_drawable = drawable
            
            # Decode the base64 image
            result_data = base64.b64decode(response["image_data"])
            
            # Save to a temporary file
            temp_result_file = os.path.join(gimp.temporary_directory(), "temp_inpaint_result.png")
            with open(temp_result_file, "wb") as f:
                f.write(result_data)
            
            # Load the temporary file
            result_image = pdb.gimp_file_load(temp_result_file, temp_result_file)
            result_layer = pdb.gimp_image_get_active_layer(result_image)
            
            # Copy the inpainted region to the target layer
            # We need to make the selection again to ensure we're copying to the right place
            pdb.gimp_selection_load(image.active_channel) if 'channel' in locals() else None
            pdb.gimp_edit_copy(result_layer)
            floating_sel = pdb.gimp_edit_paste(target_drawable, True)
            pdb.gimp_floating_sel_anchor(floating_sel)
            
            # Clean up
            os.remove(temp_result_file)
            gimp.delete(result_image)
            
            # Clear the selection
            pdb.gimp_selection_none(image)
            
            # Update the display
            gimp.displays_flush()
            
            # Display success message
            pdb.gimp_message("Inpainting completed successfully")
        else:
            pdb.gimp_message("Inpainting failed. No valid response from server.")
    
    except Exception as e:
        pdb.gimp_message(f"Error in inpainting: {str(e)}")
    
    finally:
        # End the progress bar
        gimp.progress_end()

def style_transfer(image, drawable):
    """
    Apply artistic style transfer to an image.
    
    Args:
        image: The current GIMP image
        drawable: The current drawable (layer)
    """
    # Get the server URL
    server_url = os.environ.get("MCP_SERVER_URL", DEFAULT_SERVER_URL)
    
    # Show a dialog to get parameters
    params = style_transfer_dialog(server_url)
    if not params:
        return  # User canceled
    
    # Determine if we're using classic or diffusion style transfer
    style_method = params.get("method", "classic")
    
    # Start the progress bar
    gimp.progress_init("Applying style transfer...")
    
    try:
        # Get the image data
        temp_file = os.path.join(gimp.temporary_directory(), "temp_style_image.png")
        pdb.gimp_file_save(image, drawable, temp_file, temp_file)
        
        # Read the image file and convert to base64
        with open(temp_file, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")
        
        # Clean up the temporary file
        os.remove(temp_file)
        
        # Update progress
        gimp.progress_update(0.1)
        
        # Create request parameters based on the method
        request_params = {
            "image_data": image_data,
            "method": style_method,
            "use_gpu": params["use_gpu"]
        }
        
        # Add method-specific parameters
        if style_method == "classic":
            # Display message that we're processing
            pdb.gimp_message(f"Applying classic style transfer with {params['style_name']} style, this may take a moment...")
            
            # Add classic style transfer parameters
            request_params.update({
                "style_name": params["style_name"],
                "strength": params["strength"]
            })
        elif style_method == "diffusion":
            # Get model description for the message
            model_id = params.get("model_id", "sd1.5")
            style_type = params.get("style_type", "text")
            
            if style_type == "text":
                # Display message for text-guided style transfer
                prompt_preview = params.get("style_prompt", "")[:30] + "..." if len(params.get("style_prompt", "")) > 30 else params.get("style_prompt", "")
                pdb.gimp_message(f"Applying diffusion style transfer with text prompt '{prompt_preview}', this may take a moment...")
                
                # Add diffusion text-guided parameters
                request_params.update({
                    "model_id": model_id,
                    "style_type": "text",
                    "style_prompt": params.get("style_prompt", "Oil painting in the style of Van Gogh"),
                    "strength": params.get("strength", 0.75),
                    "guidance_scale": params.get("guidance_scale", 7.5),
                    "num_inference_steps": params.get("num_inference_steps", 30),
                    "seed": params.get("seed"),
                    "use_half_precision": params.get("use_half_precision", True)
                })
            elif style_type == "image":
                # Display message for image-guided style transfer
                pdb.gimp_message(f"Applying diffusion style transfer with reference image, this may take a moment...")
                
                # Add diffusion image-guided parameters
                request_params.update({
                    "model_id": model_id,
                    "style_type": "image",
                    "style_image_data": params.get("style_image_data"),
                    "strength": params.get("strength", 0.75),
                    "guidance_scale": params.get("guidance_scale", 7.5),
                    "num_inference_steps": params.get("num_inference_steps", 30),
                    "seed": params.get("seed"),
                    "use_half_precision": params.get("use_half_precision", True)
                })
        
        # Create a progress update function
        def update_progress(progress_data):
            if "progress" in progress_data:
                progress = progress_data["progress"]
                status = progress_data.get("status", "")
                
                # Update the GIMP progress bar
                gimp.progress_update(progress)
                
                # If there's a status message, display it
                if status and status.startswith("error"):
                    pdb.gimp_message(f"Error: {status}")
        
        # Send the request
        response = send_request(server_url, "ai_style_transfer", request_params)
        
        if response and "image_data" in response and "task_id" in response:
            # Start monitoring progress if a task_id is provided
            task_id = response["task_id"]
            monitor_progress(server_url, task_id, update_progress)
            
            # Create a new layer for the result if requested
            if params["new_layer"]:
                # Create a new layer with appropriate name based on method
                if style_method == "classic":
                    new_layer_name = f"Style: {params['style_name'].replace('_', ' ').title()}"
                elif style_method == "diffusion" and params.get("style_type") == "text":
                    prompt_short = params.get("style_prompt", "")[:15] + "..." if len(params.get("style_prompt", "")) > 15 else params.get("style_prompt", "")
                    new_layer_name = f"Diffusion: {prompt_short}"
                else:
                    new_layer_name = f"Diffusion Style"
                
                new_layer = gimp.Layer(image, new_layer_name, drawable.width, 
                                      drawable.height, drawable.type, 100, NORMAL_MODE)
                
                # Add the new layer to the image
                image.add_layer(new_layer, 0)  # Add at the top
                
                # Make the new layer the active drawable
                target_drawable = new_layer
            else:
                # Use the current layer
                target_drawable = drawable
            
            # Decode the base64 image
            result_data = base64.b64decode(response["image_data"])
            
            # Save to a temporary file
            temp_result_file = os.path.join(gimp.temporary_directory(), "temp_style_result.png")
            with open(temp_result_file, "wb") as f:
                f.write(result_data)
            
            # Load the temporary file
            result_image = pdb.gimp_file_load(temp_result_file, temp_result_file)
            result_layer = pdb.gimp_image_get_active_layer(result_image)
            
            # Copy the result to the target layer
            pdb.gimp_edit_copy(result_layer)
            floating_sel = pdb.gimp_edit_paste(target_drawable, True)
            pdb.gimp_floating_sel_anchor(floating_sel)
            
            # Clean up
            os.remove(temp_result_file)
            gimp.delete(result_image)
            
            # Update the display
            gimp.displays_flush()
            
            # Display success message based on method
            if style_method == "classic":
                pdb.gimp_message("Classic style transfer completed successfully")
            else:
                pdb.gimp_message("Diffusion style transfer completed successfully")
        else:
            pdb.gimp_message("Style transfer failed. No valid response from server.")
    
    except Exception as e:
        pdb.gimp_message(f"Error in style transfer: {str(e)}")
    
    finally:
        # End the progress bar
        gimp.progress_end()

register(
    "python-fu-ai-hello-world",        # Procedure name
    "Test the AI Integration Plugin",   # Blurb
    "Tests the connection to the MCP server with a hello world message",  # Help
    "GIMP AI Integration Team",         # Author
    "GIMP AI Integration Team",         # Copyright
    "2025",                             # Date
    "<Image>/Filters/AI Tools/Hello World",  # Menu path
    "*",                                # Image type
    [],                                 # Parameters
    [],                                 # Return values
    hello_world                         # Function
)

register(
    "python-fu-ai-background-removal",  # Procedure name
    "Remove Background with AI",        # Blurb
    "Uses AI to remove the background from the current layer",  # Help
    "GIMP AI Integration Team",         # Author
    "GIMP AI Integration Team",         # Copyright
    "2025",                             # Date
    "<Image>/Filters/AI Tools/Remove Background",  # Menu path
    "RGB*, RGBA*",                      # Image type
    [],                                 # Parameters
    [],                                 # Return values
    background_removal                  # Function
)

register(
    "python-fu-ai-inpainting",          # Procedure name
    "Inpaint with AI",                  # Blurb
    "Uses AI to inpaint the selected area of an image",  # Help
    "GIMP AI Integration Team",         # Author
    "GIMP AI Integration Team",         # Copyright
    "2025",                             # Date
    "<Image>/Filters/AI Tools/Inpainting",  # Menu path
    "RGB*, RGBA*",                      # Image type
    [],                                 # Parameters
    [],                                 # Return values
    inpainting                          # Function
)

register(
    "python-fu-ai-style-transfer",      # Procedure name
    "Apply Style Transfer with AI",     # Blurb
    "Uses AI to apply artistic styles to an image",  # Help
    "GIMP AI Integration Team",         # Author
    "GIMP AI Integration Team",         # Copyright
    "2025",                             # Date
    "<Image>/Filters/AI Tools/Style Transfer",  # Menu path
    "RGB*, RGBA*",                      # Image type
    [],                                 # Parameters
    [],                                 # Return values
    style_transfer                      # Function
)

register(
    "python-fu-ai-upscale",             # Procedure name
    "Upscale Image with AI",            # Blurb
    "Uses AI to upscale an image to a higher resolution",  # Help
    "GIMP AI Integration Team",         # Author
    "GIMP AI Integration Team",         # Copyright
    "2025",                             # Date
    "<Image>/Filters/AI Tools/Upscale Image",  # Menu path
    "RGB*, RGBA*",                      # Image type
    [],                                 # Parameters
    [],                                 # Return values
    upscale_image                       # Function
)

def send_user_feedback(image, drawable):
    """
    Send feedback about the GIMP AI Integration.
    
    Args:
        image: The current GIMP image (not used)
        drawable: The current drawable (not used)
    """
    # Show the feedback dialog
    feedback_data = feedback_dialog()
    
    if feedback_data:
        # Show a progress dialog
        progress_dialog = gimp.Dialog("Submitting Feedback", "feedback-progress-dialog",
                                     None, 0, None, None)
        progress_dialog.set_size_request(300, 100)
        
        vbox = progress_dialog.vbox
        label = gtk.Label("Submitting your feedback...\nPlease wait.")
        vbox.pack_start(label, True, True, 10)
        
        progress_bar = gtk.ProgressBar()
        progress_bar.set_text("Connecting to server...")
        progress_bar.set_fraction(0.5)
        vbox.pack_start(progress_bar, False, False, 10)
        
        progress_dialog.show_all()
        
        # Update UI while processing
        while gtk.events_pending():
            gtk.main_iteration()
        
        # Submit feedback in a separate thread to avoid blocking the UI
        def submit_thread():
            success = submit_feedback(feedback_data)
            
            # Update the progress dialog
            if success:
                progress_bar.set_text("Feedback submitted successfully!")
                progress_bar.set_fraction(1.0)
            else:
                progress_bar.set_text("Feedback saved locally.")
                progress_bar.set_fraction(1.0)
            
            # Add a close button
            progress_dialog.add_button(gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE)
            progress_dialog.show_all()
            
            # Update UI
            while gtk.events_pending():
                gtk.main_iteration()
        
        # Start the submission thread
        import threading
        thread = threading.Thread(target=submit_thread)
        thread.daemon = True
        thread.start()
        
        # Run the progress dialog
        progress_dialog.run()
        progress_dialog.destroy()
    
def ai_assistant(image, drawable):
    """
    Launch the AI Assistant dialog for interactive image editing assistance.
    
    Args:
        image: The current GIMP image
        drawable: The current drawable (layer)
    """
    # Get the server URL
    server_url = os.environ.get("MCP_SERVER_URL", DEFAULT_SERVER_URL)
    
    # Capture the current image state
    image_state = capture_current_state(image)
    serialized_state = serialize_image_state(image_state)
    
    # Show the AI interaction dialog
    ai_interaction_dialog(image, drawable, server_url, serialized_state)

def analyze_image(image, drawable):
    """
    Analyze the current image using AI.
    
    Args:
        image: The current GIMP image
        drawable: The current drawable (layer)
    """
    # Get the server URL
    server_url = os.environ.get("MCP_SERVER_URL", DEFAULT_SERVER_URL)
    
    # Start the progress bar
    gimp.progress_init("Analyzing image...")
    
    try:
        # Capture the current image state
        image_state = capture_current_state(image)
        serialized_state = serialize_image_state(image_state)
        
        # Send the analysis request
        response = send_request(server_url, "image_analysis", {
            "image_state": serialized_state,
            "analysis_type": "detailed"
        })
        
        if response and "analysis" in response:
            # Show results in a dialog
            show_analysis_results(image, response["analysis"])
        else:
            pdb.gimp_message("Image analysis failed. No valid response from server.")
    
    except Exception as e:
        pdb.gimp_message(f"Error in image analysis: {str(e)}")
    
    finally:
        # End the progress bar
        gimp.progress_end()

register(
    "python-fu-ai-send-feedback",       # Procedure name
    "Send Feedback",                    # Blurb
    "Submit feedback, bug reports, or feature requests for GIMP AI Integration",  # Help
    "GIMP AI Integration Team",         # Author
    "GIMP AI Integration Team",         # Copyright
    "2025",                             # Date
    "<Image>/Filters/AI Tools/Send Feedback",  # Menu path
    "*",                                # Image type (any)
    [],                                 # Parameters
    [],                                 # Return values
    send_user_feedback                  # Function
)

register(
    "python-fu-ai-assistant",           # Procedure name
    "AI Assistance for Image Editing",   # Blurb
    "Get interactive assistance from AI for image editing tasks",  # Help
    "GIMP AI Integration Team",         # Author
    "GIMP AI Integration Team",         # Copyright
    "2025",                             # Date
    "<Image>/Filters/AI Tools/AI Assistant",  # Menu path
    "*",                                # Image type
    [],                                 # Parameters
    [],                                 # Return values
    ai_assistant                        # Function
)

register(
    "python-fu-ai-analyze-image",       # Procedure name
    "Analyze Image with AI",            # Blurb
    "Uses AI to analyze the content of the current image",  # Help
    "GIMP AI Integration Team",         # Author
    "GIMP AI Integration Team",         # Copyright
    "2025",                             # Date
    "<Image>/Filters/AI Tools/Analyze Image",  # Menu path
    "*",                                # Image type
    [],                                 # Parameters
    [],                                 # Return values
    analyze_image                       # Function
)

# This is the main function that registers the plugin
main()
