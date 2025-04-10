import os
import sys
import shutil
import platform
import subprocess
import PyInstaller.__main__
from pathlib import Path

def check_dependencies():
    """Check if all required system dependencies are installed"""
    system = platform.system()
    if system == "Linux":
        required_packages = [
            "libgtk-3-0",
            "libwebkit2gtk-4.0-37",
            "libglib2.0-0"
        ]
        try:
            for pkg in required_packages:
                subprocess.run(['dpkg', '-l', pkg], check=True, capture_output=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(f"Missing required dependencies. Please install: {', '.join(required_packages)}")
            return False
    return True  # Windows/Mac don't need extra checks currently

def build_installer():
    """Build the Raiden+ installer"""
    print("Building Raiden+ Installer...")
    
    if not check_dependencies():
        sys.exit(1)
    
    project_root = Path(__file__).parent.resolve()
    
    # Clean previous builds
    for path in ["build", "dist"]:
        build_path = project_root / path
        if build_path.exists():
            shutil.rmtree(build_path)
    
    # Base arguments
    args = [
        'desktop.py',                        # Main script
        '--name=RaidenSetup',               # Output name
        '--onefile',                        # Single executable
        '--windowed',                       # No console window
        '--add-data=frontend:frontend',     # Include frontend
        '--add-data=tools:tools',          # Include tools
        '--hidden-import=uvicorn',
        '--hidden-import=fastapi',
        '--hidden-import=pywebview',
        '--hidden-import=keyring',
        '--hidden-import=pystray',
        '--hidden-import=PIL',
        '--hidden-import=langchain_core',
        '--hidden-import=chromadb',
        '--hidden-import=pysqlite3',
        '--collect-submodules=langchain',
        '--collect-submodules=chromadb',
        '--collect-data=langchain',
        '--collect-data=chromadb',
        '--noconfirm',                      # Overwrite without asking
        '--clean',                          # Clean cache
    ]

    # Platform-specific arguments
    system = platform.system()
    if system == "Windows":
        args.append('--icon=frontend/raiden.ico')
    elif system == "Linux":
        gtk_paths = ['/usr/lib/x86_64-linux-gnu', '/usr/lib64', '/usr/lib']
        for base_path in gtk_paths:
            gtk_lib = Path(base_path) / 'libgtk-3.so.0'
            gdk_lib = Path(base_path) / 'libgdk-3.so.0'
            if gtk_lib.exists() and gdk_lib.exists():
                args.extend([
                    f'--add-binary={gtk_lib}:.',
                    f'--add-binary={gdk_lib}:.'
                ])
                break
    elif system == "Darwin":  # macOS
        args.extend([
            '--icon=frontend/raiden.icns',
            '--osx-bundle-identifier=com.raiden.plus'
        ])

    try:
        PyInstaller.__main__.run(args)
        
        # Create .env template in dist
        env_template = project_root / "dist" / ".env.template"
        env_template.write_text("""GOOGLE_API_KEY=your_google_api_key
GROQ_API_KEY=your_groq_api_key
TAVILY_API_KEY=your_tavily_api_key
BRAVE_SEARCH_API_KEY=your_brave_api_key
GITHUB_TOKEN=your_github_token
AWS_ACCESS_KEY_ID=your_aws_key_id
AWS_SECRET_ACCESS_KEY=your_aws_secret
GEMINI_API_KEY=your_gemini_api_key""")
        
        print(f"\nBuild complete! You can find RaidenSetup{'.exe' if system == 'Windows' else ''} in the 'dist' folder")
        print("Don't forget to rename .env.template to .env and configure your API keys!")
        
    except Exception as e:
        print(f"Error during build: {e}")
        sys.exit(1)

if __name__ == '__main__':
    build_installer()
