"""
AI Interaction Dialog for GIMP.

This module provides a dialog for interacting with the AI assistant
for image editing guidance and suggestions.
"""
import os
import threading
import json
from typing import Dict, Any, Optional

from gimpfu import *

# Import our client module for MCP communication
from ..client.mcp_client import send_request
from ..utils.image_state import capture_current_state, serialize_image_state

def ai_interaction_dialog(image, drawable, server_url, image_state=None):
    """
    Show a dialog for interacting with the AI assistant.
    
    Args:
        image: The GIMP image object
        drawable: The current drawable
        server_url: URL of the MCP server
        image_state: Serialized image state (if already captured)
        
    Returns:
        None
    """
    # If image state is not provided, capture it
    if image_state is None:
        image_state = serialize_image_state(capture_current_state(image))
    
    # Create the dialog
    dialog = gimp.Dialog("AI Assistant", "ai-assistant-dialog",
                       None, 0, None, None)
    dialog.set_size_request(600, 400)
    
    # Create a vertical box for the dialog content
    vbox = dialog.vbox
    
    # Add a welcome message and instructions
    welcome_label = gtk.Label()
    welcome_label.set_markup("<b>Welcome to the GIMP AI Assistant</b>")
    vbox.pack_start(welcome_label, False, False, 5)
    welcome_label.show()
    
    instructions_label = gtk.Label("Ask me about your image or request editing suggestions.\n"
                                "I can help you with filters, color adjustments, composition, and more.")
    vbox.pack_start(instructions_label, False, False, 10)
    instructions_label.show()
    
    # Create a scrolled window for the conversation
    scrolled_window = gtk.ScrolledWindow()
    scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
    scrolled_window.set_size_request(-1, 200)  # Height set to 200 pixels
    vbox.pack_start(scrolled_window, True, True, 0)
    scrolled_window.show()
    
    # Text view for displaying conversation
    conversation_view = gtk.TextView()
    conversation_view.set_editable(False)
    conversation_view.set_wrap_mode(gtk.WRAP_WORD)
    conversation_buffer = conversation_view.get_buffer()
    conversation_buffer.set_text("AI Assistant: I'm analyzing your image... please wait...")
    scrolled_window.add(conversation_view)
    conversation_view.show()
    
    # Add a separator
    separator = gtk.HSeparator()
    vbox.pack_start(separator, False, False, 5)
    separator.show()
    
    # Create a horizontal box for the user input
    hbox_input = gtk.HBox(False, 5)
    vbox.pack_start(hbox_input, False, False, 5)
    hbox_input.show()
    
    # Text entry for user input
    user_input = gtk.Entry()
    user_input.set_size_request(400, -1)
    user_input.set_text("What would you like to know about my image?")
    hbox_input.pack_start(user_input, True, True, 5)
    user_input.show()
    
    # Send button
    send_button = gtk.Button("Send")
    hbox_input.pack_start(send_button, False, False, 5)
    send_button.show()
    
    # Progress bar
    progress_bar = gtk.ProgressBar()
    progress_bar.set_text("Ready")
    vbox.pack_start(progress_bar, False, False, 5)
    progress_bar.show()
    
    # Add horizontal box for action buttons
    hbox_actions = gtk.HBox(True, 5)
    vbox.pack_start(hbox_actions, False, False, 5)
    hbox_actions.show()
    
    # Action buttons
    analyze_button = gtk.Button("Analyze Image")
    apply_button = gtk.Button("Apply Suggestion")
    apply_button.set_sensitive(False)  # Disabled until a suggestion is made
    hbox_actions.pack_start(analyze_button, True, True, 5)
    hbox_actions.pack_start(apply_button, True, True, 5)
    analyze_button.show()
    apply_button.show()
    
    # Add Close button at the bottom
    close_button = gtk.Button("Close")
    vbox.pack_start(close_button, False, False, 10)
    close_button.show()
    
    # Variables to store the conversation context and current suggestion
    conversation_context = {
        "messages": [],
        "image_analyzed": False,
        "current_suggestion": None
    }
    
    # Function to append text to the conversation
    def append_to_conversation(sender, text):
        end_iter = conversation_buffer.get_end_iter()
        conversation_buffer.insert(end_iter, f"\n\n{sender}: {text}")
        # Scroll to the bottom
        mark = conversation_buffer.create_mark("end", conversation_buffer.get_end_iter(), False)
        conversation_view.scroll_to_mark(mark, 0.0, True, 0.0, 1.0)
    
    # Function to handle user input
    def on_send_clicked(widget):
        user_message = user_input.get_text()
        if not user_message.strip():
            return
        
        # Add user message to conversation
        append_to_conversation("You", user_message)
        conversation_context["messages"].append({"role": "user", "content": user_message})
        
        # Clear input field
        user_input.set_text("")
        
        # Disable send button and show progress
        send_button.set_sensitive(False)
        progress_bar.set_text("Processing your request...")
        progress_bar.set_fraction(0.3)
        
        # Process in a separate thread to avoid blocking the UI
        threading.Thread(target=process_user_message, args=(user_message,)).start()
    
    # Function to process the user message in a background thread
    def process_user_message(message):
        try:
            # Prepare the request
            request_params = {
                "message": message,
                "conversation_history": conversation_context["messages"],
                "image_state": image_state
            }
            
            # Only include analysis results if we have analyzed the image
            if conversation_context["image_analyzed"]:
                request_params["analysis_results"] = conversation_context.get("analysis_results", {})
            
            # Send the request to the AI assistant
            response = send_request(server_url, "ai_assistant", request_params)
            
            # Process the response
            if response and "message" in response:
                # Update the UI in the main thread
                gtk.gdk.threads_enter()
                
                ai_message = response["message"]
                append_to_conversation("AI Assistant", ai_message)
                conversation_context["messages"].append({"role": "assistant", "content": ai_message})
                
                # Check if there's a suggestion
                if "suggestion" in response:
                    suggestion = response["suggestion"]
                    conversation_context["current_suggestion"] = suggestion
                    apply_button.set_sensitive(True)
                
                # Update progress bar
                progress_bar.set_text("Ready")
                progress_bar.set_fraction(0.0)
                
                # Re-enable send button
                send_button.set_sensitive(True)
                
                gtk.gdk.threads_leave()
            else:
                # Handle error
                gtk.gdk.threads_enter()
                
                append_to_conversation("AI Assistant", "Sorry, I couldn't process your request. Please try again.")
                progress_bar.set_text("Error occurred")
                progress_bar.set_fraction(0.0)
                send_button.set_sensitive(True)
                
                gtk.gdk.threads_leave()
        except Exception as e:
            # Handle exceptions
            gtk.gdk.threads_enter()
            
            error_message = str(e)
            append_to_conversation("AI Assistant", f"An error occurred: {error_message}. Please try again.")
            progress_bar.set_text("Error occurred")
            progress_bar.set_fraction(0.0)
            send_button.set_sensitive(True)
            
            gtk.gdk.threads_leave()
    
    # Function to analyze the image
    def on_analyze_clicked(widget):
        # Show progress
        analyze_button.set_sensitive(False)
        progress_bar.set_text("Analyzing image...")
        progress_bar.set_fraction(0.3)
        
        # Process in a separate thread to avoid blocking the UI
        threading.Thread(target=analyze_image).start()
    
    # Function to analyze the image in a background thread
    def analyze_image():
        try:
            # Prepare the request
            request_params = {
                "image_state": image_state,
                "analysis_type": "detailed"
            }
            
            # Send the request to the server
            response = send_request(server_url, "image_analysis", request_params)
            
            # Process the response
            if response and "analysis" in response:
                # Update the UI in the main thread
                gtk.gdk.threads_enter()
                
                analysis_results = response["analysis"]
                conversation_context["analysis_results"] = analysis_results
                conversation_context["image_analyzed"] = True
                
                # Update the conversation with analysis summary
                analysis_summary = generate_analysis_summary(analysis_results)
                append_to_conversation("AI Assistant", f"I've analyzed your image. {analysis_summary}")
                
                # Update progress bar
                progress_bar.set_text("Analysis complete")
                progress_bar.set_fraction(1.0)
                
                # Re-enable analyze button
                analyze_button.set_sensitive(True)
                
                gtk.gdk.threads_leave()
            else:
                # Handle error
                gtk.gdk.threads_enter()
                
                append_to_conversation("AI Assistant", "Sorry, I couldn't analyze the image. Please try again.")
                progress_bar.set_text("Analysis failed")
                progress_bar.set_fraction(0.0)
                analyze_button.set_sensitive(True)
                
                gtk.gdk.threads_leave()
        except Exception as e:
            # Handle exceptions
            gtk.gdk.threads_enter()
            
            error_message = str(e)
            append_to_conversation("AI Assistant", f"An error occurred during analysis: {error_message}. Please try again.")
            progress_bar.set_text("Analysis failed")
            progress_bar.set_fraction(0.0)
            analyze_button.set_sensitive(True)
            
            gtk.gdk.threads_leave()
    
    # Function to generate a summary from analysis results
    def generate_analysis_summary(analysis_results):
        try:
            dimensions = analysis_results.get("dimensions", {})
            width = dimensions.get("width", 0)
            height = dimensions.get("height", 0)
            aspect_ratio = dimensions.get("aspect_ratio", 0)
            
            layer_count = analysis_results.get("layer_count", 0)
            has_selection = analysis_results.get("has_selection", False)
            
            color_analysis = analysis_results.get("color_analysis", {})
            brightness = color_analysis.get("brightness", 0)
            contrast = color_analysis.get("contrast", 0)
            is_grayscale = color_analysis.get("is_grayscale", False)
            dominant_colors = color_analysis.get("dominant_colors", [])
            
            # Build a summary
            summary = f"Your image is {width}x{height} pixels with an aspect ratio of {aspect_ratio}. "
            summary += f"It has {layer_count} layers. "
            
            if has_selection:
                selection_size = analysis_results.get("selection_size", {})
                selection_width = selection_size.get("width", 0)
                selection_height = selection_size.get("height", 0)
                summary += f"You have an active selection of size {selection_width}x{selection_height}. "
            
            summary += f"The overall brightness is {brightness:.1f} and contrast is {contrast:.1f}. "
            
            if is_grayscale:
                summary += "The image appears to be grayscale. "
            else:
                if dominant_colors:
                    summary += f"The dominant colors are {', '.join(dominant_colors)}. "
            
            # Add detected objects if available (from detailed analysis)
            if "detected_objects" in analysis_results:
                objects = analysis_results["detected_objects"]
                if objects and objects[0]["label"] != "unknown":
                    object_labels = [obj["label"] for obj in objects]
                    summary += f"I detected the following objects: {', '.join(object_labels)}. "
            
            summary += "How would you like me to help you edit this image?"
            
            return summary
        except Exception as e:
            return "I've analyzed your image but couldn't generate a detailed summary. How can I help you with it?"
    
    # Function to apply the current suggestion
    def on_apply_clicked(widget):
        suggestion = conversation_context["current_suggestion"]
        if not suggestion:
            pdb.gimp_message("No suggestion available to apply.")
            return
        
        # Disable apply button and show progress
        apply_button.set_sensitive(False)
        progress_bar.set_text("Applying suggestion...")
        progress_bar.set_fraction(0.3)
        
        # Process in a separate thread to avoid blocking the UI
        threading.Thread(target=apply_suggestion, args=(suggestion,)).start()
    
    # Function to apply the suggestion in a background thread
    def apply_suggestion(suggestion):
        try:
            # Parse the suggestion
            suggestion_type = suggestion.get("type")
            operation = suggestion.get("operation")
            parameters = suggestion.get("parameters", {})
            
            # Prepare the request for the GIMP API
            request_params = {
                "operation": operation,
                "image_id": image.ID,
                "drawable_id": drawable.ID
            }
            # Add all parameters from the suggestion
            request_params.update(parameters)
            
            # Send the request to the server
            response = send_request(server_url, "gimp_api", request_params)
            
            # Process the response
            if response and response.get("status") == "success":
                # Update the UI in the main thread
                gtk.gdk.threads_enter()
                
                # Update the conversation
                append_to_conversation("AI Assistant", f"I've applied the suggestion: {operation}")
                
                # Update progress bar
                progress_bar.set_text("Suggestion applied")
                progress_bar.set_fraction(1.0)
                
                # Reset suggestion
                conversation_context["current_suggestion"] = None
                apply_button.set_sensitive(False)
                
                # Refresh the display
                gimp.displays_flush()
                
                gtk.gdk.threads_leave()
            else:
                # Handle error
                gtk.gdk.threads_enter()
                
                error_message = response.get("message", "Unknown error")
                append_to_conversation("AI Assistant", f"Sorry, I couldn't apply the suggestion: {error_message}")
                progress_bar.set_text("Failed to apply suggestion")
                progress_bar.set_fraction(0.0)
                apply_button.set_sensitive(True)
                
                gtk.gdk.threads_leave()
        except Exception as e:
            # Handle exceptions
            gtk.gdk.threads_enter()
            
            error_message = str(e)
            append_to_conversation("AI Assistant", f"An error occurred while applying the suggestion: {error_message}")
            progress_bar.set_text("Error occurred")
            progress_bar.set_fraction(0.0)
            apply_button.set_sensitive(False)  # Leave disabled if it failed
            
            gtk.gdk.threads_leave()
    
    # Function to close the dialog
    def on_close_clicked(widget):
        dialog.destroy()
    
    # Connect signals
    send_button.connect("clicked", on_send_clicked)
    analyze_button.connect("clicked", on_analyze_clicked)
    apply_button.connect("clicked", on_apply_clicked)
    close_button.connect("clicked", on_close_clicked)
    
    # Connect Enter key to send
    def on_key_press(widget, event):
        if event.keyval == gtk.keysyms.Return:
            on_send_clicked(None)
            return True
        return False
    
    user_input.connect("key-press-event", on_key_press)
    
    # Show the dialog
    dialog.show()
    
    # Start analyzing the image automatically
    threading.Thread(target=analyze_image).start()
    
    # Run the dialog
    dialog.run()
    dialog.destroy()
