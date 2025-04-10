import os
import sys
import webview
import threading
import uvicorn
from pathlib import Path
from app import app, WORKSPACE_DIR

# Ensure proper base directory when packaged
if getattr(sys, 'frozen', False):
    base_dir = sys._MEIPASS
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))

# Configure workspace directory for desktop mode
desktop_workspace = Path.home() / "RaidenWorkspace"
WORKSPACE_DIR = desktop_workspace
WORKSPACE_DIR.mkdir(exist_ok=True)

def start_server():
    """Start the FastAPI server"""
    uvicorn.run(app, host="127.0.0.1", port=5000)

def main():
    # Start the server in a separate thread
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    # Create desktop window
    window = webview.create_window(
        'Raiden Desktop',
        url='http://127.0.0.1:5000/frontend/index.html',
        width=1200,
        height=800,
        resizable=True,
        min_size=(800, 600)
    )
    
    # Start the desktop application
    webview.start(debug=True)

if __name__ == '__main__':
    main()
