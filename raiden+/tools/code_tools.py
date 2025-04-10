import os
from pathlib import Path
from typing import List, Dict, Optional
import ast
import black
import isort
import radon.complexity as radon_cc
import radon.raw as radon_raw
import bandit.core.manager as bandit_manager
from bandit.core.config import BanditConfig
from bandit.core.meta_ast import BanditMetaAst
from langchain_core.tools import tool

try:
    from app import WORKSPACE_DIR, color_text, _resolve_safe_path
except ImportError:
    WORKSPACE_DIR = Path("./raiden_workspace_srv")
    WORKSPACE_DIR.mkdir(exist_ok=True)
    def color_text(text, color="WHITE"): print(f"[{color}] {text}"); return text
    def _resolve_safe_path(filename: str) -> Path:
        target_path = (WORKSPACE_DIR / filename).resolve()
        if not str(target_path).startswith(str(WORKSPACE_DIR.resolve())):
            raise ValueError("Path traversal attempt detected.")
        return target_path

@tool
def analyze_code(file_path: str) -> str:
    """
    Analyzes Python code for complexity, security issues, and provides metrics.
    Also formats the code using black and isort.
    
    Args:
        file_path (str): Path to the Python file to analyze
    
    Returns:
        str: Analysis report including metrics, security issues, and formatting changes
    """
    try:
        input_path = _resolve_safe_path(file_path)
        if not input_path.exists():
            return f"Error: File '{file_path}' not found in workspace"
            
        with open(input_path, 'r') as f:
            code = f.read()
            
        # Parse AST
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return f"Syntax error in code: {str(e)}"
            
        # Calculate complexity metrics
        cc_results = radon_cc.cc_visit(code)
        raw_metrics = radon_raw.analyze(code)
        
        # Security analysis with Bandit
        b_conf = BanditConfig()
        b_mgr = bandit_manager.BanditManager(b_conf, 'file')
        b_meta = BanditMetaAst()
        b_mgr.b_ma = b_meta
        b_mgr.run_scope([input_path])
        
        # Format code
        try:
            formatted_code = black.format_str(code, mode=black.FileMode())
            sorted_code = isort.code(formatted_code)
            
            # Save formatted code
            backup_path = input_path.with_suffix('.py.bak')
            with open(backup_path, 'w') as f:
                f.write(code)  # Save backup
            with open(input_path, 'w') as f:
                f.write(sorted_code)  # Save formatted code
        except Exception as e:
            formatted_status = f"Error formatting code: {str(e)}"
        else:
            formatted_status = "Code formatted successfully (backup saved with .bak extension)"
        
        # Build report
        report = []
        report.append("=== Code Analysis Report ===\n")
        
        # Complexity metrics
        report.append("Complexity Metrics:")
        for item in cc_results:
            report.append(f"- {item.name}: Cyclomatic Complexity = {item.complexity}")
        
        # Raw metrics
        report.append("\nCode Statistics:")
        report.append(f"- Lines of Code: {raw_metrics.loc}")
        report.append(f"- Logical Lines of Code: {raw_metrics.lloc}")
        report.append(f"- Number of Comments: {raw_metrics.comments}")
        
        # Security issues
        report.append("\nSecurity Analysis:")
        if b_mgr.scores:
            for score in b_mgr.scores:
                report.append(f"- {score.fname}:{score.lineno} - {score.issue_text} (Severity: {score.severity})")
        else:
            report.append("No security issues found")
        
        # Formatting status
        report.append(f"\nFormatting: {formatted_status}")
        
        return "\n".join(report)
        
    except Exception as e:
        return f"Error analyzing code: {str(e)}"

@tool
def search_code_patterns(pattern: str, file_types: Optional[List[str]] = None) -> str:
    """
    Searches for code patterns across files in the workspace using AST-based pattern matching.
    
    Args:
        pattern (str): The pattern to search for (e.g., "function calls", "class definitions", etc.)
        file_types (List[str], optional): File extensions to search (e.g., ['.py', '.js']). Defaults to ['.py']
    
    Returns:
        str: Found patterns and their locations
    """
    if not file_types:
        file_types = ['.py']
        
    results = []
    results.append(f"Searching for pattern: {pattern}")
    
    try:
        for file_type in file_types:
            for file_path in WORKSPACE_DIR.rglob(f"*{file_type}"):
                if file_path.is_file():
                    try:
                        with open(file_path, 'r') as f:
                            code = f.read()
                            
                        if file_type == '.py':
                            tree = ast.parse(code)
                            matches = []
                            
                            class PatternVisitor(ast.NodeVisitor):
                                def visit_FunctionDef(self, node):
                                    if 'function' in pattern.lower():
                                        matches.append((node.name, node.lineno))
                                    self.generic_visit(node)
                                    
                                def visit_ClassDef(self, node):
                                    if 'class' in pattern.lower():
                                        matches.append((node.name, node.lineno))
                                    self.generic_visit(node)
                                    
                                def visit_Call(self, node):
                                    if 'call' in pattern.lower() and isinstance(node.func, ast.Name):
                                        matches.append((node.func.id, node.lineno))
                                    self.generic_visit(node)
                            
                            visitor = PatternVisitor()
                            visitor.visit(tree)
                            
                            if matches:
                                rel_path = file_path.relative_to(WORKSPACE_DIR)
                                results.append(f"\nFile: {rel_path}")
                                for name, line in matches:
                                    results.append(f"- {name} (line {line})")
                                    
                    except Exception as e:
                        results.append(f"Error processing {file_path}: {str(e)}")
                        
    except Exception as e:
        return f"Error searching patterns: {str(e)}"
        
    if len(results) == 1:
        results.append("No matching patterns found")
        
    return "\n".join(results)