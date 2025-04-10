"""
Example script showing how Claude Desktop can use the GIMP AI Integration.

This script demonstrates a typical workflow where Claude Desktop:
1. Creates a new image
2. Analyzes the image
3. Makes edits based on user instructions
4. Saves the result
"""
import sys
import os
import json
import time

# Add parent directory to path to import the helper
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.claude_desktop_helper import GimpMCPClient

def main():
    """Run the example workflow."""
    print("Starting Claude Desktop example workflow")
    
    # Create a client
    client = GimpMCPClient()
    
    try:
        # 1. Create a new image
        print("Creating a new 1000x800 image...")
        session_id = client.create_new_image(1000, 800, (240, 240, 255, 255))  # Light blue background
        print(f"Created new image with session ID: {session_id}")
        
        # 2. Add some initial content
        print("Adding title text...")
        client.add_text("Created by Claude Desktop", 250, 100, font="Arial", size=36, color=(0, 0, 128))
        
        print("Adding image description...")
        client.add_text("This image demonstrates the GIMP AI Integration", 300, 200, font="Arial", size=18, color=(64, 64, 64))
        
        # 3. Apply some effects
        print("Applying a blur effect...")
        client.apply_blur(1.5)
        
        # 4. Analyze the image
        print("Analyzing the image...")
        analysis = client.analyze_image("detailed")
        print("Image analysis results:")
        print(json.dumps(analysis, indent=2))
        
        # 5. Make edits based on analysis
        print("Adjusting brightness/contrast based on analysis...")
        brightness = analysis.get("color_analysis", {}).get("brightness", 120)
        
        # If the image is too dark, brighten it
        if brightness < 100:
            print("Image appears dark, increasing brightness...")
            client.adjust_brightness_contrast(brightness=30)
        elif brightness > 200:
            print("Image appears too bright, decreasing brightness...")
            client.adjust_brightness_contrast(brightness=-20)
        
        # 6. Execute multiple commands in one request
        print("Executing a sequence of commands...")
        result = client.execute_commands([
            {
                "operation": "create_rectangle_selection",
                "params": {
                    "x": 200,
                    "y": 300,
                    "width": 600,
                    "height": 400
                }
            },
            {
                "operation": "fill_selection",
                "params": {
                    "fill_type": 1  # Foreground fill
                }
            },
            {
                "operation": "select_none",
                "params": {}
            }
        ])
        print("Commands executed successfully:", result.get("success", False))
        
        # 7. Get AI assistance
        print("Getting AI assistance...")
        response = client.get_ai_assistance("Can you suggest an improvement for this image?")
        print(f"AI suggests: {response.get('message', 'No suggestion')}")
        
        # 8. Apply the suggestion if available
        if "suggestion" in response:
            print("Applying AI suggestion...")
            client.apply_suggestion(response["suggestion"])
            print("Applied AI suggestion")
        
        # 9. Save the result
        output_file = os.path.join(os.path.dirname(__file__), "claude_desktop_output.png")
        print(f"Saving the image to {output_file}...")
        client.save_image(output_file)
        print(f"Image saved to {output_file}")
        
        # 10. Close the session
        print("Closing the session...")
        client.close_session()
        print("Session closed")
        
        print("Example workflow completed successfully!")
    
    except Exception as e:
        print(f"Error in example workflow: {e}")
        # Ensure session is closed on error
        try:
            client.close_session()
        except:
            pass

if __name__ == "__main__":
    main()
