import os
import sys
import PyInstaller.__main__
from pathlib import Path

def build_exe():
    """Build the Raiden+ executable."""
    print("Building Raiden+ Desktop Application...")
    
    # Get the absolute path to the project root
    project_root = Path(__file__).parent.resolve()
    
    PyInstaller.__main__.run([
        'desktop.py',                        # Main script
        '--name=Raiden',                     # Output exe name
        '--windowed',                        # No console window
        '--onefile',                         # Single executable
        '--icon=frontend/raiden.ico',        # Application icon
        '--add-data=frontend/*;frontend/',   # Include frontend files
        '--add-data=tools/*;tools/',         # Include tool modules
        '--distpath=dist',                   # Output directory
        '--workpath=build',                  # Build directory
        '--clean',                           # Clean build files
    ])
    
    print("\nBuild complete! You can find Raiden.exe in the 'dist' folder.")

if __name__ == '__main__':
    build_exe()
