import psutil
import platform
from datetime import datetime
from typing import Dict, List
from langchain_core.tools import tool

@tool
def get_system_info() -> str:
    """Gets basic system information."""
    info = {
        "System": platform.system(),
        "Node Name": platform.node(),
        "Release": platform.release(),
        "Version": platform.version(),
        "Machine": platform.machine(),
        "Processor": platform.processor(),
        "CPU Cores": psutil.cpu_count(logical=False),
        "Total Memory": f"{psutil.virtual_memory().total / (1024**3):.2f} GB"
    }
    return "\n".join(f"{k}: {v}" for k, v in info.items())

@tool
def get_resource_usage() -> str:
    """Gets current CPU, memory, and disk usage."""
    try:
        # CPU Usage
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Memory Usage
        memory = psutil.virtual_memory()
        memory_used_gb = memory.used / (1024**3)
        memory_total_gb = memory.total / (1024**3)
        
        # Disk Usage
        disk = psutil.disk_usage('/')
        disk_used_gb = disk.used / (1024**3)
        disk_total_gb = disk.total / (1024**3)
        
        return f"Resource Usage:\n" + \
               f"CPU Usage: {cpu_percent}%\n" + \
               f"Memory Usage: {memory_used_gb:.2f}GB / {memory_total_gb:.2f}GB ({memory.percent}%)\n" + \
               f"Disk Usage: {disk_used_gb:.2f}GB / {disk_total_gb:.2f}GB ({disk.percent}%)"
    except Exception as e:
        return f"Error getting resource usage: {str(e)}"

@tool
def list_running_processes(top_n: int = 10) -> str:
    """Lists top N running processes by CPU usage."""
    try:
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
                
        # Sort by CPU usage
        processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
        
        output = [f"Top {top_n} Processes by CPU Usage:"]
        for proc in processes[:top_n]:
            output.append(
                f"PID: {proc['pid']}, " + \
                f"Name: {proc['name']}, " + \
                f"CPU: {proc['cpu_percent']}%, " + \
                f"Memory: {proc.get('memory_percent', 0):.1f}%"
            )
            
        return "\n".join(output)
    except Exception as e:
        return f"Error listing processes: {str(e)}"

@tool
def monitor_network_connections() -> str:
    """Lists active network connections."""
    try:
        connections = psutil.net_connections(kind='inet')
        active_conns = []
        
        for conn in connections:
            try:
                if conn.status == 'ESTABLISHED':
                    local = f"{conn.laddr.ip}:{conn.laddr.port}"
                    remote = f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "N/A"
                    active_conns.append(f"Local: {local}, Remote: {remote}, PID: {conn.pid}")
            except (AttributeError, IndexError):
                continue
                
        return "Active Network Connections:\n" + "\n".join(active_conns[:10])  # Limit to top 10
    except Exception as e:
        return f"Error monitoring network connections: {str(e)}"
