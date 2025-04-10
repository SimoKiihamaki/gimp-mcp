#!/usr/bin/env python3
"""
Setup Script for GIMP AI Integration

This script performs a complete setup for the GIMP AI Integration:
1. Checks for Python dependencies
2. Creates a virtual environment (if requested)
3. Installs required packages
4. Configures environment variables
5. Deploys the plugin to the correct GIMP location
6. Provides instructions for starting the server and using the plugin

Usage:
    python setup_gimp_ai.py [--venv] [--host HOST] [--port PORT] [--no-deploy]

Options:
    --venv          Create and use a virtual environment
    --host HOST     Host for the MCP server (default: localhost)
    --port PORT     Port for the MCP server (default: 8000)
    --no-deploy     Skip deployment of the plugin to GIMP
"""

import os
import sys
import argparse
import platform
import subprocess
import venv
import shutil
from pathlib import Path

def check_python_version():
    """Check if Python version is adequate."""
    python_version = sys.version_info
    min_version = (3, 8)
    
    if python_version < min_version:
        print(f"❌ Python version {python_version.major}.{python_version.minor} is not supported.")
        print(f"   Minimum required version is {min_version[0]}.{min_version[1]}")
        return False
    else:
        print(f"✅ Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
        return True

def create_virtual_environment(venv_dir):
    """Create a virtual environment for the project."""
    if os.path.exists(venv_dir):
        print(f"Virtual environment already exists at {venv_dir}")
        return True
    
    print(f"Creating virtual environment at {venv_dir}...")
    try:
        venv.create(venv_dir, with_pip=True)
        print("✅ Virtual environment created successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to create virtual environment: {e}")
        return False

def get_activate_command(venv_dir):
    """Get the command to activate the virtual environment."""
    system = platform.system()
    if system == "Windows":
        return f"{venv_dir}\\Scripts\\activate.bat"
    else:  # Unix-like (Linux, macOS)
        return f"source {venv_dir}/bin/activate"

def install_dependencies(venv_dir=None):
    """Install required dependencies."""
    # Determine pip command based on whether venv is used
    if venv_dir:
        if platform.system() == "Windows":
            pip_cmd = f"{venv_dir}\\Scripts\\pip"
        else:
            pip_cmd = f"{venv_dir}/bin/pip"
    else:
        pip_cmd = "pip"
    
    # Install backend dependencies
    backend_req = os.path.join(project_root, "backend", "requirements.txt")
    print(f"Installing backend dependencies from {backend_req}...")
    try:
        subprocess.run([pip_cmd, "install", "-r", backend_req], check=True)
        print("✅ Backend dependencies installed successfully")
    except subprocess.CalledProcessError:
        print("❌ Failed to install backend dependencies")
        return False
    
    # Install frontend dependencies
    frontend_req = os.path.join(project_root, "frontend", "requirements.txt")
    print(f"Installing frontend dependencies from {frontend_req}...")
    try:
        subprocess.run([pip_cmd, "install", "-r", frontend_req], check=True)
        print("✅ Frontend dependencies installed successfully")
    except subprocess.CalledProcessError:
        print("❌ Failed to install frontend dependencies")
        return False
    
    return True

def configure_environment(host, port, venv_dir=None):
    """Configure environment variables for the plugin and server."""
    system = platform.system()
    
    # Create .env file for server
    env_file = os.path.join(project_root, ".env")
    socket_port = port + 1876  # Use a different port for socket server, e.g., 8000 -> 9876
    
    with open(env_file, "w") as f:
        f.write(f"MCP_SERVER_HOST={host}\n")
        f.write(f"MCP_SERVER_PORT={port}\n")
        f.write(f"MCP_SOCKET_HOST={host}\n")
        f.write(f"MCP_SOCKET_PORT={socket_port}\n")
        f.write("MCP_ENABLE_AUTH=false\n")
        f.write("MCP_USE_HTTPS=false\n")
        f.write("MCP_PREFER_SOCKET=true\n")
    
    print(f"✅ Environment configuration written to: {env_file}")
    
    # Create activation scripts with environment variables
    server_url = f"http://{host}:{port}/jsonrpc"
    
    if system == "Windows":
        # Windows batch script
        script_file = os.path.join(project_root, "set_env.bat")
        with open(script_file, "w") as f:
            f.write("@echo off\n")
            if venv_dir:
                f.write(f"call {venv_dir}\\Scripts\\activate.bat\n")
            f.write(f"set MCP_SERVER_URL={server_url}\n")
            f.write(f"set MCP_SERVER_HOST={host}\n")
            f.write(f"set MCP_SERVER_PORT={port}\n")
            f.write(f"set MCP_SOCKET_HOST={host}\n")
            f.write(f"set MCP_SOCKET_PORT={socket_port}\n")
            f.write("set MCP_PREFER_SOCKET=true\n")
            # Add command to start the server
            f.write("echo Environment variables set for GIMP AI Integration\n")
            f.write("echo To start the MCP servers, run:\n")
            f.write(f"echo   python {os.path.join(project_root, 'backend', 'server', 'app.py')}\n")
            f.write(f"echo   python {os.path.join(project_root, 'backend', 'server', 'socket_server.py')}\n")
    else:
        # Unix shell script
        script_file = os.path.join(project_root, "set_env.sh")
        with open(script_file, "w") as f:
            f.write("#!/bin/bash\n")
            if venv_dir:
                f.write(f"source {venv_dir}/bin/activate\n")
            f.write(f"export MCP_SERVER_URL={server_url}\n")
            f.write(f"export MCP_SERVER_HOST={host}\n")
            f.write(f"export MCP_SERVER_PORT={port}\n")
            f.write(f"export MCP_SOCKET_HOST={host}\n")
            f.write(f"export MCP_SOCKET_PORT={socket_port}\n")
            f.write("export MCP_PREFER_SOCKET=true\n")
            # Add command to start the server
            f.write("echo \"Environment variables set for GIMP AI Integration\"\n")
            f.write("echo \"To start the MCP servers, run:\"\n")
            f.write(f"echo \"  {os.path.join(project_root, 'start_gimp_ai.sh')}\"\n")
        os.chmod(script_file, 0o755)
        
        # Create the startup script
        start_script = os.path.join(project_root, "start_gimp_ai.sh")
        with open(start_script, "w") as f:
            f.write("#!/bin/bash\n")
            f.write("# start_gimp_ai.sh\n")
            f.write("# Script to start the GIMP AI Integration server(s)\n\n")
            
            f.write("# Get directory where this script is located\n")
            f.write("SCRIPT_DIR=\"$( cd \"$( dirname \"${BASH_SOURCE[0]}\" )\" && pwd )\"\n\n")
            
            f.write("# Activate virtual environment if it exists\n")
            f.write("if [ -d \"$SCRIPT_DIR/venv\" ]; then\n")
            f.write("    source \"$SCRIPT_DIR/venv/bin/activate\"\n")
            f.write("    echo \"✅ Virtual environment activated\"\n")
            f.write("else\n")
            f.write("    echo \"⚠️ Virtual environment not found. Using system Python.\"\n")
            f.write("fi\n\n")
            
            f.write("# Set environment variables\n")
            f.write(f"export MCP_SERVER_URL={server_url}\n")
            f.write(f"export MCP_SERVER_HOST={host}\n")
            f.write(f"export MCP_SERVER_PORT={port}\n")
            f.write(f"export MCP_SOCKET_HOST={host}\n")
            f.write(f"export MCP_SOCKET_PORT={socket_port}\n")
            f.write("export MCP_PREFER_SOCKET=true\n\n")
            
            f.write("echo \"Starting HTTP JSON-RPC server on $MCP_SERVER_HOST:$MCP_SERVER_PORT...\"\n")
            f.write("python \"$SCRIPT_DIR/backend/server/app.py\" > http_server.log 2>&1 &\n")
            f.write("HTTP_PID=$!\n")
            f.write("echo \"✅ HTTP server started (PID: $HTTP_PID)\"\n\n")
            
            f.write("echo \"Starting Socket JSON-RPC server on $MCP_SOCKET_HOST:$MCP_SOCKET_PORT...\"\n")
            f.write("python \"$SCRIPT_DIR/backend/server/socket_server.py\" > socket_server.log 2>&1 &\n")
            f.write("SOCKET_PID=$!\n")
            f.write("echo \"✅ Socket server started (PID: $SOCKET_PID)\"\n\n")
            
            f.write("echo \"\"\n")
            f.write("echo \"Both servers are now running.\"\n")
            f.write("echo \"To test the connection from GIMP, launch GIMP and select:\"\n")
            f.write("echo \"  Filters > AI Tools > Hello World\"\n")
            f.write("echo \"\"\n")
            f.write("echo \"Press Ctrl+C to stop all servers.\"\n")
            f.write("echo \"\"\n\n")
            
            f.write("# Wait for Ctrl+C\n")
            f.write("trap \"echo 'Stopping servers...'; kill $HTTP_PID $SOCKET_PID 2>/dev/null; exit 0\" INT TERM\n")
            f.write("wait $HTTP_PID\n")
        os.chmod(start_script, 0o755)
    
    print(f"✅ Environment script created: {script_file}")
    return True

def deploy_plugin():
    """Deploy the plugin to GIMP."""
    deploy_script = os.path.join(project_root, "scripts", "deploy.py")
    print("Deploying plugin to GIMP...")
    try:
        # Make both plugin main files executable before deployment
        plugin_main_2_10 = os.path.join(project_root, "frontend", "gimp_plugin", "plugin_main.py")
        plugin_main_3_0 = os.path.join(project_root, "frontend", "gimp_plugin", "plugin_main_gimp3.py")
        
        if os.path.exists(plugin_main_2_10) and platform.system() != "Windows":
            os.chmod(plugin_main_2_10, 0o755)
            print(f"✅ Made {plugin_main_2_10} executable")
            
        if os.path.exists(plugin_main_3_0) and platform.system() != "Windows":
            os.chmod(plugin_main_3_0, 0o755)
            print(f"✅ Made {plugin_main_3_0} executable")
        
        # Run the deployment script
        subprocess.run([sys.executable, deploy_script], check=True)
        print("✅ Plugin deployed successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to deploy plugin: {e}")
        return False

def print_final_instructions(host, port, venv_dir=None):
    """Print final instructions for using the plugin and server."""
    server_script = os.path.join(project_root, "backend", "server", "app.py")
    activate_cmd = get_activate_command(venv_dir) if venv_dir else ""
    
    print("\n" + "=" * 60)
    print("GIMP AI Integration - Setup Complete")
    print("=" * 60)
    print("\nTo use the plugin:")
    
    if venv_dir:
        print(f"1. Activate the virtual environment:")
        print(f"   {activate_cmd}")
    
    print(f"2. Set the environment variables:")
    if platform.system() == "Windows":
        print(f"   {os.path.join(project_root, 'set_env.bat')}")
    else:
        print(f"   source {os.path.join(project_root, 'set_env.sh')}")
    
    print(f"3. Start the MCP server:")
    print(f"   python {server_script}")
    
    print(f"4. Launch GIMP and access the AI tools under 'Filters > AI Tools'")
    
    print("\nNotes:")
    print("- The server must be running for the plugin to work")
    print("- If you encounter any issues, check the error messages in both GIMP and the server terminal")
    print("- Use the 'Hello World' option in the AI Tools menu to test the connection")
    
    print("\nFor more information, see the documentation in the docs/ directory.")
    print("=" * 60)

# Main execution
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Setup GIMP AI Integration")
    parser.add_argument("--venv", action="store_true", help="Create and use a virtual environment")
    parser.add_argument("--host", default="localhost", help="Server host (default: localhost)")
    parser.add_argument("--port", type=int, default=8000, help="Server port (default: 8000)")
    parser.add_argument("--no-deploy", action="store_true", help="Skip deployment of the plugin to GIMP")
    
    args = parser.parse_args()
    
    # Get project root
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    print("GIMP AI Integration - Setup")
    print("=" * 40)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Create virtual environment if requested
    venv_dir = None
    if args.venv:
        venv_dir = os.path.join(project_root, "venv")
        if not create_virtual_environment(venv_dir):
            sys.exit(1)
    
    # Install dependencies
    if not install_dependencies(venv_dir):
        sys.exit(1)
    
    # Configure environment
    if not configure_environment(args.host, args.port, venv_dir):
        sys.exit(1)
    
    # Deploy plugin
    if not args.no_deploy:
        if not deploy_plugin():
            print("Warning: Plugin deployment failed, but setup will continue.")
    
    # Print final instructions
    print_final_instructions(args.host, args.port, venv_dir)
    
    sys.exit(0)
