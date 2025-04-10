#!/usr/bin/env python
"""
Deployment script for GIMP AI Integration.

This script helps deploy the GIMP AI Integration plugin and server on different platforms.
It performs the following tasks:
1. Checks the environment for required dependencies
2. Installs the plugin to the correct GIMP plugins directory
3. Configures environment variables
4. Provides instructions for starting the server
"""
import os
import sys
import platform
import shutil
import subprocess
import argparse
from pathlib import Path

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent.absolute()

def check_requirements():
    """Check if all requirements are installed."""
    print("Checking environment requirements...")
    
    # Run the environment check script
    check_script = os.path.join(PROJECT_ROOT, "scripts", "check_environment.py")
    result = subprocess.run([sys.executable, check_script], capture_output=True, text=True)
    
    # Print the output
    print(result.stdout)
    
    # Return True if the check passed, False otherwise
    return result.returncode == 0

def detect_gimp_version():
    """Detect the installed GIMP version."""
    system = platform.system()
    
    # Check for GIMP 3.0 first
    if system == "Windows":
        # Windows common paths for GIMP 3.0
        gimp3_paths = [
            r"C:\\Program Files\\GIMP 3\\bin\\gimp-3.0.exe",
            r"C:\\Program Files (x86)\\GIMP 3\\bin\\gimp-3.0.exe"
        ]
        for path in gimp3_paths:
            if os.path.exists(path):
                return "3.0"
                
    elif system == "Darwin":  # macOS
        # macOS common paths for GIMP 3.0
        gimp3_paths = [
            "/Applications/GIMP-3.0.app",
            "/Applications/GIMP.app"  # GIMP 3.0 could be installed as 'GIMP.app'
        ]
        for path in gimp3_paths:
            if os.path.exists(path):
                return "3.0"
                
    else:  # Linux
        # Try to find GIMP 3.0 in PATH
        if shutil.which("gimp-3.0"):
            return "3.0"
            
    # If GIMP 3.0 not found, check for GIMP 2.10
    if system == "Windows":
        gimp2_paths = [
            r"C:\\Program Files\\GIMP 2\\bin\\gimp-2.10.exe",
            r"C:\\Program Files (x86)\\GIMP 2\\bin\\gimp-2.10.exe"
        ]
        for path in gimp2_paths:
            if os.path.exists(path):
                return "2.10"
                
    elif system == "Darwin":  # macOS
        gimp2_paths = [
            "/Applications/GIMP-2.10.app"
        ]
        for path in gimp2_paths:
            if os.path.exists(path):
                return "2.10"
                
    else:  # Linux
        if shutil.which("gimp-2.10") or shutil.which("gimp"):
            return "2.10"
    
    # Default to 2.10 if no version found
    print("Warning: Could not detect GIMP version. Defaulting to 2.10.")
    return "2.10"

def install_plugin():
    """Install the plugin to the GIMP plugins directory."""
    system = platform.system()
    home = os.path.expanduser("~")
    
    # Detect GIMP version
    gimp_version = detect_gimp_version()
    print(f"Detected GIMP version: {gimp_version}")
    
    # Determine the GIMP plugin directory based on the platform and version
    if gimp_version == "3.0":
        if system == "Windows":
            plugin_dir = os.path.join(home, "AppData", "Roaming", "GIMP", "3.0", "plug-ins")
        elif system == "Darwin":  # macOS
            plugin_dir = os.path.join(home, "Library", "Application Support", "GIMP", "3.0", "plug-ins")
            # Also check alternative macOS GIMP 3.0 path
            alt_plugin_dir = "/Applications/GIMP-3.0.app/Contents/Resources/lib/gimp/3.0/plug-ins"
            if os.path.exists(os.path.dirname(alt_plugin_dir)):
                plugin_dir = alt_plugin_dir
        else:  # Linux
            plugin_dir = os.path.join(home, ".config", "GIMP", "3.0", "plug-ins")
    else:  # Default to 2.10
        if system == "Windows":
            plugin_dir = os.path.join(home, "AppData", "Roaming", "GIMP", "2.10", "plug-ins")
        elif system == "Darwin":  # macOS
            plugin_dir = os.path.join(home, "Library", "Application Support", "GIMP", "2.10", "plug-ins")
        else:  # Linux
            plugin_dir = os.path.join(home, ".config", "GIMP", "2.10", "plug-ins")
    
    # Create the plugin directory if it doesn't exist
    os.makedirs(plugin_dir, exist_ok=True)
    
    # Path to the plugin source directory
    plugin_src = os.path.join(PROJECT_ROOT, "frontend", "gimp_plugin")
    
    # Target directory for the plugin
    plugin_dest = os.path.join(plugin_dir, "gimp_ai_integration")
    
    print(f"Installing plugin to: {plugin_dest}")
    
    # Remove the plugin directory if it already exists
    if os.path.exists(plugin_dest):
        shutil.rmtree(plugin_dest)
    
    # Copy the plugin files
    shutil.copytree(plugin_src, plugin_dest)
    
    # Make the appropriate main plugin file executable on Unix-like systems
    if system != "Windows":
        if gimp_version == "3.0":
            plugin_main = os.path.join(plugin_dest, "plugin_main_gimp3.py")
            if os.path.exists(plugin_main):
                os.chmod(plugin_main, 0o755)
                # Create a symlink to make it more discoverable
                plugin_main_link = os.path.join(plugin_dest, "plugin_main.py")
                if not os.path.exists(plugin_main_link):
                    os.symlink(plugin_main, plugin_main_link)
        else:
            plugin_main = os.path.join(plugin_dest, "plugin_main.py")
            os.chmod(plugin_main, 0o755)
    
    print(f"Plugin installed successfully for GIMP {gimp_version}.")
    return True

def configure_environment(server_host, server_port, api_key=None, use_https=False):
    """Configure environment variables for the plugin and server."""
    system = platform.system()
    env_file = os.path.join(PROJECT_ROOT, ".env")
    
    # Create or update the .env file
    with open(env_file, "w") as f:
        f.write(f"MCP_SERVER_HOST={server_host}\n")
        f.write(f"MCP_SERVER_PORT={server_port}\n")
        
        if api_key:
            f.write(f"MCP_ENABLE_AUTH=true\n")
            f.write(f"MCP_API_KEY_USER={api_key}\n")
        else:
            f.write("MCP_ENABLE_AUTH=false\n")
        
        if use_https:
            f.write("MCP_USE_HTTPS=true\n")
            f.write(f"MCP_SSL_CERTFILE={os.path.join(PROJECT_ROOT, 'cert.pem')}\n")
            f.write(f"MCP_SSL_KEYFILE={os.path.join(PROJECT_ROOT, 'key.pem')}\n")
        else:
            f.write("MCP_USE_HTTPS=false\n")
    
    print(f"Environment configuration written to: {env_file}")
    
    # Create a script to set environment variables for the plugin
    if system == "Windows":
        script_file = os.path.join(PROJECT_ROOT, "set_env.bat")
        with open(script_file, "w") as f:
            f.write(f"@echo off\n")
            f.write(f"set MCP_SERVER_URL=http{'s' if use_https else ''}://{server_host}:{server_port}/jsonrpc\n")
            if api_key:
                f.write(f"set MCP_API_KEY={api_key}\n")
    else:
        script_file = os.path.join(PROJECT_ROOT, "set_env.sh")
        with open(script_file, "w") as f:
            f.write("#!/bin/bash\n")
            f.write(f"export MCP_SERVER_URL=http{'s' if use_https else ''}://{server_host}:{server_port}/jsonrpc\n")
            if api_key:
                f.write(f"export MCP_API_KEY={api_key}\n")
        os.chmod(script_file, 0o755)
    
    print(f"Environment script created: {script_file}")
    print(f"Run this script before launching GIMP to set the required environment variables.")
    
    return True

def generate_self_signed_cert():
    """Generate a self-signed SSL certificate for HTTPS."""
    # Check if openssl is available
    if shutil.which("openssl") is None:
        print("Error: openssl is not installed. Cannot generate self-signed certificate.")
        return False
    
    cert_file = os.path.join(PROJECT_ROOT, "cert.pem")
    key_file = os.path.join(PROJECT_ROOT, "key.pem")
    
    # Generate a self-signed certificate
    cmd = [
        "openssl", "req", "-x509", "-newkey", "rsa:4096", "-keyout", key_file,
        "-out", cert_file, "-days", "365", "-nodes", "-subj",
        "/C=US/ST=State/L=City/O=Organization/CN=localhost"
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print(f"Self-signed certificate generated: {cert_file}, {key_file}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error generating self-signed certificate: {e}")
        return False

def print_final_instructions():
    """Print final instructions for using the plugin and server."""
    server_script = os.path.join(PROJECT_ROOT, "backend", "server", "app.py")
    
    print("\n" + "=" * 60)
    print("GIMP AI Integration - Installation Complete")
    print("=" * 60)
    print("\nTo use the plugin:")
    print(f"1. Set the environment variables by running the script in the project root directory")
    print(f"2. Start the MCP server with: python {server_script}")
    print(f"3. Launch GIMP and access the AI tools under 'Filters > AI Tools'")
    print("\nFor more information, see the documentation in the docs/ directory.")
    print("=" * 60)

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Deploy GIMP AI Integration")
    parser.add_argument("--host", default="127.0.0.1", help="Server host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Server port (default: 8000)")
    parser.add_argument("--auth", action="store_true", help="Enable authentication")
    parser.add_argument("--https", action="store_true", help="Enable HTTPS with self-signed certificate")
    parser.add_argument("--skip-checks", action="store_true", help="Skip environment checks")
    
    args = parser.parse_args()
    
    print("GIMP AI Integration - Deployment")
    print("=" * 40)
    
    # Check requirements
    if not args.skip_checks:
        if not check_requirements():
            print("\nEnvironment check failed. Please fix the issues before continuing.")
            return 1
    
    # Generate API key if authentication is enabled
    api_key = None
    if args.auth:
        import secrets
        api_key = secrets.token_urlsafe(32)
        print(f"\nGenerated API key: {api_key}")
        print("Keep this key secure - it will be needed for plugin authentication.")
    
    # Generate self-signed certificate if HTTPS is enabled
    if args.https:
        print("\nGenerating self-signed SSL certificate...")
        if not generate_self_signed_cert():
            return 1
    
    # Install plugin
    print("\nInstalling plugin...")
    if not install_plugin():
        return 1
    
    # Configure environment
    print("\nConfiguring environment...")
    if not configure_environment(args.host, args.port, api_key, args.https):
        return 1
    
    # Print final instructions
    print_final_instructions()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
