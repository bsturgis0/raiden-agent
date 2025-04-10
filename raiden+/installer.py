import os
import sys
import shutil
import PyInstaller.__main__
from pathlib import Path

def build_installer():
    """Build the Raiden+ installer"""
    print("Building Raiden+ Installer...")
    
    project_root = Path(__file__).parent.resolve()
    
    # Clean previous builds
    for path in ["build", "dist"]:
        build_path = project_root / path
        if build_path.exists():
            shutil.rmtree(build_path)
    
    # Collect all required files
    resources = [
        ('frontend/*', 'frontend'),
        ('tools/*', 'tools'),
        ('.env.template', '.'),  # Template for configuration
        ('README.md', '.'),
    ]
    
    PyInstaller.__main__.run([
        'desktop.py',                        # Main script
        '--name=RaidenSetup',               # Output name
        '--onefile',                        # Single executable
        '--windowed',                       # No console window
        '--icon=frontend/raiden.ico',       # Application icon
        '--add-data=frontend:frontend',     # Include frontend
        '--add-data=tools:tools',          # Include tools
        '--hidden-import=uvicorn',
        '--hidden-import=fastapi',
        '--hidden-import=pywebview',
        '--hidden-import=keyring',
        '--hidden-import=pystray',
        '--hidden-import=PIL',
        '--collect-all=langchain',
        '--collect-all=chromadb',
        '--noconfirm',                      # Overwrite without asking
        '--clean',                          # Clean cache
    ])
    
    print("\nBuild complete! You can find RaidenSetup.exe in the 'dist' folder")

if __name__ == '__main__':
    build_installer()
