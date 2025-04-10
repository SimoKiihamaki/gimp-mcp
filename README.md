# GIMP AI Integration Addon and MCP Server

This project integrates advanced AI capabilities into GIMP through a Python plugin and Model Context Protocol (MCP) server.

## Overview

The GIMP AI Integration Addon provides users with AI-powered image editing tools directly within GIMP, including:

- Background removal
- Inpainting
- Style transfer
- Image upscaling
- AI Assistant for interactive editing guidance
- Image analysis and content understanding
- Direct integration with Claude Desktop and other AI systems

The system consists of two main components:
1. **GIMP Python Plugin (Frontend)**: Integrates with GIMP's menu system and provides UI for AI features
2. **MCP Server (Backend)**: Processes requests from the plugin and interfaces with AI models

## Project Structure

```
gimp-ai-integration/
├── backend/               # MCP Server
│   ├── server/            # Main server code
│   │   ├── routes/        # Server route definitions
│   │   ├── handlers/      # Request handlers
│   │   ├── models/        # AI model wrappers
│   │   └── utils/         # Shared utilities
│   └── tests/             # Backend tests
├── frontend/              # GIMP plugin
│   └── gimp_plugin/       # Plugin code
│       ├── dialogs/       # UI dialogs
│       ├── client/        # MCP client code
│       └── utils/         # Shared utilities
├── docs/                  # Documentation
├── utils/                 # Utility scripts and helper libraries
├── examples/              # Example scripts and usage samples
└── models/                # Local AI models (optional)
```

## Installation

### Prerequisites
- GIMP 2.10 or GIMP 3.0
- Python 3.8 or later
- Required Python packages (see requirements.txt files)

### Easy Setup (Recommended)
Use our automated setup script which handles dependencies, environment configuration, and plugin installation:

```bash
# Clone the repository
git clone https://github.com/yourusername/gimp-ai-integration.git
cd gimp-ai-integration

# Run the setup script (creates a virtual environment)
python scripts/setup_gimp_ai.py --venv

# Follow the on-screen instructions to complete setup
```

### Manual Setup
If you prefer to set up manually:

1. Clone this repository
2. Install dependencies:
   ```bash
   pip install -r backend/requirements.txt
   pip install -r frontend/requirements.txt
   ```
3. Deploy the plugin to GIMP:
   ```bash
   python scripts/deploy.py
   ```
   This will detect your GIMP version (2.10 or 3.0) and install the appropriate plugin version.
4. Set environment variables:
   ```bash
   # On macOS/Linux
   export MCP_SERVER_URL="http://localhost:8000/jsonrpc"
   
   # On Windows
   set MCP_SERVER_URL=http://localhost:8000/jsonrpc
   ```
5. Start the MCP server:
   ```bash
   python backend/server/app.py
   ```
6. Launch GIMP and access AI features under "Filters > AI Tools"

### macOS Specific Instructions
On macOS, we provide a dedicated setup script that handles all the details:

```bash
# Clone the repository
git clone https://github.com/yourusername/gimp-ai-integration.git
cd gimp-ai-integration

# Make the setup script executable
chmod +x scripts/setup_macos.sh

# Run the setup script
./scripts/setup_macos.sh

# Follow the on-screen instructions
```

The script will:
1. Create a Python virtual environment
2. Install all dependencies
3. Detect your GIMP version (2.10 or 3.0)
4. Install the plugin to the correct location
5. Create a start script for the server

Once setup is complete, you can start the server with:
```bash
./start_gimp_ai.sh
```

For reference, the GIMP plugin directories on macOS are:
- GIMP 2.10: `~/Library/Application Support/GIMP/2.10/plug-ins/`
- GIMP 3.0: `~/Library/Application Support/GIMP/3.0/plug-ins/` or inside the application bundle

If you're using GIMP 3.0 and encounter issues with the plugin not showing up:
1. Check that you're using the GIMP 3.0 compatible plugin (plugin_main_gimp3.py)
2. Make sure the plugin file is executable: `chmod +x plugin_main_gimp3.py`
3. Try both plugin directories to ensure it's installed in the correct location
4. Use the "Hello World" option in the AI Tools menu to test the connection to the server

### Troubleshooting

If the plugin doesn't appear in GIMP's menu:
- Ensure the plugin is installed in the correct directory for your GIMP version
- Check that the plugin file is executable
- Restart GIMP after installing the plugin
- Look for error messages in GIMP's Error Console (Windows > Dockable Dialogs > Error Console)

If the plugin can't connect to the server:
- Make sure the MCP server is running
- Check that the MCP_SERVER_URL environment variable is set correctly
- Try the "Hello World" option to test the connection
- Look for error messages in both GIMP and the server terminal

## Features

### For GIMP Users
- **AI Tools menu** integrated directly into GIMP
- **Background removal** with a single click
- **Inpainting** to remove unwanted objects
- **Style transfer** to apply artistic styles
- **Image upscaling** with AI-enhanced details
- **AI Assistant** for interactive editing guidance
- **Image analysis** to understand image content

### For Claude Desktop and AI Systems
- **Full MCP API** for direct control of GIMP
- **Session-based operations** for complex editing workflows
- **Image analysis capabilities** for content understanding
- **Batch command execution** for efficient operations
- **Helper library** for easy integration

## Documentation

See the `docs/` directory for detailed documentation:
- [User Guide](docs/user_guide.md)
- [Developer Guide](docs/developer_guide.md)
- [Architecture Overview](docs/architecture.md)
- [MCP API Specification](docs/mcp_api_specification.md)

## Claude Desktop Integration

The GIMP AI Integration provides a comprehensive API that allows Claude Desktop to create and edit images programmatically. The `utils/claude_desktop_helper.py` library provides a simple interface for Claude Desktop to interact with GIMP.

Example usage:

```python
from utils.claude_desktop_helper import GimpMCPClient

# Create a client
client = GimpMCPClient()

# Create a new image
session_id = client.create_new_image(800, 600)

# Add some text
client.add_text("Hello, Claude Desktop!", 100, 300)

# Apply a blur
client.apply_blur(10.0)

# Save the image
client.save_image("output.png")

# Close the session
client.close_session()
```

See the `examples/claude_desktop_example.py` file for a more comprehensive example.

## License

[MIT License](LICENSE)
