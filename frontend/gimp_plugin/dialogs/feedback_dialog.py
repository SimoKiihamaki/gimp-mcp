"""
Feedback Dialog for GIMP AI Integration.

This module provides a dialog for users to submit feedback, bug reports,
and feature requests directly from GIMP.
"""
from gimpfu import *
import os
import json
import tempfile
import threading
import time
import sys

# Add the plugin directory to the Python path to find our modules
plugin_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if plugin_dir not in sys.path:
    sys.path.append(plugin_dir)

from client.mcp_client import send_request

# Default MCP server URL
DEFAULT_SERVER_URL = "http://localhost:8000/jsonrpc"

def feedback_dialog():
    """
    Show a dialog for submitting feedback.
    
    Returns:
        dict: Feedback data or None if canceled.
    """
    # Create dialog
    dialog = gimp.Dialog("Send Feedback - GIMP AI Integration", "feedback-dialog",
                       None, 0, None, None)
    
    # Set dialog size
    dialog.set_size_request(500, 600)
    
    # Create a vertical box for the dialog content
    vbox = dialog.vbox
    vbox.set_border_width(10)
    
    # Add header text
    header_label = gtk.Label("Your feedback helps us improve GIMP AI Integration.")
    header_label.set_justify(gtk.JUSTIFY_CENTER)
    vbox.pack_start(header_label, False, False, 10)
    
    # Create a table for form fields
    table = gtk.Table(7, 2, False)
    table.set_row_spacings(10)
    table.set_col_spacings(10)
    vbox.pack_start(table, False, False, 0)
    
    # Add form fields
    # 1. Feedback Type
    type_label = gtk.Label("Feedback Type:")
    type_label.set_alignment(0, 0.5)
    table.attach(type_label, 0, 1, 0, 1, gtk.FILL, gtk.FILL, 0, 0)
    
    feedback_types = [
        "Bug Report",
        "Feature Request",
        "General Feedback",
        "Question",
        "UI/UX Improvement",
        "Performance Issue",
        "Documentation Issue"
    ]
    
    type_combo = gtk.combo_box_new_text()
    for feedback_type in feedback_types:
        type_combo.append_text(feedback_type)
    type_combo.set_active(2)  # Default to "General Feedback"
    table.attach(type_combo, 1, 2, 0, 1, gtk.FILL | gtk.EXPAND, gtk.FILL, 0, 0)
    
    # 2. Feature Category
    category_label = gtk.Label("Feature Category:")
    category_label.set_alignment(0, 0.5)
    table.attach(category_label, 0, 1, 1, 2, gtk.FILL, gtk.FILL, 0, 0)
    
    categories = [
        "General",
        "Background Removal",
        "Inpainting",
        "Style Transfer",
        "Image Upscaling",
        "Installation/Setup",
        "Other"
    ]
    
    category_combo = gtk.combo_box_new_text()
    for category in categories:
        category_combo.append_text(category)
    category_combo.set_active(0)  # Default to "General"
    table.attach(category_combo, 1, 2, 1, 2, gtk.FILL | gtk.EXPAND, gtk.FILL, 0, 0)
    
    # 3. Subject
    subject_label = gtk.Label("Subject:")
    subject_label.set_alignment(0, 0.5)
    table.attach(subject_label, 0, 1, 2, 3, gtk.FILL, gtk.FILL, 0, 0)
    
    subject_entry = gtk.Entry()
    table.attach(subject_entry, 1, 2, 2, 3, gtk.FILL | gtk.EXPAND, gtk.FILL, 0, 0)
    
    # 4. Description
    description_label = gtk.Label("Description:")
    description_label.set_alignment(0, 0)
    table.attach(description_label, 0, 1, 3, 4, gtk.FILL, gtk.FILL, 0, 0)
    
    description_window = gtk.ScrolledWindow()
    description_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
    description_window.set_shadow_type(gtk.SHADOW_IN)
    
    description_buffer = gtk.TextBuffer()
    description_view = gtk.TextView(description_buffer)
    description_view.set_wrap_mode(gtk.WRAP_WORD)
    description_window.add(description_view)
    description_window.set_size_request(-1, 150)
    
    table.attach(description_window, 1, 2, 3, 4, gtk.FILL | gtk.EXPAND, gtk.FILL | gtk.EXPAND, 0, 0)
    
    # 5. System Information
    system_frame = gtk.Frame("System Information (helps us diagnose issues)")
    vbox.pack_start(system_frame, False, False, 10)
    
    system_box = gtk.VBox(False, 5)
    system_box.set_border_width(5)
    system_frame.add(system_box)
    
    # 5a. Include system info checkbox
    include_system_check = gtk.CheckButton("Include system information")
    include_system_check.set_active(True)
    system_box.pack_start(include_system_check, False, False, 0)
    
    # 5b. System info text (readonly)
    system_window = gtk.ScrolledWindow()
    system_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
    system_window.set_shadow_type(gtk.SHADOW_IN)
    
    import platform
    system_text = (
        f"OS: {platform.system()} {platform.release()}\n"
        f"GIMP Version: {gimp.version}\n"
        f"Python Version: {sys.version.split()[0]}\n"
    )
    
    # Try to get GPU information
    try:
        import torch
        if torch.cuda.is_available():
            system_text += f"GPU: {torch.cuda.get_device_name(0)}\n"
            system_text += f"CUDA Version: {torch.version.cuda}\n"
        else:
            system_text += "GPU: Not available or not detected\n"
    except ImportError:
        system_text += "GPU: Unknown (PyTorch not installed)\n"
    
    system_buffer = gtk.TextBuffer()
    system_buffer.set_text(system_text)
    system_view = gtk.TextView(system_buffer)
    system_view.set_editable(False)
    system_view.set_wrap_mode(gtk.WRAP_WORD)
    system_window.add(system_view)
    system_window.set_size_request(-1, 100)
    
    system_box.pack_start(system_window, False, False, 0)
    
    # 6. Contact Information (optional)
    contact_frame = gtk.Frame("Contact Information (optional)")
    vbox.pack_start(contact_frame, False, False, 10)
    
    contact_box = gtk.VBox(False, 5)
    contact_box.set_border_width(5)
    contact_frame.add(contact_box)
    
    # 6a. Contact name
    contact_table = gtk.Table(2, 2, False)
    contact_table.set_row_spacings(5)
    contact_table.set_col_spacings(5)
    contact_box.pack_start(contact_table, False, False, 0)
    
    name_label = gtk.Label("Name:")
    name_label.set_alignment(0, 0.5)
    contact_table.attach(name_label, 0, 1, 0, 1, gtk.FILL, gtk.FILL, 0, 0)
    
    name_entry = gtk.Entry()
    contact_table.attach(name_entry, 1, 2, 0, 1, gtk.FILL | gtk.EXPAND, gtk.FILL, 0, 0)
    
    # 6b. Contact email
    email_label = gtk.Label("Email:")
    email_label.set_alignment(0, 0.5)
    contact_table.attach(email_label, 0, 1, 1, 2, gtk.FILL, gtk.FILL, 0, 0)
    
    email_entry = gtk.Entry()
    contact_table.attach(email_entry, 1, 2, 1, 2, gtk.FILL | gtk.EXPAND, gtk.FILL, 0, 0)
    
    # 7. Privacy notice
    privacy_text = (
        "By submitting feedback, you agree to our privacy policy. "
        "We will only use your contact information to respond to your feedback "
        "if necessary. We will not share your information with third parties."
    )
    privacy_label = gtk.Label(privacy_text)
    privacy_label.set_line_wrap(True)
    privacy_label.set_justify(gtk.JUSTIFY_LEFT)
    vbox.pack_start(privacy_label, False, False, 10)
    
    # Add buttons for OK and Cancel
    dialog.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
    dialog.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
    
    # Show the dialog
    dialog.show_all()
    
    # Run the dialog and get the response
    response = dialog.run()
    
    if response == gtk.RESPONSE_OK:
        # Get the values
        feedback_type = feedback_types[type_combo.get_active()]
        category = categories[category_combo.get_active()]
        subject = subject_entry.get_text()
        
        description_start, description_end = description_buffer.get_bounds()
        description = description_buffer.get_text(description_start, description_end)
        
        include_system = include_system_check.get_active()
        system_info = system_text if include_system else ""
        
        name = name_entry.get_text()
        email = email_entry.get_text()
        
        # Destroy the dialog
        dialog.destroy()
        
        # Return the parameters
        return {
            "type": feedback_type,
            "category": category,
            "subject": subject,
            "description": description,
            "system_info": system_info,
            "name": name,
            "email": email,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    else:
        # Destroy the dialog
        dialog.destroy()
        return None

def submit_feedback(feedback_data):
    """
    Submit feedback to the server.
    
    Args:
        feedback_data (dict): Feedback data to submit
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get the server URL
        server_url = os.environ.get("MCP_SERVER_URL", DEFAULT_SERVER_URL)
        
        # Send the feedback to the server
        response = send_request(server_url, "submit_feedback", {
            "feedback": feedback_data
        })
        
        if response and response.get("status") == "success":
            return True
        else:
            # If the server is unavailable or returns an error, save the feedback locally
            save_feedback_locally(feedback_data)
            return False
    except Exception as e:
        print(f"Error submitting feedback: {e}")
        # Save the feedback locally on error
        save_feedback_locally(feedback_data)
        return False

def save_feedback_locally(feedback_data):
    """
    Save feedback to a local file if the server is unavailable.
    
    Args:
        feedback_data (dict): Feedback data to save
    """
    try:
        # Create a temporary file
        temp_dir = tempfile.gettempdir()
        feedback_dir = os.path.join(temp_dir, "gimp_ai_feedback")
        os.makedirs(feedback_dir, exist_ok=True)
        
        # Generate a unique filename
        timestamp = time.strftime("%Y%m%d%H%M%S")
        filename = f"feedback_{timestamp}.json"
        filepath = os.path.join(feedback_dir, filename)
        
        # Save the feedback to the file
        with open(filepath, "w") as f:
            json.dump(feedback_data, f, indent=2)
        
        print(f"Feedback saved locally to: {filepath}")
    except Exception as e:
        print(f"Error saving feedback locally: {e}")
