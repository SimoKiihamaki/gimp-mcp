#!/usr/bin/env python
"""
Environment Checker for GIMP AI Integration

This script checks if the current environment meets all the requirements
for running the GIMP AI Integration addon and MCP server.
"""
import os
import sys
import platform
import importlib.util
import subprocess
import shutil

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

def check_package_installed(package_name):
    """Check if a Python package is installed."""
    try:
        spec = importlib.util.find_spec(package_name)
        if spec is None:
            print(f"❌ Package {package_name} is not installed.")
            return False
        
        # Try to import the package to ensure it's working
        __import__(package_name)
        print(f"✅ Package {package_name} is installed.")
        return True
    except ImportError as e:
        print(f"❌ Package {package_name} is installed but has import issues: {e}")
        return False

def check_gimp_installation():
    """Check if GIMP is installed."""
    system = platform.system()
    
    if system == "Windows":
        # Check common installation paths on Windows
        gimp_paths = [
            r"C:\\Program Files\\GIMP 2\\bin\\gimp-2.10.exe",
            r"C:\\Program Files (x86)\\GIMP 2\\bin\\gimp-2.10.exe"
        ]
        for path in gimp_paths:
            if os.path.exists(path):
                print(f"✅ GIMP found at: {path}")
                return True
                
        # Try to find GIMP in PATH
        if shutil.which("gimp-2.10.exe") or shutil.which("gimp.exe"):
            print("✅ GIMP found in PATH")
            return True
            
    elif system == "Darwin":  # macOS
        # Check common installation paths on macOS
        gimp_paths = [
            "/Applications/GIMP.app",
            "/Applications/GIMP-2.10.app"
        ]
        for path in gimp_paths:
            if os.path.exists(path):
                print(f"✅ GIMP found at: {path}")
                return True
                
    else:  # Linux
        # Try to find GIMP in PATH
        if shutil.which("gimp") or shutil.which("gimp-2.10"):
            print("✅ GIMP found in PATH")
            return True
            
        # Check common installation paths on Linux
        gimp_paths = [
            "/usr/bin/gimp",
            "/usr/bin/gimp-2.10",
            "/usr/local/bin/gimp"
        ]
        for path in gimp_paths:
            if os.path.exists(path):
                print(f"✅ GIMP found at: {path}")
                return True
    
    print("❌ GIMP is not found. Please install GIMP 2.10 or later.")
    return False

def check_gpu_availability():
    """Check if GPU is available for PyTorch."""
    try:
        import torch
        
        if torch.cuda.is_available():
            device_count = torch.cuda.device_count()
            device_name = torch.cuda.get_device_name(0) if device_count > 0 else "Unknown"
            print(f"✅ GPU is available: {device_name} (Devices: {device_count})")
            return True
        else:
            print("⚠️ GPU is not available. AI operations will use CPU only (slower).")
            return False
    except ImportError:
        print("⚠️ PyTorch is not installed. Cannot check GPU availability.")
        return False
    except Exception as e:
        print(f"⚠️ Error checking GPU availability: {e}")
        return False

def check_gimp_plugin_directory():
    """Check if the GIMP plugin directory exists and is writable."""
    system = platform.system()
    home = os.path.expanduser("~")
    
    if system == "Windows":
        plugin_dir = os.path.join(home, "AppData", "Roaming", "GIMP", "2.10", "plug-ins")
    elif system == "Darwin":  # macOS
        plugin_dir = os.path.join(home, "Library", "Application Support", "GIMP", "2.10", "plug-ins")
    else:  # Linux
        plugin_dir = os.path.join(home, ".config", "GIMP", "2.10", "plug-ins")
    
    if os.path.exists(plugin_dir):
        if os.access(plugin_dir, os.W_OK):
            print(f"✅ GIMP plugin directory is writable: {plugin_dir}")
            return True
        else:
            print(f"❌ GIMP plugin directory exists but is not writable: {plugin_dir}")
            return False
    else:
        print(f"❌ GIMP plugin directory does not exist: {plugin_dir}")
        print(f"   Please run GIMP at least once to create this directory.")
        return False

def check_environment_variables():
    """Check if necessary environment variables are set."""
    # Check for MCP server URL
    mcp_url = os.environ.get("MCP_SERVER_URL")
    if mcp_url:
        print(f"✅ MCP_SERVER_URL is set to: {mcp_url}")
    else:
        print("ℹ️ MCP_SERVER_URL is not set. Default value will be used: http://localhost:8000/jsonrpc")
    
    # Check for MCP server host/port
    mcp_host = os.environ.get("MCP_SERVER_HOST")
    if mcp_host:
        print(f"✅ MCP_SERVER_HOST is set to: {mcp_host}")
    else:
        print("ℹ️ MCP_SERVER_HOST is not set. Default value will be used: 127.0.0.1")
    
    mcp_port = os.environ.get("MCP_SERVER_PORT")
    if mcp_port:
        print(f"✅ MCP_SERVER_PORT is set to: {mcp_port}")
    else:
        print("ℹ️ MCP_SERVER_PORT is not set. Default value will be used: 8000")
    
    return True

def main():
    """Run all environment checks."""
    print("=" * 60)
    print(" GIMP AI Integration - Environment Check")
    print("=" * 60)
    print(f"Operating System: {platform.system()} {platform.release()}")
    print("-" * 60)
    
    # Run all checks
    checks = [
        ("Python Version", check_python_version),
        ("GIMP Installation", check_gimp_installation),
        ("GIMP Plugin Directory", check_gimp_plugin_directory),
        ("Environment Variables", check_environment_variables),
        ("GPU Availability", check_gpu_availability)
    ]
    
    required_packages = [
        "torch",
        "PIL",  # Pillow
        "numpy",
        "fastapi",
        "uvicorn",
        "requests"
    ]
    
    # Check all required packages
    print("Checking required packages:")
    all_packages_installed = True
    for package in required_packages:
        if not check_package_installed(package):
            all_packages_installed = False
    
    # Add package check to the checks list
    checks.append(("Required Packages", lambda: all_packages_installed))
    
    print("-" * 60)
    print("Summary:")
    
    all_passed = True
    for name, check_func in checks:
        result = "PASS" if check_func() else "FAIL"
        if result == "FAIL":
            all_passed = False
        print(f"  {name}: {result}")
    
    print("-" * 60)
    if all_passed:
        print("✅ All checks passed! Your environment is ready to run GIMP AI Integration.")
    else:
        print("❌ Some checks failed. Please address the issues above before running the application.")
    
    print("=" * 60)
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
