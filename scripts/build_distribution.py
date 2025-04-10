#!/usr/bin/env python
"""
Build distribution packages for GIMP AI Integration.

This script builds wheel packages and creates platform-specific installers
for Windows, macOS, and Linux.
"""
import os
import sys
import platform
import subprocess
import shutil
import argparse
from pathlib import Path

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent.absolute()

def run_command(cmd, cwd=None):
    """Run a command and return its output."""
    print(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, cwd=cwd or PROJECT_ROOT, check=True, 
                               capture_output=True, text=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Command failed with error: {e}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        sys.exit(1)

def build_wheel():
    """Build wheel packages."""
    print("Building wheel packages...")
    
    # Clean up previous builds
    dist_dir = os.path.join(PROJECT_ROOT, "dist")
    if os.path.exists(dist_dir):
        shutil.rmtree(dist_dir)
    
    # Build the wheel package
    run_command([sys.executable, "-m", "pip", "install", "--upgrade", "build", "wheel", "setuptools"])
    run_command([sys.executable, "-m", "build", "--wheel"])
    
    print(f"Wheel package built successfully. See the ./dist directory.")
    return True

def build_standalone_installer():
    """Build standalone installer using PyInstaller."""
    print("Building standalone installer...")
    
    # Check if PyInstaller is installed
    try:
        import PyInstaller
    except ImportError:
        run_command([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    # Path to the spec file for PyInstaller
    spec_file = os.path.join(PROJECT_ROOT, "scripts", "installer.spec")
    
    # Create a PyInstaller spec file if it doesn't exist
    if not os.path.exists(spec_file):
        # Create a basic spec file
        with open(spec_file, "w") as f:
            f.write("""
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['../backend/server/app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('../frontend/gimp_plugin', 'frontend/gimp_plugin'),
        ('../docs', 'docs'),
        ('../scripts', 'scripts'),
    ],
    hiddenimports=[
        'uvicorn.logging',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'uvicorn.lifespan.off',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='gimp-ai-server',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

installer = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='gimp-ai-installer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='gimp-ai-server',
)
            """)
    
    # Build the standalone installer
    run_command(["pyinstaller", "--clean", spec_file])
    
    # Create an installer script based on the platform
    if platform.system() == "Windows":
        create_windows_installer()
    elif platform.system() == "Darwin":
        create_macos_installer()
    else:
        create_linux_installer()
    
    print(f"Standalone installer built successfully. See the ./dist directory.")
    return True

def create_windows_installer():
    """Create a Windows installer using NSIS or similar."""
    # Implementation details would depend on the specific installer technology
    # This is a simplified placeholder
    install_script = os.path.join(PROJECT_ROOT, "scripts", "windows_install.bat")
    
    with open(install_script, "w") as f:
        f.write("""@echo off
echo Installing GIMP AI Integration...

:: Create the destination directory
set INSTALL_DIR=%APPDATA%\\GIMP\\2.10\\plug-ins\\gimp_ai_integration
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

:: Copy the files
xcopy /E /I /Y "frontend\\gimp_plugin\\*" "%INSTALL_DIR%"

:: Create a shortcut for the server
set SERVER_DIR=%LOCALAPPDATA%\\GimpAIServer
if not exist "%SERVER_DIR%" mkdir "%SERVER_DIR%"
xcopy /E /I /Y "dist\\gimp-ai-server\\*" "%SERVER_DIR%"

:: Create a desktop shortcut for the server
set SHORTCUT=%USERPROFILE%\\Desktop\\GIMP AI Server.lnk
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%SHORTCUT%'); $s.TargetPath = '%SERVER_DIR%\\gimp-ai-server.exe'; $s.Save()"

echo Installation complete!
echo Start the server by running the "GIMP AI Server" shortcut on your desktop
pause
""")
    
    print(f"Windows installer script created: {install_script}")
    return True

def create_macos_installer():
    """Create a macOS installer package."""
    # This is a simplified placeholder
    install_script = os.path.join(PROJECT_ROOT, "scripts", "macos_install.sh")
    
    with open(install_script, "w") as f:
        f.write("""#!/bin/bash
echo "Installing GIMP AI Integration..."

# Create the destination directory
INSTALL_DIR="$HOME/Library/Application Support/GIMP/2.10/plug-ins/gimp_ai_integration"
mkdir -p "$INSTALL_DIR"

# Copy the files
cp -R frontend/gimp_plugin/* "$INSTALL_DIR/"

# Create a directory for the server
SERVER_DIR="$HOME/Applications/GimpAIServer"
mkdir -p "$SERVER_DIR"
cp -R dist/gimp-ai-server/* "$SERVER_DIR/"

# Create an application launcher
cat > "$HOME/Applications/GIMP AI Server.command" << 'EOL'
#!/bin/bash
cd "$HOME/Applications/GimpAIServer"
./gimp-ai-server
EOL

chmod +x "$HOME/Applications/GIMP AI Server.command"

echo "Installation complete!"
echo "Start the server by running the 'GIMP AI Server' application in your Applications folder"
""")
    
    os.chmod(install_script, 0o755)
    print(f"macOS installer script created: {install_script}")
    return True

def create_linux_installer():
    """Create a Linux installer script."""
    # This is a simplified placeholder
    install_script = os.path.join(PROJECT_ROOT, "scripts", "linux_install.sh")
    
    with open(install_script, "w") as f:
        f.write("""#!/bin/bash
echo "Installing GIMP AI Integration..."

# Create the destination directory
INSTALL_DIR="$HOME/.config/GIMP/2.10/plug-ins/gimp_ai_integration"
mkdir -p "$INSTALL_DIR"

# Copy the files
cp -R frontend/gimp_plugin/* "$INSTALL_DIR/"

# Create a directory for the server
SERVER_DIR="$HOME/.local/share/GimpAIServer"
mkdir -p "$SERVER_DIR"
cp -R dist/gimp-ai-server/* "$SERVER_DIR/"

# Create a desktop entry
cat > "$HOME/.local/share/applications/gimp-ai-server.desktop" << 'EOL'
[Desktop Entry]
Name=GIMP AI Server
Exec=$HOME/.local/share/GimpAIServer/gimp-ai-server
Icon=gimp
Type=Application
Categories=Graphics;
Comment=MCP Server for GIMP AI Integration
EOL

echo "Installation complete!"
echo "Start the server by running 'GIMP AI Server' from your applications menu"
echo "or by running '$HOME/.local/share/GimpAIServer/gimp-ai-server'"
""")
    
    os.chmod(install_script, 0o755)
    print(f"Linux installer script created: {install_script}")
    return True

def create_release_notes():
    """Create release notes for the current version."""
    version = "0.1.0-beta"  # Beta version
    release_notes_file = os.path.join(PROJECT_ROOT, "RELEASE_NOTES.md")
    
    with open(release_notes_file, "w") as f:
        f.write(f"""# Release Notes - Version {version}

## GIMP AI Integration Beta Release

This is the first beta release of the GIMP AI Integration project, which brings advanced AI capabilities to GIMP through a Python plugin and Model Context Protocol (MCP) server.

### Features

- **Background Removal**: Automatically remove backgrounds from images using AI
- **Inpainting**: Fill in selected areas with AI-generated content
- **Style Transfer**: Apply artistic styles to images
- **Image Upscaling**: Enhance image resolution with AI

### Installation

For detailed installation instructions, please see the [User Guide](docs/user_guide.md).

### Known Issues

- The server requires a significant amount of memory when processing large images
- Style transfer can be slow on systems without GPU acceleration
- Upscaling at 8x may produce artifacts on complex images

### Feedback and Bug Reports

Please report any issues or provide feedback through:
- GitHub Issues: https://github.com/yourusername/gimp-ai-integration/issues
- Email: example@example.com

### System Requirements

- GIMP 2.10 or later
- Python 3.8 or later
- At least 8GB RAM
- NVIDIA GPU with CUDA support (recommended but not required)

### Acknowledgements

We would like to thank the open-source community and the contributors to the AI models used in this project.
""")
    
    print(f"Release notes created: {release_notes_file}")
    return True

def package_full_distribution():
    """Create a full distribution package with all components."""
    # Build the wheel package
    build_wheel()
    
    # Build the standalone installer
    build_standalone_installer()
    
    # Create release notes
    create_release_notes()
    
    # Create a zip archive of everything
    dist_dir = os.path.join(PROJECT_ROOT, "dist")
    system_name = platform.system().lower()
    archive_name = f"gimp-ai-integration-0.1.0-beta-{system_name}"
    
    # Create distribution directory if it doesn't exist
    os.makedirs(dist_dir, exist_ok=True)
    
    # Determine the archive format based on the platform
    if platform.system() == "Windows":
        archive_format = "zip"
        archive_file = os.path.join(dist_dir, f"{archive_name}.zip")
        # Create a zip archive
        shutil.make_archive(os.path.join(dist_dir, archive_name), "zip", PROJECT_ROOT)
    else:
        archive_format = "gztar"
        archive_file = os.path.join(dist_dir, f"{archive_name}.tar.gz")
        # Create a tar.gz archive
        shutil.make_archive(os.path.join(dist_dir, archive_name), "gztar", PROJECT_ROOT)
    
    print(f"Distribution package created: {archive_file}")
    return True

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Build distribution packages for GIMP AI Integration")
    parser.add_argument("--wheel", action="store_true", help="Build wheel package only")
    parser.add_argument("--installer", action="store_true", help="Build standalone installer only")
    parser.add_argument("--notes", action="store_true", help="Create release notes only")
    parser.add_argument("--all", action="store_true", help="Build all distribution packages")
    
    args = parser.parse_args()
    
    # If no options are specified, build everything
    if not (args.wheel or args.installer or args.notes or args.all):
        args.all = True
    
    if args.wheel or args.all:
        build_wheel()
    
    if args.installer or args.all:
        build_standalone_installer()
    
    if args.notes or args.all:
        create_release_notes()
    
    if args.all:
        package_full_distribution()
    
    print("Build process completed successfully!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
