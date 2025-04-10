import os
import sys
import time
import psutil
import logging
from pathlib import Path
from datetime import datetime
import subprocess
from typing import Optional, Dict
import asyncio
import tracemalloc

class ServerMonitor:
    def __init__(self, max_retries: int = 5, initial_delay: int = 5):
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.restart_count = 0
        self.server_process: Optional[subprocess.Popen] = None
        self.last_crash_time: Optional[float] = None
        self.crash_count = 0
        self.is_running = False
        self.running = False
        
        # Setup logging with memory tracking
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            filename=log_dir / 'server_monitor.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # Initialize crash statistics
        self.crash_stats: Dict[str, int] = {
            'memory_related': 0,
            'connection_related': 0,
            'model_related': 0,
            'unknown': 0
        }

    def analyze_crash(self, stderr_output: str) -> str:
        """Analyze crash reason from stderr output"""
        if "MemoryError" in stderr_output or "OOM" in stderr_output:
            self.crash_stats['memory_related'] += 1
            return "memory_related"
        elif "ConnectionError" in stderr_output or "Connection refused" in stderr_output:
            self.crash_stats['connection_related'] += 1
            return "connection_related"
        elif "Model initialization failed" in stderr_output or "API Error" in stderr_output:
            self.crash_stats['model_related'] += 1
            return "model_related"
        else:
            self.crash_stats['unknown'] += 1
            return "unknown"

    def calculate_backoff_delay(self) -> int:
        """Calculate exponential backoff delay"""
        return min(300, self.initial_delay * (2 ** self.restart_count))  # Max 5 minutes

    async def start_server(self) -> bool:
        """Start the FastAPI server with monitoring"""
        try:
            cmd = [sys.executable, "app.py"]
            self.server_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            logging.info("Server started successfully")
            return True
        except Exception as e:
            logging.error(f"Failed to start server: {e}")
            return False

    def check_server_health(self) -> bool:
        """Enhanced health check with process metrics"""
        if not self.server_process:
            return False
            
        try:
            if self.server_process.poll() is not None:
                stderr_output = self.server_process.stderr.read() if self.server_process.stderr else ""
                crash_type = self.analyze_crash(stderr_output)
                logging.warning(f"Server crashed. Type: {crash_type}")
                logging.debug(f"Stderr output: {stderr_output}")
                return False
                
            # Check process metrics
            process = psutil.Process(self.server_process.pid)
            metrics = {
                'cpu_percent': process.cpu_percent(),
                'memory_percent': process.memory_percent(),
                'num_threads': process.num_threads(),
                'connections': len(process.connections())
            }
            
            # Log metrics periodically
            logging.info(f"Server metrics: {metrics}")
            
            # Check for potential issues
            if metrics['memory_percent'] > 90:
                logging.warning(f"High memory usage: {metrics['memory_percent']}%")
                return False
                
            if metrics['cpu_percent'] > 95:
                logging.warning(f"High CPU usage: {metrics['cpu_percent']}%")
                return False
                
            return True
            
        except Exception as e:
            logging.error(f"Health check error: {e}")
            return False

    def monitor(self):
        """Main monitoring loop with improved crash handling using asyncio"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            loop.run_until_complete(self._async_monitor())
        except KeyboardInterrupt:
            logging.info("Monitoring stopped by user")
        finally:
            loop.close()

    async def _async_monitor(self):
        """Async implementation of monitor"""
        self.running = True
        logging.info("Starting server monitoring")
        
        while self.running:
            try:
                server_started = await self.start_server()
                if not server_started:
                    if self.restart_count >= self.max_retries:
                        logging.error("Maximum restart attempts reached")
                        await self.alert_admin()
                        break
                    
                    delay = self.calculate_backoff_delay()
                    logging.info(f"Waiting {delay} seconds before restart attempt {self.restart_count + 1}")
                    await asyncio.sleep(delay)
                    self.restart_count += 1
                    continue
                
                while self.running:
                    if not self.check_server_health():
                        now = time.time()
                        if self.last_crash_time and (now - self.last_crash_time) < 60:
                            self.crash_count += 1
                            if self.crash_count >= 3:
                                logging.error("Multiple crashes detected in short time period")
                                await self.alert_admin()
                                break
                        else:
                            self.crash_count = 1
                        
                        self.last_crash_time = now
                        break
                    
                    await asyncio.sleep(10)
                    
            except Exception as e:
                logging.error(f"Monitoring error: {e}")
                await asyncio.sleep(self.initial_delay)
        
        logging.info("Server monitoring stopped")

    def stop(self):
        """Stop the monitoring loop gracefully"""
        self.running = False
        if self.server_process:
            self.server_process.terminate()
            try:
                self.server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.server_process.kill()

    async def alert_admin(self):
        """Async version of alert_admin"""
        crash_report = f"""
        Critical Server Issues Detected:
        
        Crash Statistics:
        - Memory Related: {self.crash_stats['memory_related']}
        - Connection Related: {self.crash_stats['connection_related']}
        - Model Related: {self.crash_stats['model_related']}
        - Unknown: {self.crash_stats['unknown']}
        
        Total Restart Attempts: {self.restart_count}
        Last Crash Time: {datetime.fromtimestamp(self.last_crash_time) if self.last_crash_time else 'N/A'}
        Rapid Crash Count: {self.crash_count}
        Memory Snapshot: {tracemalloc.get_traced_memory()}
        """
        
        logging.critical(crash_report)
        # Add async alerting method here (email, Slack, etc.)

