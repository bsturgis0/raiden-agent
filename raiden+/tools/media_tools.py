from langchain_core.tools import tool

@tool
def format_video(input_path: str, output_format: str = "mp4") -> str:
    """Converts video files between formats"""

@tool
def extract_audio(video_path: str, output_path: str) -> str:
    """Extracts audio from video files"""

@tool
def compress_media(input_path: str, quality: str = "high") -> str:
    """Compresses media files while maintaining quality"""
