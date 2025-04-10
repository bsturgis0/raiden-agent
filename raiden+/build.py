import PyInstaller.__main__
import shutil
from pathlib import Path

def build_exe():
    """Build Raiden+ desktop application"""
    print("Building Raiden+ Desktop Application...")
    
    # Clean previous builds
    for path in ["build", "dist"]:
        if Path(path).exists():
            shutil.rmtree(path)
    
    PyInstaller.__main__.run([
        'desktop.py',
        '--name=Raiden',
        '--windowed',  # No console window
        '--onefile',   # Single executable
        '--clean',     # Clean cache
        '--icon=frontend/raiden.ico',  # Add application icon
        '--add-data=frontend:frontend',  # Include frontend files
        '--add-data=tools:tools',       # Include tool modules
        '--add-data=.env:.env',         # Include environment file
        '--hidden-import=uvicorn',
        '--hidden-import=fastapi',
        '--hidden-import=pywebview',
        '--hidden-import=keyring',
        '--hidden-import=pystray',
        '--hidden-import=PIL.Image',
        '--collect-all=langchain',      # Include all langchain dependencies
        '--collect-all=langchain_core',
        '--collect-all=langchain_community',
        '--collect-all=chromadb',
        '--noconsole',                 # No terminal window
        '--noconfirm',                 # Overwrite existing files
    ])
    
    print("\nBuild complete! You can find Raiden.exe in the 'dist' folder")

if __name__ == '__main__':
    build_exe()
