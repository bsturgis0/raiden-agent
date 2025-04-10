import json
from typing import Any, Dict, List, Union
from pathlib import Path

class OutputFormatter:
    @staticmethod
    def format_table(data: List[Dict[str, Any]]) -> str:
        """Format data as a markdown table"""
        if not data:
            return ""
            
        headers = list(data[0].keys())
        table = ["| " + " | ".join(headers) + " |",
                "| " + " | ".join(["---" for _ in headers]) + " |"]
                
        for row in data:
            table.append("| " + " | ".join(str(row.get(h, "")) for h in headers) + " |")
            
        return "\n".join(table)

    @staticmethod
    def format_code_block(code: str, language: str = "") -> str:
        """Format code in markdown code block"""
        return f"```{language}\n{code}\n```"

    @staticmethod
    def format_plot_path(plot_path: str) -> str:
        """Format plot image path for display"""
        return f"![Plot]({plot_path})"

    @staticmethod
    def format_json(data: Any) -> str:
        """Format JSON data in a code block"""
        try:
            formatted_json = json.dumps(data, indent=2)
            return f"```json\n{formatted_json}\n```"
        except Exception:
            return str(data)

def format_tool_output(tool_name: str, output: Any) -> str:
    """Format tool output for consistent display"""
    try:
        # If output is already a string with markdown, return as is
        if isinstance(output, str) and ("```" in output or "![" in output):
            return output

        # Handle different output types 
        if isinstance(output, (dict, list)):
            return OutputFormatter.format_json(output)
            
        if tool_name.startswith("analyze_"):
            return OutputFormatter.format_json(output)
            
        elif tool_name.startswith("python_repl"):
            if "plot" in str(output).lower():
                plot_lines = []
                for line in str(output).split("\n"):
                    if ".png" in line or ".jpg" in line:
                        plot_path = line.split("'")[1] if "'" in line else line.split()[0]
                        plot_lines.append(OutputFormatter.format_plot_path(plot_path))
                    else:
                        plot_lines.append(line)
                return "\n".join(plot_lines)
            return OutputFormatter.format_code_block(str(output), "python")
            
        elif tool_name in ["get_resource_usage", "get_system_info", 
                         "check_website", "analyze_domain", "get_weather"]:
            return OutputFormatter.format_code_block(str(output), "yaml")
            
        elif tool_name == "list_running_processes":
            try:
                processes = []
                for line in str(output).split("\n")[1:]:
                    if not line.strip(): continue
                    parts = line.split(",")
                    if len(parts) >= 4:
                        proc = {
                            "PID": parts[0].split(":")[1].strip(),
                            "Name": parts[1].split(":")[1].strip(),
                            "CPU%": parts[2].split(":")[1].strip(),
                            "Memory%": parts[3].split(":")[1].strip()
                        }
                        processes.append(proc)
                return OutputFormatter.format_table(processes)
            except:
                return str(output)
                
        # Default handling
        return str(output)
        
    except Exception as e:
        return f"Error formatting output: {str(e)}\nRaw output: {str(output)}"

# Export the formatter class and function
__all__ = ['OutputFormatter', 'format_tool_output']