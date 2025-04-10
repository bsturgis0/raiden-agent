import os
from pathlib import Path
from typing import Optional, List
import ast
import re
import json
import pdoc
from sphinx.ext.napoleon import GoogleDocstring
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

class DocStringParser:
    """Helper class to parse and format docstrings"""
    @staticmethod
    def parse_docstring(obj) -> dict:
        """Parse docstring into structured format"""
        docstring = obj.__doc__ or ""
        doc = GoogleDocstring(docstring)
        
        # Extract sections
        sections = {
            'description': [],
            'args': [],
            'returns': [],
            'raises': [],
            'examples': []
        }
        
        current_section = 'description'
        for line in str(doc).split('\n'):
            if line.strip().lower() in sections:
                current_section = line.strip().lower()
            elif line.strip():
                sections[current_section].append(line.strip())
                
        return {k: '\n'.join(v) for k, v in sections.items()}

@tool
def generate_docs(input_path: str, output_format: str = "markdown") -> str:
    """
    Generates comprehensive documentation for Python code.
    Supports markdown and HTML output formats.
    
    Args:
        input_path (str): Path to Python file or directory to document
        output_format (str): Output format - "markdown" or "html"
    
    Returns:
        str: Generated documentation path
    """
    try:
        input_path = _resolve_safe_path(input_path)
        if not input_path.exists():
            return f"Error: Path '{input_path}' not found"

        # Generate output path
        output_name = input_path.stem + "_docs"
        output_dir = _resolve_safe_path(output_name)
        output_dir.mkdir(exist_ok=True)

        # Generate documentation
        if output_format == "html":
            pdoc.pdoc(str(input_path), output_directory=str(output_dir))
            return f"Documentation generated in HTML format: {output_name}/index.html"
        else:
            # Custom markdown generation
            docs = []
            docs.append(f"# Documentation for {input_path.name}\n")
            
            with open(input_path, 'r') as f:
                code = f.read()
                
            try:
                tree = ast.parse(code)
            except SyntaxError as e:
                return f"Syntax error in code: {str(e)}"
                
            # Module docstring
            if ast.get_docstring(tree):
                docs.append("## Module Description\n")
                docs.append(ast.get_docstring(tree))
                docs.append("\n")
                
            # Classes
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    docs.append(f"## Class: {node.name}\n")
                    if ast.get_docstring(node):
                        docs.append(ast.get_docstring(node))
                    docs.append("\n")
                    
                    # Methods
                    for child in node.body:
                        if isinstance(child, ast.FunctionDef):
                            docs.append(f"### Method: {child.name}\n")
                            if ast.get_docstring(child):
                                docs.append(ast.get_docstring(child))
                            docs.append("\n")
                            
                elif isinstance(node, ast.FunctionDef) and node.parent_field is None:
                    docs.append(f"## Function: {node.name}\n")
                    if ast.get_docstring(node):
                        docs.append(ast.get_docstring(node))
                    docs.append("\n")
                    
            # Save markdown
            output_file = output_dir / f"{input_path.stem}.md"
            with open(output_file, 'w') as f:
                f.write('\n'.join(docs))
                
            return f"Documentation generated in Markdown format: {output_name}/{input_path.stem}.md"
            
    except Exception as e:
        return f"Error generating documentation: {str(e)}"

@tool
def api_specification(input_path: str, spec_format: str = "openapi") -> str:
    """
    Generates API specification from Python code (FastAPI, Flask, etc.).
    Supports OpenAPI/Swagger and API Blueprint formats.
    
    Args:
        input_path (str): Path to Python file containing API definitions
        spec_format (str): Specification format - "openapi" or "blueprint"
    
    Returns:
        str: Path to generated specification file
    """
    try:
        input_path = _resolve_safe_path(input_path)
        if not input_path.exists():
            return f"Error: File '{input_path}' not found"
            
        with open(input_path, 'r') as f:
            code = f.read()
            
        # Parse AST
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return f"Syntax error in code: {str(e)}"
            
        # Extract API information
        api_info = {
            'info': {
                'title': input_path.stem,
                'version': '1.0.0'
            },
            'paths': {}
        }
        
        route_decorators = {
            'get', 'post', 'put', 'delete', 
            'patch', 'options', 'head', 'trace'
        }
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Call) and hasattr(decorator.func, 'attr'):
                        if decorator.func.attr.lower() in route_decorators:
                            method = decorator.func.attr.lower()
                            
                            # Try to extract path from decorator args
                            path = "/"
                            if decorator.args:
                                path = ast.literal_eval(decorator.args[0])
                                
                            # Parse docstring for operation info
                            docstring = ast.get_docstring(node)
                            if docstring:
                                doc_info = DocStringParser.parse_docstring(type('Tmp', (), {'__doc__': docstring}))
                                
                                operation = {
                                    'summary': doc_info['description'],
                                    'parameters': [],
                                    'responses': {
                                        '200': {
                                            'description': doc_info['returns']
                                        }
                                    }
                                }
                                
                                # Add path to spec
                                if path not in api_info['paths']:
                                    api_info['paths'][path] = {}
                                api_info['paths'][path][method] = operation
        
        # Generate output
        output_name = f"{input_path.stem}_api_spec"
        if spec_format == "openapi":
            output_file = _resolve_safe_path(f"{output_name}.json")
            with open(output_file, 'w') as f:
                json.dump(api_info, f, indent=2)
        else:
            # Convert to API Blueprint format
            output_file = _resolve_safe_path(f"{output_name}.apib")
            with open(output_file, 'w') as f:
                f.write(f"# {api_info['info']['title']}\n\n")
                
                for path, methods in api_info['paths'].items():
                    for method, operation in methods.items():
                        f.write(f"## {method.upper()} {path}\n\n")
                        if 'summary' in operation:
                            f.write(f"{operation['summary']}\n\n")
                        if 'responses' in operation:
                            f.write("+ Response 200\n\n")
                            
        return f"API specification generated: {output_file.name}"
        
    except Exception as e:
        return f"Error generating API specification: {str(e)}"