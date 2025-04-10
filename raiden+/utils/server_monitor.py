import os
import sys
import time
import psutil
import logging
import subprocess
from pathlib import Path
from typing import Optional

class ServerMonitor:
    def __init__(self, max_retries: int = 3, retry_delay: int = 5):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.server_process: Optional[subprocess.Popen] = None
        self.restart_count = 0
        
        # Setup logging
        logging.basicConfig(
            filename='server_monitor.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
    def start_server(self) -> bool:
        """Start the FastAPI server"""
        try:
            cmd = [sys.executable, "app.py"]
            self.server_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            logging.info("Server started successfully")
            return True
        except Exception as e:
            logging.error(f"Failed to start server: {e}")
            return False
            
    def check_server_health(self) -> bool:
        """Check if server is running and responsive"""
        if not self.server_process:
            return False
            
        # Check process status
        if self.server_process.poll() is not None:
            logging.warning("Server process has terminated")
            return False
            
        # Check memory usage
        process = psutil.Process(self.server_process.pid)
        memory_percent = process.memory_percent()
        if memory_percent > 90:
            logging.warning(f"High memory usage: {memory_percent}%")
            return False
            
        return True
        
    def restart_server(self) -> bool:
        """Attempt to restart the server"""
        if self.restart_count >= self.max_retries:
            logging.error("Maximum restart attempts reached")
            return False
            
        logging.info("Attempting server restart...")
        self.restart_count += 1
        
        # Kill existing process if any
        if self.server_process:
            self.server_process.terminate()
            try:
                self.server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.server_process.kill()
                
        # Wait before restart
        time.sleep(self.retry_delay)
        
        # Start new process
        return self.start_server()
        
    def monitor(self):
        """Main monitoring loop"""
        logging.info("Starting server monitoring")
        
        if not self.start_server():
            logging.error("Initial server start failed")
            return
            
        while True:
            try:
                if not self.check_server_health():
                    logging.warning("Server health check failed")
                    if not self.restart_server():
                        logging.error("Server restart failed")
                        break
                        
                time.sleep(30)  # Check every 30 seconds
                
            except KeyboardInterrupt:
                logging.info("Monitoring stopped by user")
                if self.server_process:
                    self.server_process.terminate()
                break
            except Exception as e:
                logging.error(f"Monitoring error: {e}")
                break

