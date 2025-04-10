#!/bin/bash
# start_gimp_ai.sh
# Script to start the GIMP AI Integration server(s)

# Get directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Activate virtual environment if it exists
if [ -d "$SCRIPT_DIR/venv" ]; then
    source "$SCRIPT_DIR/venv/bin/activate"
    echo "✅ Virtual environment activated"
else
    echo "⚠️ Virtual environment not found. Using system Python."
fi

# Set environment variables
export MCP_SERVER_URL=http://localhost:8000/jsonrpc
export MCP_SERVER_HOST=localhost
export MCP_SERVER_PORT=8000
export MCP_SOCKET_HOST=localhost
export MCP_SOCKET_PORT=9876
export MCP_PREFER_SOCKET=true

# Determine protocol mode from arguments
PROTOCOL="both"  # Default: start both HTTP and Socket servers
VERBOSE=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --http-only)
            PROTOCOL="http"
            shift
            ;;
        --socket-only)
            PROTOCOL="socket"
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            echo "Usage: $0 [--http-only|--socket-only] [--verbose]"
            echo ""
            echo "Options:"
            echo "  --http-only    Start only the HTTP JSON-RPC server"
            echo "  --socket-only  Start only the Socket JSON-RPC server"
            echo "  --verbose      Enable verbose logging"
            echo "  --help         Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Create log directory if it doesn't exist
mkdir -p "$SCRIPT_DIR/logs"

# Start servers based on protocol mode
if [ "$PROTOCOL" = "http" ] || [ "$PROTOCOL" = "both" ]; then
    echo "Starting HTTP JSON-RPC server on $MCP_SERVER_HOST:$MCP_SERVER_PORT..."
    if [ "$PROTOCOL" = "both" ]; then
        # Start in background
        if [ "$VERBOSE" = true ]; then
            python "$SCRIPT_DIR/backend/server/app.py" 2>&1 | tee "$SCRIPT_DIR/logs/http_server.log" &
        else
            python "$SCRIPT_DIR/backend/server/app.py" > "$SCRIPT_DIR/logs/http_server.log" 2>&1 &
        fi
        HTTP_PID=$!
        echo "✅ HTTP server started (PID: $HTTP_PID)"
    else
        # Start in foreground
        if [ "$VERBOSE" = true ]; then
            python "$SCRIPT_DIR/backend/server/app.py" 2>&1 | tee "$SCRIPT_DIR/logs/http_server.log"
        else
            python "$SCRIPT_DIR/backend/server/app.py"
        fi
    fi
fi

if [ "$PROTOCOL" = "socket" ] || [ "$PROTOCOL" = "both" ]; then
    echo "Starting Socket JSON-RPC server on $MCP_SOCKET_HOST:$MCP_SOCKET_PORT..."
    if [ "$PROTOCOL" = "both" ]; then
        # Start in background
        if [ "$VERBOSE" = true ]; then
            python "$SCRIPT_DIR/backend/server/socket_server.py" 2>&1 | tee "$SCRIPT_DIR/logs/socket_server.log" &
        else
            python "$SCRIPT_DIR/backend/server/socket_server.py" > "$SCRIPT_DIR/logs/socket_server.log" 2>&1 &
        fi
        SOCKET_PID=$!
        echo "✅ Socket server started (PID: $SOCKET_PID)"
    else
        # Start in foreground
        if [ "$VERBOSE" = true ]; then
            python "$SCRIPT_DIR/backend/server/socket_server.py" 2>&1 | tee "$SCRIPT_DIR/logs/socket_server.log"
        else
            python "$SCRIPT_DIR/backend/server/socket_server.py"
        fi
    fi
fi

# If both servers are running, wait for either to exit
if [ "$PROTOCOL" = "both" ]; then
    echo ""
    echo "Both servers are now running."
    echo "To test the connection from GIMP, launch GIMP and select:"
    echo "  Filters > AI Tools > Hello World"
    echo ""
    echo "Press Ctrl+C to stop all servers."
    echo "Logs are saved in $SCRIPT_DIR/logs/"
    echo ""
    
    # Wait for Ctrl+C
    trap "echo 'Stopping servers...'; kill $HTTP_PID $SOCKET_PID 2>/dev/null; exit 0" INT TERM
    wait $HTTP_PID $SOCKET_PID
fi
