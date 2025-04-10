# Developer Guide

This guide provides information for developers who want to contribute to or extend the GIMP AI Integration project.

## Development Environment Setup

1. **Clone the repository**
   ```
   git clone https://github.com/yourusername/gimp-ai-integration.git
   cd gimp-ai-integration
   ```

2. **Create a virtual environment**
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```
   pip install -r backend/requirements.txt
   pip install -r frontend/requirements.txt
   ```

4. **Install development tools**
   ```
   pip install pytest flake8 black
   ```

## Project Structure

```
gimp-ai-integration/
├── backend/               # MCP Server
│   ├── server/            # Main server code
│   │   ├── __init__.py
│   │   ├── app.py         # Main entry point
│   │   ├── routes/        # Server route definitions
│   │   ├── handlers/      # Request handlers
│   │   ├── models/        # AI model wrappers
│   │   └── utils/         # Shared utilities
│   ├── tests/             # Backend tests
│   └── requirements.txt   # Backend dependencies
├── frontend/              # GIMP plugin
│   ├── gimp_plugin/       # Plugin code
│   │   ├── __init__.py
│   │   ├── plugin_main.py # Main plugin file
│   │   ├── dialogs/       # UI dialogs
│   │   ├── client/        # MCP client code
│   │   └── utils/         # Shared utilities
│   └── requirements.txt   # Frontend dependencies
├── docs/                  # Documentation
└── models/                # Local AI models (optional)
```

## Adding a New AI Feature

To add a new AI feature to the system, you need to:

1. **Create a backend handler**

   Add a new file in `backend/server/handlers/` for your feature:
   
   ```python
   # backend/server/handlers/my_new_feature.py
   
   def handle_my_new_feature(params):
       """
       Handle a request for the new AI feature.
       
       Args:
           params (dict): Parameters including image_data, etc.
       
       Returns:
           dict: Result including processed image data.
       """
       # Process the request
       # ...
       
       return {
           "image_data": processed_image_data,
           "status": "success"
       }
   ```

2. **Register the handler in the routes**

   Update `backend/server/routes/json_rpc.py` to include your new method:
   
   ```python
   from ..handlers.my_new_feature import handle_my_new_feature
   
   # Add to the handlers dictionary
   handlers = {
       # ...existing handlers
       "ai_my_new_feature": handle_my_new_feature,
   }
   ```

3. **Create a frontend dialog**

   Add a new dialog in `frontend/gimp_plugin/dialogs/`:
   
   ```python
   # frontend/gimp_plugin/dialogs/my_new_feature_dialog.py
   
   import gi
   gi.require_version('Gtk', '2.0')
   from gi.repository import Gtk
   
   class MyNewFeatureDialog:
       def __init__(self):
           self.dialog = Gtk.Dialog("My New Feature", None, 0,
                              (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                               Gtk.STOCK_OK, Gtk.ResponseType.OK))
           
           # Add your dialog components
           # ...
           
           self.dialog.show_all()
       
       def run(self):
           response = self.dialog.run()
           if response == Gtk.ResponseType.OK:
               # Get values from dialog
               # ...
               self.dialog.destroy()
               return params
           else:
               self.dialog.destroy()
               return None
   ```

4. **Update the plugin main file**

   Update `frontend/gimp_plugin/plugin_main.py` to include your new feature:
   
   ```python
   from dialogs.my_new_feature_dialog import MyNewFeatureDialog
   from client.mcp_client import send_request
   
   def my_new_feature_function(image, drawable):
       dialog = MyNewFeatureDialog()
       params = dialog.run()
       
       if params:
           # Get image data
           # ...
           
           # Send request to server
           result = send_request("ai_my_new_feature", {
               "image_data": image_data,
               # Other parameters
           })
           
           # Process result
           # ...
   
   # Register in GIMP
   register(
       "python-fu-ai-my-new-feature",
       "My New AI Feature",
       "Description of my new feature",
       "Your Name",
       "Your Name",
       "2025",
       "<Image>/Filters/AI Tools/My New Feature",
       "RGB*, GRAY*",
       [],
       [],
       my_new_feature_function
   )
   ```

## Testing

### Running Backend Tests

```
cd backend
pytest
```

### Testing the GIMP Plugin

Since GIMP plugins run within GIMP's environment, testing is often done manually. However, you can create simple test scripts for certain components:

```
cd frontend/gimp_plugin/tests
python test_client.py
```

## Code Style

This project follows PEP 8 style guidelines. Use the following tools to ensure your code is properly formatted:

```
# Check style
flake8 backend frontend

# Format code
black backend frontend
```

## Documentation

Please document all new code with docstrings following PEP 257. Update relevant documentation in the `docs/` directory when adding new features.

## Pull Request Process

1. Create a new branch for your feature or bugfix
2. Make your changes, following the code style guide
3. Add tests for your changes
4. Update documentation as needed
5. Submit a pull request with a clear description of the changes
