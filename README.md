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
- GIMP 2.10 or later
- Python 3.8 or later
- Required Python packages (see requirements.txt files)

### Setup
1. Clone this repository
2. Install backend dependencies: `pip install -r backend/requirements.txt`
3. Install frontend dependencies: `pip install -r frontend/requirements.txt`
4. Copy or symlink the `frontend/gimp_plugin` directory to your GIMP plugins directory
5. Start the MCP server: `python backend/server/app.py`
6. Launch GIMP and access AI features under "Filters > AI Tools"

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
