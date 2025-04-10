#!/bin/bash
source /Users/simo/Projects/gimp-ai-integration/venv/bin/activate
export MCP_SERVER_URL=http://localhost:8000/jsonrpc
export MCP_SERVER_HOST=localhost
export MCP_SERVER_PORT=8000
export MCP_SOCKET_HOST=localhost
export MCP_SOCKET_PORT=9876
export MCP_PREFER_SOCKET=true
echo "Environment variables set for GIMP AI Integration"
echo "To start the MCP servers, run:"
echo "  /Users/simo/Projects/gimp-ai-integration/start_gimp_ai.sh"
