import os
import sys
import webview
import threading
import keyring
import pystray
from PIL import Image
import json
from pathlib import Path
import uvicorn
from app import app

class RaidenDesktop:
    def __init__(self):
        self.window = None
        self.tray = None
        self.is_visible = True
        self.workspace_dir = Path.home() / "RaidenWorkspace"
        self.workspace_dir.mkdir(exist_ok=True)
        
        # Set workspace for app
        os.environ["RAIDEN_WORKSPACE"] = str(self.workspace_dir)
        
    def setup_tray(self):
        """Setup system tray icon and menu"""
        icon_path = Path(__file__).parent / "frontend" / "raiden.ico"
        image = Image.open(icon_path)
        
        def show_window():
            self.window.show()
            self.is_visible = True
            
        def hide_window():
            self.window.hide()
            self.is_visible = False
            
        def quit_app():
            self.tray.stop()
            self.window.destroy()
        
        menu = (
            pystray.MenuItem("Show", show_window),
            pystray.MenuItem("Hide", hide_window),
            pystray.MenuItem("Quit", quit_app)
        )
        
        self.tray = pystray.Icon(
            "Raiden+",
            image,
            "Raiden+ Agent",
            menu
        )
    
    def store_api_key(self, service: str, key: str):
        """Securely store API key"""
        keyring.set_password("raiden", service, key)
    
    def load_api_keys(self):
        """Load API keys from secure storage or .env"""
        env_path = self.workspace_dir / ".env"
        if env_path.exists():
            # Load keys from .env and store in keyring
            pass
    
    def run(self):
        """Launch the desktop application"""
        # Start FastAPI server
        server_thread = threading.Thread(
            target=lambda: uvicorn.run(app, host="127.0.0.1", port=5000),
            daemon=True
        )
        server_thread.start()
        
        # Setup system tray
        self.setup_tray()
        tray_thread = threading.Thread(target=self.tray.run)
        tray_thread.start()
        
        # Create main window
        self.window = webview.create_window(
            'Raiden+',
            url='http://127.0.0.1:5000/frontend',
            width=1200,
            height=800,
            resizable=True,
            min_size=(800, 600)
        )
        
        # Start GUI
        webview.start(debug=True)

def main():
    app = RaidenDesktop()
    app.run()

if __name__ == '__main__':
    main()
