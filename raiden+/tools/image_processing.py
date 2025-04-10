import os
from pathlib import Path
from PIL import Image, ImageEnhance, ImageFilter
from typing import Optional, Tuple
from langchain_core.tools import tool

try:
    from app import WORKSPACE_DIR, _resolve_safe_path
except ImportError:
    WORKSPACE_DIR = Path("./raiden_workspace_srv")
    def _resolve_safe_path(filename: str) -> Path:
        return WORKSPACE_DIR / filename

@tool
def resize_image(image_path: str, width: int, height: int, output_path: Optional[str] = None) -> str:
    """Resizes an image to specified dimensions."""
    try:
        input_path = _resolve_safe_path(image_path)
        if not input_path.exists():
            return f"Error: Image '{image_path}' not found"
            
        output_path = _resolve_safe_path(output_path or f"resized_{image_path}")
        
        with Image.open(input_path) as img:
            resized = img.resize((width, height), Image.Resampling.LANCZOS)
            resized.save(output_path)
            
        return f"Image resized and saved as '{output_path.name}'"
    except Exception as e:
        return f"Error resizing image: {str(e)}"

@tool
def apply_filter(image_path: str, filter_type: str) -> str:
    """Applies visual filters to images (blur, sharpen, emboss, etc)."""
    try:
        input_path = _resolve_safe_path(image_path)
        if not input_path.exists():
            return f"Error: Image '{image_path}' not found"
            
        filter_map = {
            "blur": ImageFilter.BLUR,
            "sharpen": ImageFilter.SHARPEN,
            "emboss": ImageFilter.EMBOSS,
            "edge_enhance": ImageFilter.EDGE_ENHANCE,
            "smooth": ImageFilter.SMOOTH
        }
        
        if filter_type not in filter_map:
            return f"Error: Unknown filter type. Available filters: {', '.join(filter_map.keys())}"
            
        output_path = _resolve_safe_path(f"{filter_type}_{image_path}")
        
        with Image.open(input_path) as img:
            filtered = img.filter(filter_map[filter_type])
            filtered.save(output_path)
            
        return f"Filter '{filter_type}' applied and saved as '{output_path.name}'"
    except Exception as e:
        return f"Error applying filter: {str(e)}"

@tool
def adjust_image(image_path: str, brightness: float = 1.0, contrast: float = 1.0, 
                saturation: float = 1.0, sharpness: float = 1.0) -> str:
    """Adjusts image properties (brightness, contrast, saturation, sharpness)."""
    try:
        input_path = _resolve_safe_path(image_path)
        if not input_path.exists():
            return f"Error: Image '{image_path}' not found"
            
        output_path = _resolve_safe_path(f"adjusted_{image_path}")
        
        with Image.open(input_path) as img:
            # Apply adjustments
            if brightness != 1.0:
                img = ImageEnhance.Brightness(img).enhance(brightness)
            if contrast != 1.0:
                img = ImageEnhance.Contrast(img).enhance(contrast)
            if saturation != 1.0:
                img = ImageEnhance.Color(img).enhance(saturation)
            if sharpness != 1.0:
                img = ImageEnhance.Sharpness(img).enhance(sharpness)
                
            img.save(output_path)
            
        return f"Image adjusted and saved as '{output_path.name}'"
    except Exception as e:
        return f"Error adjusting image: {str(e)}"
