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
        '--add-data=frontend:frontend',  # Include frontend files
        '--add-data=tools:tools',       # Include tool modules
        '--hidden-import=uvicorn',
        '--hidden-import=fastapi',
        '--hidden-import=pywebview',
        '--collect-all=langchain',      # Include all langchain dependencies
    ])
    
    print("\nBuild complete! You can find Raiden.exe in the 'dist' folder")

if __name__ == '__main__':
    build_exe()
