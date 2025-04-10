import os
import tempfile
from pathlib import Path
from typing import Optional
import whisper
from langchain_core.tools import tool
from pydub import AudioSegment

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
def transcribe_audio(file_path: str, language: Optional[str] = None) -> str:
    """
    Transcribes audio from various formats (mp3, wav, m4a, etc.) to text.
    Supports multiple languages and provides timestamps.
    
    Args:
        file_path (str): Path to the audio file in the workspace
        language (str, optional): Language code (e.g., 'en', 'es', 'fr'). Auto-detects if not specified.
    
    Returns:
        str: Transcribed text with timestamps
    """
    try:
        input_path = _resolve_safe_path(file_path)
        if not input_path.exists():
            return f"Error: Audio file '{file_path}' not found in workspace"

        # Load audio and convert to WAV if needed
        audio = AudioSegment.from_file(str(input_path))
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_wav:
            audio.export(temp_wav.name, format='wav')
            
            # Initialize Whisper model
            model = whisper.load_model("base")
            
            # Transcribe
            result = model.transcribe(
                temp_wav.name,
                language=language,
                task="transcribe",
                verbose=False
            )
            
            # Format output with timestamps
            formatted_output = []
            for segment in result["segments"]:
                start_time = f"{int(segment['start'] // 60)}:{int(segment['start'] % 60):02d}"
                end_time = f"{int(segment['end'] // 60)}:{int(segment['end'] % 60):02d}"
                formatted_output.append(f"[{start_time} - {end_time}] {segment['text'].strip()}")
            
            # Clean up
            os.unlink(temp_wav.name)
            
            return "\n".join(formatted_output)
            
    except Exception as e:
        return f"Error transcribing audio: {str(e)}"