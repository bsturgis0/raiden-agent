import socket
import requests
import dns.resolver
import speedtest
from typing import Optional
from langchain_core.tools import tool

@tool
def check_website(url: str) -> str:
    """Checks website availability and status."""
    try:
        response = requests.get(url, timeout=10)
        return f"Website Status:\n" + \
               f"URL: {url}\n" + \
               f"Status Code: {response.status_code}\n" + \
               f"Response Time: {response.elapsed.total_seconds():.2f}s\n" + \
               f"Server: {response.headers.get('Server', 'Unknown')}\n" + \
               f"Content Type: {response.headers.get('Content-Type', 'Unknown')}"
    except requests.exceptions.RequestException as e:
        return f"Error checking website: {str(e)}"

@tool
def analyze_domain(domain: str) -> str:
    """Gets domain information and DNS records."""
    try:
        info = []
        info.append(f"Domain Analysis for: {domain}\n")
        
        # IP Resolution
        try:
            ip = socket.gethostbyname(domain)
            info.append(f"IP Address: {ip}")
        except socket.gaierror:
            info.append("IP Address: Unable to resolve")
        
        # DNS Records
        record_types = ['A', 'AAAA', 'MX', 'NS', 'TXT']
        for record_type in record_types:
            try:
                answers = dns.resolver.resolve(domain, record_type)
                records = [str(rdata) for rdata in answers]
                info.append(f"\n{record_type} Records:")
                for record in records:
                    info.append(f"  - {record}")
            except Exception:
                info.append(f"\n{record_type} Records: None found")
                
        return "\n".join(info)
    except Exception as e:
        return f"Error analyzing domain: {str(e)}"

@tool
def test_network_speed() -> str:
    """Tests internet connection speed."""
    try:
        st = speedtest.Speedtest()
        st.get_best_server()
        
        # Test download speed
        download_speed = st.download() / 1_000_000  # Convert to Mbps
        
        # Test upload speed
        upload_speed = st.upload() / 1_000_000  # Convert to Mbps
        
        # Get ping
        ping = st.results.ping
        
        return f"Network Speed Test Results:\n" + \
               f"Download Speed: {download_speed:.2f} Mbps\n" + \
               f"Upload Speed: {upload_speed:.2f} Mbps\n" + \
               f"Ping: {ping:.2f} ms"
    except Exception as e:
        return f"Error testing network speed: {str(e)}"
