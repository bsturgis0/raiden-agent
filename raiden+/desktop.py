import os
import sys
import webview
import threading
import uvicorn
from pathlib import Path
from app import app

def get_workspace_dir():
    """Get the appropriate workspace directory for desktop mode"""
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        base_dir = Path(os.path.expanduser("~/RaidenWorkspace"))
    else:
        # Running in development
        base_dir = Path("./raiden_workspace")
    base_dir.mkdir(exist_ok=True)
    return base_dir

def start_server():
    """Start the FastAPI server"""
    uvicorn.run(app, host="127.0.0.1", port=5000)

def main():
    # Configure workspace
    os.environ["RAIDEN_WORKSPACE"] = str(get_workspace_dir())
    
    # Start server in background thread
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    # Create desktop window
    window = webview.create_window(
        'Raiden+',
        url='http://127.0.0.1:5000/frontend',
        width=1200,
        height=800,
        resizable=True,
        min_size=(800, 600)
    )
    
    webview.start(debug=True)

if __name__ == '__main__':
    main()
