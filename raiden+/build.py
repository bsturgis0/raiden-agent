import os
import sys
import PyInstaller.__main__
import shutil
from pathlib import Path

def get_python_lib_path():
    """Get the Python library path in a cross-platform way"""
    if sys.platform.startswith('win'):
        return None  # Windows doesn't need this
    
    possible_paths = [
        f"{sys.prefix}/lib/libpython{sys.version_info.major}.{sys.version_info.minor}.so.1.0",
        f"{sys.prefix}/lib/libpython{sys.version_info.major}.{sys.version_info.minor}m.so.1.0",
        f"{sys.prefix}/lib/x86_64-linux-gnu/libpython{sys.version_info.major}.{sys.version_info.minor}.so.1.0",
    ]
    
    for path in possible_paths:
        if Path(path).exists():
            return path
    return None

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
        '--noconfirm',
    ]

    # Add Python library path if found
    python_lib = get_python_lib_path()
    if python_lib:
        args.append(f'--python-library={python_lib}')
    
    # Platform-specific arguments
    if sys.platform.startswith('win'):
        args.extend(['--windowed', '--icon=frontend/raiden.ico'])
    elif sys.platform.startswith('linux'):
        # Check common locations for GTK libraries
        gtk_paths = [
            '/usr/lib/x86_64-linux-gnu',
            '/usr/lib64',
            '/usr/lib'
        ]
        
        for base_path in gtk_paths:
            gtk_lib = Path(base_path) / 'libgtk-3.so.0'
            gdk_lib = Path(base_path) / 'libgdk-3.so.0'
            
            if gtk_lib.exists() and gdk_lib.exists():
                args.extend([
                    f'--add-binary={gtk_lib}:.',
                    f'--add-binary={gdk_lib}:.'
                ])
                break
    
    PyInstaller.__main__.run(args)
    
    print("\nBuild complete! Find the executable in the 'dist' folder")

if __name__ == '__main__':
    build_exe()
