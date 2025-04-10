import os
import sys
import webview
import threading
import keyring
import pystray
from PIL import Image
import json
from pathlib import Path
from typing import Optional
import uvicorn
from app import app, WORKSPACE_DIR

class RaidenDesktop:
    def __init__(self):
        self.window = None
        self.tray = None
        self.is_visible = True
        
    def setup_tray(self):
        """Create system tray icon and menu"""
        icon_path = Path(__file__).parent / "frontend" / "raiden.ico"
        image = Image.open(icon_path)
        
        def show_window():
            self.window.show()
            self.is_visible = True
            
        def hide_window():
            self.window.hide()
            self.is_visible = False
            
        def toggle_window():
            if self.is_visible:
                hide_window()
            else:
                show_window()
                
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
        
    def get_api_key(self, service: str) -> Optional[str]:
        """Retrieve stored API key"""
        return keyring.get_password("raiden", service)
        
    def run(self):
        """Start the desktop application"""
        # Start backend server
        server_thread = threading.Thread(
            target=lambda: uvicorn.run(app, host="127.0.0.1", port=5000),
            daemon=True
        )
        server_thread.start()
        
        # Create window
        self.window = webview.create_window(
            'Raiden+',
            url='http://127.0.0.1:5000/frontend',
            width=1200,
            height=800,
            resizable=True,
            min_size=(800, 600)
        )
        
        # Setup system tray
        self.setup_tray()
        
        # Start tray icon in separate thread
        tray_thread = threading.Thread(target=self.tray.run)
        tray_thread.start()
        
        # Start main window
        webview.start(debug=True)

def main():
    app = RaidenDesktop()
    app.run()

if __name__ == '__main__':
    main()
