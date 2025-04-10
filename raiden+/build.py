import os
import sys
import PyInstaller.__main__
import shutil
from pathlib import Path

def build_exe():
    """Build Raiden+ desktop application with platform-specific settings"""
    print("Building Raiden+ Desktop Application...")
    
    # Clean previous builds
    for path in ["build", "dist"]:
        if Path(path).exists():
            shutil.rmtree(path)
    
    # Base arguments
    args = [
        'desktop.py',
        '--name=Raiden',
        '--clean',
        '--add-data=frontend:frontend',
        '--add-data=tools:tools',
        '--hidden-import=uvicorn',
        '--hidden-import=fastapi',
        '--hidden-import=pywebview',
        '--hidden-import=keyring',
        '--hidden-import=PIL',
        '--hidden-import=pystray',
        '--hidden-import=langchain_core',
        '--hidden-import=chromadb',
        '--hidden-import=pysqlite3',
        '--collect-submodules=langchain',
        '--collect-submodules=chromadb',
        '--collect-data=langchain',
        '--collect-data=chromadb',
        f'--python-library={sys.prefix}/lib/libpython{sys.version_info.major}.{sys.version_info.minor}.so.1.0',
        '--noconfirm',
    ]
    
    # Platform-specific arguments
    if sys.platform.startswith('win'):
        args.extend(['--windowed', '--icon=frontend/raiden.ico'])
    elif sys.platform.startswith('linux'):
        args.extend([
            '--add-binary=/usr/lib/x86_64-linux-gnu/libgtk-3.so.0:.',
            '--add-binary=/usr/lib/x86_64-linux-gnu/libgdk-3.so.0:.'
        ])
    
    PyInstaller.__main__.run(args)
    
    print("\nBuild complete! Find the executable in the 'dist' folder")

if __name__ == '__main__':
    build_exe()
