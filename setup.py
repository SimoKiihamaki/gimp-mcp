#!/usr/bin/env python
"""
Setup script for GIMP AI Integration project.
This installs both the backend server and frontend plugin components.
"""
import os
import site
import platform
from setuptools import setup, find_packages

# Read the long description from README.md
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read the version from the __init__.py file
version = "0.1.0"

# Read requirements from requirements.txt files
with open("backend/requirements.txt", "r", encoding="utf-8") as fh:
    backend_requirements = [line.strip() for line in fh.readlines() if line.strip()]

with open("frontend/requirements.txt", "r", encoding="utf-8") as fh:
    frontend_requirements = [line.strip() for line in fh.readlines() if line.strip()]

# Combine all requirements
all_requirements = list(set(backend_requirements + frontend_requirements))

# Get the GIMP plugins directory based on the platform
def get_gimp_plugin_dir():
    home = os.path.expanduser("~")
    system = platform.system()
    
    if system == "Windows":
        return os.path.join(home, "AppData", "Roaming", "GIMP", "2.10", "plug-ins")
    elif system == "Darwin":  # macOS
        return os.path.join(home, "Library", "Application Support", "GIMP", "2.10", "plug-ins")
    else:  # Linux
        return os.path.join(home, ".config", "GIMP", "2.10", "plug-ins")

setup(
    name="gimp-ai-integration",
    version=version,
    author="GIMP AI Integration Team",
    author_email="example@example.com",
    description="AI integration for GIMP using a Model Context Protocol (MCP) server",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/gimp-ai-integration",
    project_urls={
        "Bug Tracker": "https://github.com/yourusername/gimp-ai-integration/issues",
        "Documentation": "https://github.com/yourusername/gimp-ai-integration/tree/main/docs",
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Multimedia :: Graphics :: Editors :: Raster-Based",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(include=["backend", "backend.*"]),
    python_requires=">=3.8",
    install_requires=all_requirements,
    entry_points={
        "console_scripts": [
            "gimp-ai-server=backend.server.app:main",
            "gimp-ai-deploy=scripts.deploy:main",
            "gimp-ai-check=scripts.check_environment:main",
        ],
    },
    data_files=[
        # Include the frontend plugin files
        (os.path.join(get_gimp_plugin_dir(), "gimp_ai_integration"), 
            [os.path.join(dirpath, f) 
             for dirpath, dirnames, filenames in os.walk("frontend/gimp_plugin") 
             for f in filenames]),
        
        # Include documentation
        ("share/doc/gimp-ai-integration", 
            [os.path.join(dirpath, f) 
             for dirpath, dirnames, filenames in os.walk("docs") 
             for f in filenames]),
    ],
    include_package_data=True,
    zip_safe=False,
)
