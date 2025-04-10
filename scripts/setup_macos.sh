#!/bin/bash
# setup_macos.sh
# macOS-specific setup script for GIMP AI Integration

# Exit on error
set -e

# Get directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Print banner
echo "============================================"
echo "GIMP AI Integration - macOS Setup"
echo "============================================"
echo

# Check Python version
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
    echo "❌ Error: Python 3.8 or later is required."
    echo "Current version: $PYTHON_VERSION"
    echo "Please install a newer version of Python and try again."
    exit 1
fi

echo "✅ Python version $PYTHON_VERSION is supported."

# Create virtual environment
VENV_DIR="$PROJECT_ROOT/venv"
if [ -d "$VENV_DIR" ]; then
    echo "Virtual environment already exists at $VENV_DIR"
else
    echo "Creating virtual environment at $VENV_DIR..."
    python3 -m venv "$VENV_DIR"
    echo "✅ Virtual environment created successfully"
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"
echo "✅ Virtual environment activated"

# Install dependencies
echo "Installing backend dependencies..."
pip install -r "$PROJECT_ROOT/backend/requirements.txt"
echo "✅ Backend dependencies installed successfully"

echo "Installing frontend dependencies..."
pip install -r "$PROJECT_ROOT/frontend/requirements.txt"
echo "✅ Frontend dependencies installed successfully"

# Run setup script
echo "Running main setup script..."
python "$SCRIPT_DIR/setup_gimp_ai.py" --venv --no-deploy

# Special handling for macOS GIMP plugins
echo
echo "Setting up GIMP plugin for macOS..."

# Check for all possible GIMP installations
echo "Searching for GIMP installations on macOS..."

# Define all possible installation paths
GIMP_PATHS=(
    "/Applications/GIMP-3.0.app" 
    "/Applications/GIMP.app" 
    "/Applications/GIMP-2.10.app"
    "/System/Applications/GIMP.app"  # For system-wide installations
    "$HOME/Applications/GIMP.app"    # For user-specific installations
)

# Define all possible plugin paths
GIMP3_USER_PLUGINS="$HOME/Library/Application Support/GIMP/3.0/plug-ins"
GIMP2_USER_PLUGINS="$HOME/Library/Application Support/GIMP/2.10/plug-ins"

# List of found GIMP installations
FOUND_GIMP_APPS=()
FOUND_VERSIONS=()
FOUND_PLUGIN_PATHS=()
FOUND_ALT_PLUGIN_PATHS=()

# Check each path
for GIMP_PATH in "${GIMP_PATHS[@]}"; do
    if [ -d "$GIMP_PATH" ]; then
        echo "Found GIMP at: $GIMP_PATH"
        FOUND_GIMP_APPS+=("$GIMP_PATH")
        
        # Check if it's GIMP 3.0
        if [ -d "$GIMP_PATH/Contents/Resources/lib/gimp/3.0" ]; then
            echo "  ✓ Detected as GIMP 3.0"
            FOUND_VERSIONS+=("3.0")
            FOUND_PLUGIN_PATHS+=("$GIMP3_USER_PLUGINS")
            FOUND_ALT_PLUGIN_PATHS+=("$GIMP_PATH/Contents/Resources/lib/gimp/3.0/plug-ins")
        else
            # Assume it's GIMP 2.10
            echo "  ✓ Detected as GIMP 2.10"
            FOUND_VERSIONS+=("2.10")
            FOUND_PLUGIN_PATHS+=("$GIMP2_USER_PLUGINS")
            FOUND_ALT_PLUGIN_PATHS+=("")
        fi
    fi
done

# If no GIMP installations found
if [ ${#FOUND_GIMP_APPS[@]} -eq 0 ]; then
    echo "❌ No GIMP installations found in standard locations."
    echo "If GIMP is installed in a non-standard location, you can specify it now."
    
    # Ask user if they want to specify a custom path, install to default, or abort
    echo "Choose an option:"
    echo "1) Specify custom GIMP path"
    echo "2) Install to default locations (recommended)"
    echo "3) Abort installation"
    read -p "Enter your choice (1-3): " CHOICE
    
    case $CHOICE in
        1)
            # Ask for custom path
            read -p "Enter the full path to your GIMP installation: " CUSTOM_PATH
            if [ -d "$CUSTOM_PATH" ]; then
                echo "Found GIMP at: $CUSTOM_PATH"
                
                # Try to detect version
                if [ -d "$CUSTOM_PATH/Contents/Resources/lib/gimp/3.0" ]; then
                    echo "  ✓ Detected as GIMP 3.0"
                    FOUND_VERSIONS=("3.0")
                    FOUND_PLUGIN_PATHS=("$GIMP3_USER_PLUGINS")
                    FOUND_ALT_PLUGIN_PATHS=("$CUSTOM_PATH/Contents/Resources/lib/gimp/3.0/plug-ins")
                else
                    echo "  ✓ Assuming GIMP 2.10"
                    FOUND_VERSIONS=("2.10")
                    FOUND_PLUGIN_PATHS=("$GIMP2_USER_PLUGINS")
                    FOUND_ALT_PLUGIN_PATHS=("")
                fi
            else
                echo "❌ No GIMP installation found at $CUSTOM_PATH"
                echo "Installing to default locations instead."
                FOUND_VERSIONS=("2.10" "3.0")
                FOUND_PLUGIN_PATHS=("$GIMP2_USER_PLUGINS" "$GIMP3_USER_PLUGINS")
                FOUND_ALT_PLUGIN_PATHS=("" "")
            fi
            ;;
        2)
            # Set default locations
            echo "Will install for both GIMP 2.10 and 3.0 to standard plugin directories."
            FOUND_VERSIONS=("2.10" "3.0")
            FOUND_PLUGIN_PATHS=("$GIMP2_USER_PLUGINS" "$GIMP3_USER_PLUGINS")
            FOUND_ALT_PLUGIN_PATHS=("" "")
            ;;
        3)
            echo "Installation aborted. You can manually run the deploy.py script later."
            exit 1
            ;;
        *)
            echo "Invalid choice. Installing to default locations."
            FOUND_VERSIONS=("2.10" "3.0")
            FOUND_PLUGIN_PATHS=("$GIMP2_USER_PLUGINS" "$GIMP3_USER_PLUGINS")
            FOUND_ALT_PLUGIN_PATHS=("" "")
            ;;
    esac
fi

# Define function to install for a specific version
install_for_version() {
    local GIMP_VERSION="$1"
    local PLUGIN_DIR="$2"
    local ALT_PLUGIN_DIR="$3"
    
    echo "Installing for GIMP $GIMP_VERSION:"
    echo "  → Main plugin directory: $PLUGIN_DIR"
    if [ -n "$ALT_PLUGIN_DIR" ]; then
        echo "  → Alternative plugin directory: $ALT_PLUGIN_DIR"
    fi
    
    # Create main plugin directory if it doesn't exist
    mkdir -p "$PLUGIN_DIR"
    
    # Set up the plugin
    PLUGIN_SRC="$PROJECT_ROOT/frontend/gimp_plugin"
    PLUGIN_DEST="$PLUGIN_DIR/gimp_ai_integration"
    
    # Remove old plugin if it exists
    if [ -d "$PLUGIN_DEST" ]; then
        echo "  → Removing existing plugin..."
        rm -rf "$PLUGIN_DEST"
    fi
    
    # Copy plugin files
    echo "  → Copying plugin files..."
    cp -r "$PLUGIN_SRC" "$PLUGIN_DEST"
    
    # Make the appropriate plugin file executable
    if [ "$GIMP_VERSION" == "3.0" ]; then
        PLUGIN_MAIN="$PLUGIN_DEST/plugin_main_gimp3.py"
        if [ -f "$PLUGIN_MAIN" ]; then
            chmod +x "$PLUGIN_MAIN"
            echo "  → Made plugin_main_gimp3.py executable"
            
            # Create symlink for convenience
            ln -sf "$PLUGIN_MAIN" "$PLUGIN_DEST/plugin_main.py"
            echo "  → Created symlink from plugin_main.py to plugin_main_gimp3.py"
        else
            echo "  ⚠️ Warning: Could not find plugin_main_gimp3.py"
        fi
        
        # Try alternative plugin directory if specified
        if [ -n "$ALT_PLUGIN_DIR" ]; then
            # Create directory structure if not exists
            mkdir -p "$(dirname "$ALT_PLUGIN_DIR")"
            mkdir -p "$ALT_PLUGIN_DIR"
            
            # Set up the alternative plugin location
            ALT_PLUGIN_DEST="$ALT_PLUGIN_DIR/gimp_ai_integration"
            
            # Remove old plugin if it exists
            if [ -d "$ALT_PLUGIN_DEST" ]; then
                rm -rf "$ALT_PLUGIN_DEST"
            fi
            
            # Copy plugin files
            echo "  → Installing to alternative location..."
            cp -r "$PLUGIN_SRC" "$ALT_PLUGIN_DEST"
            
            # Make the plugin file executable
            chmod +x "$ALT_PLUGIN_DEST/plugin_main_gimp3.py"
            ln -sf "$ALT_PLUGIN_DEST/plugin_main_gimp3.py" "$ALT_PLUGIN_DEST/plugin_main.py"
            echo "  → Plugin also installed to alternative location"
        fi
    else
        PLUGIN_MAIN="$PLUGIN_DEST/plugin_main.py"
        chmod +x "$PLUGIN_MAIN"
        echo "  → Made plugin_main.py executable"
    fi
    
    echo "  ✅ Installation complete for GIMP $GIMP_VERSION"
}

# If multiple GIMP installations found, let user choose
if [ ${#FOUND_GIMP_APPS[@]} -gt 1 ]; then
    echo "Multiple GIMP installations found. Installing for all versions."
    
    for i in "${!FOUND_GIMP_APPS[@]}"; do
        GIMP_APP="${FOUND_GIMP_APPS[$i]}"
        GIMP_VERSION="${FOUND_VERSIONS[$i]}"
        PLUGIN_DIR="${FOUND_PLUGIN_PATHS[$i]}"
        ALT_PLUGIN_DIR="${FOUND_ALT_PLUGIN_PATHS[$i]}"
        
        echo "Installing for GIMP $GIMP_VERSION at $GIMP_APP..."
        
        # Continue with installation for this version
        install_for_version "$GIMP_VERSION" "$PLUGIN_DIR" "$ALT_PLUGIN_DIR"
    done
else
    # Only one installation found or using defaults
    for i in "${!FOUND_VERSIONS[@]}"; do
        GIMP_VERSION="${FOUND_VERSIONS[$i]}"
        PLUGIN_DIR="${FOUND_PLUGIN_PATHS[$i]}"
        ALT_PLUGIN_DIR="${FOUND_ALT_PLUGIN_PATHS[$i]}"
        
        echo "Installing for GIMP $GIMP_VERSION..."
        
        # Continue with installation for this version
        install_for_version "$GIMP_VERSION" "$PLUGIN_DIR" "$ALT_PLUGIN_DIR"
    done
fi

# Function to install for a specific GIMP version
install_for_version() {
    local GIMP_VERSION="$1"
    local PLUGIN_DIR="$2"
    local ALT_PLUGIN_DIR="$3"
    
    echo "Installing for GIMP $GIMP_VERSION:"
    echo "  → Main plugin directory: $PLUGIN_DIR"
    if [ -n "$ALT_PLUGIN_DIR" ]; then
        echo "  → Alternative plugin directory: $ALT_PLUGIN_DIR"
    fi
    
    # Create main plugin directory if it doesn't exist
    mkdir -p "$PLUGIN_DIR"
    
    # Set up the plugin
    PLUGIN_SRC="$PROJECT_ROOT/frontend/gimp_plugin"
    PLUGIN_DEST="$PLUGIN_DIR/gimp_ai_integration"
    
    # Remove old plugin if it exists
    if [ -d "$PLUGIN_DEST" ]; then
        echo "  → Removing existing plugin..."
        rm -rf "$PLUGIN_DEST"
    fi
    
    # Copy plugin files
    echo "  → Copying plugin files..."
    cp -r "$PLUGIN_SRC" "$PLUGIN_DEST"
    
    # Make the appropriate plugin file executable
    if [ "$GIMP_VERSION" == "3.0" ]; then
        PLUGIN_MAIN="$PLUGIN_DEST/plugin_main_gimp3.py"
        if [ -f "$PLUGIN_MAIN" ]; then
            chmod +x "$PLUGIN_MAIN"
            echo "  → Made plugin_main_gimp3.py executable"
            
            # Create symlink for convenience
            ln -sf "$PLUGIN_MAIN" "$PLUGIN_DEST/plugin_main.py"
            echo "  → Created symlink from plugin_main.py to plugin_main_gimp3.py"
        else
            echo "  ⚠️ Warning: Could not find plugin_main_gimp3.py"
        fi
        
        # Try alternative plugin directory if specified
        if [ -n "$ALT_PLUGIN_DIR" ]; then
            # Create directory structure if not exists
            mkdir -p "$(dirname "$ALT_PLUGIN_DIR")"
            mkdir -p "$ALT_PLUGIN_DIR"
            
            # Set up the alternative plugin location
            ALT_PLUGIN_DEST="$ALT_PLUGIN_DIR/gimp_ai_integration"
            
            # Remove old plugin if it exists
            if [ -d "$ALT_PLUGIN_DEST" ]; then
                rm -rf "$ALT_PLUGIN_DEST"
            fi
            
            # Copy plugin files
            echo "  → Installing to alternative location..."
            cp -r "$PLUGIN_SRC" "$ALT_PLUGIN_DEST"
            
            # Make the plugin file executable
            chmod +x "$ALT_PLUGIN_DEST/plugin_main_gimp3.py"
            ln -sf "$ALT_PLUGIN_DEST/plugin_main_gimp3.py" "$ALT_PLUGIN_DEST/plugin_main.py"
            echo "  → Plugin also installed to alternative location"
        fi
    else
        PLUGIN_MAIN="$PLUGIN_DEST/plugin_main.py"
        chmod +x "$PLUGIN_MAIN"
        echo "  → Made plugin_main.py executable"
    fi
    
    echo "  ✅ Installation complete for GIMP $GIMP_VERSION"
}

# Install for all detected versions or user-selected version
for i in "${!FOUND_VERSIONS[@]}"; do
    GIMP_VERSION="${FOUND_VERSIONS[$i]}"
    PLUGIN_DIR="${FOUND_PLUGIN_PATHS[$i]}"
    ALT_PLUGIN_DIR="${FOUND_ALT_PLUGIN_PATHS[$i]}"
    
    install_for_version "$GIMP_VERSION" "$PLUGIN_DIR" "$ALT_PLUGIN_DIR"
done

# Create activation script with socket server support
ACTIVATE_SCRIPT="$PROJECT_ROOT/start_gimp_ai.sh"
cat > "$ACTIVATE_SCRIPT" << EOF
#!/bin/bash
# start_gimp_ai.sh
# Script to start the GIMP AI Integration server(s)

# Get directory where this script is located
SCRIPT_DIR="\$( cd "\$( dirname "\${BASH_SOURCE[0]}" )" && pwd )"

# Activate virtual environment
source "\$SCRIPT_DIR/venv/bin/activate"

# Set environment variables
export MCP_SERVER_URL="http://localhost:8000/jsonrpc"
export MCP_SERVER_HOST="localhost"
export MCP_SERVER_PORT="8000"
export MCP_SOCKET_HOST="localhost"
export MCP_SOCKET_PORT="9876"
export MCP_PREFER_SOCKET="true"

# Determine protocol mode from arguments
PROTOCOL="both"  # Default: start both HTTP and Socket servers
VERBOSE=false

# Parse command line arguments
while [[ \$# -gt 0 ]]; do
    case \$1 in
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
            echo "Usage: \$0 [--http-only|--socket-only] [--verbose]"
            echo ""
            echo "Options:"
            echo "  --http-only    Start only the HTTP JSON-RPC server"
            echo "  --socket-only  Start only the Socket JSON-RPC server"
            echo "  --verbose      Enable verbose logging"
            echo "  --help         Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: \$1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Create log directory if it doesn't exist
mkdir -p "\$SCRIPT_DIR/logs"

# Start servers based on protocol mode
if [ "\$PROTOCOL" = "http" ] || [ "\$PROTOCOL" = "both" ]; then
    echo "Starting HTTP JSON-RPC server on \$MCP_SERVER_HOST:\$MCP_SERVER_PORT..."
    if [ "\$PROTOCOL" = "both" ]; then
        # Start in background
        if [ "\$VERBOSE" = true ]; then
            python "\$SCRIPT_DIR/backend/server/app.py" 2>&1 | tee "\$SCRIPT_DIR/logs/http_server.log" &
        else
            python "\$SCRIPT_DIR/backend/server/app.py" > "\$SCRIPT_DIR/logs/http_server.log" 2>&1 &
        fi
        HTTP_PID=\$!
        echo "✅ HTTP server started (PID: \$HTTP_PID)"
    else
        # Start in foreground
        if [ "\$VERBOSE" = true ]; then
            python "\$SCRIPT_DIR/backend/server/app.py" 2>&1 | tee "\$SCRIPT_DIR/logs/http_server.log"
        else
            python "\$SCRIPT_DIR/backend/server/app.py"
        fi
    fi
fi

if [ "\$PROTOCOL" = "socket" ] || [ "\$PROTOCOL" = "both" ]; then
    echo "Starting Socket JSON-RPC server on \$MCP_SOCKET_HOST:\$MCP_SOCKET_PORT..."
    if [ "\$PROTOCOL" = "both" ]; then
        # Start in background
        if [ "\$VERBOSE" = true ]; then
            python "\$SCRIPT_DIR/backend/server/socket_server.py" 2>&1 | tee "\$SCRIPT_DIR/logs/socket_server.log" &
        else
            python "\$SCRIPT_DIR/backend/server/socket_server.py" > "\$SCRIPT_DIR/logs/socket_server.log" 2>&1 &
        fi
        SOCKET_PID=\$!
        echo "✅ Socket server started (PID: \$SOCKET_PID)"
    else
        # Start in foreground
        if [ "\$VERBOSE" = true ]; then
            python "\$SCRIPT_DIR/backend/server/socket_server.py" 2>&1 | tee "\$SCRIPT_DIR/logs/socket_server.log"
        else
            python "\$SCRIPT_DIR/backend/server/socket_server.py"
        fi
    fi
fi

# If both servers are running, wait for either to exit
if [ "\$PROTOCOL" = "both" ]; then
    echo ""
    echo "Both servers are now running."
    echo "To test the connection from GIMP, launch GIMP and select:"
    echo "  Filters > AI Tools > Hello World"
    echo ""
    echo "Press Ctrl+C to stop all servers."
    echo "Logs are saved in \$SCRIPT_DIR/logs/"
    echo ""
    
    # Wait for Ctrl+C
    trap "echo 'Stopping servers...'; kill \$HTTP_PID \$SOCKET_PID 2>/dev/null; exit 0" INT TERM
    wait \$HTTP_PID \$SOCKET_PID
fi
EOF

chmod +x "$ACTIVATE_SCRIPT"
echo "✅ Created server start script: $ACTIVATE_SCRIPT"

# Print final instructions
echo
echo "============================================"
echo "GIMP AI Integration - Setup Complete!"
echo "============================================"
echo
echo "To start the MCP server:"
echo "  $ACTIVATE_SCRIPT"
echo
echo "Then launch GIMP and use the AI features under:"
echo "  Filters > AI Tools"
echo
echo "To test the connection, try the 'Hello World' option first."
echo
echo "Troubleshooting:"
echo "1. If the plugin doesn't appear in GIMP's menu:"
echo "   - Restart GIMP"
echo "   - Check that the plugin is in the correct directory:"
for i in "${!FOUND_VERSIONS[@]}"; do
    VERSION="${FOUND_VERSIONS[$i]}"
    DIR="${FOUND_PLUGIN_PATHS[$i]}"
    echo "     GIMP $VERSION: $DIR/gimp_ai_integration"
done
echo
echo "2. If the server won't start:"
echo "   - Check that Python and all dependencies are installed"
echo "   - Try running with --verbose flag for more details"
echo "   - Check logs in the logs/ directory"
echo
echo "3. If the plugin can't connect to the server:"
echo "   - Make sure both servers are running"
echo "   - Check that no firewall is blocking connections"
echo "   - Try using the socket server with --socket-only flag"
echo
echo "Additional flags for $ACTIVATE_SCRIPT:"
echo "  --http-only: Use only HTTP server"
echo "  --socket-only: Use only socket server"
echo "  --verbose: Show detailed logs"
echo
echo "Enjoy using GIMP AI Integration!"
echo "============================================"
