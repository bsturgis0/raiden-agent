import os
from pathlib import Path
from typing import Optional
import azure.cognitiveservices.speech as speechsdk
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
def text_to_speech(text: str, language: str = "en-US", voice_name: str = "en-US-JennyNeural", output_filename: Optional[str] = None) -> str:
    """
    Converts text to natural-sounding speech using Azure Cognitive Services.
    
    Args:
        text (str): The text to convert to speech
        language (str, optional): Language code (e.g., 'en-US', 'es-ES'). Defaults to "en-US"
        voice_name (str, optional): Azure voice name. Defaults to "en-US-JennyNeural"
        output_filename (str, optional): Output filename. If not provided, generates one
    
    Returns:
        str: Path to the generated audio file or error message
    """
    try:
        speech_key = os.environ.get("AZURE_SPEECH_KEY")
        speech_region = os.environ.get("AZURE_SPEECH_REGION", "eastus")
        
        if not speech_key:
            return "Error: AZURE_SPEECH_KEY not configured"
            
        # Generate output filename if not provided
        if not output_filename:
            output_filename = f"speech_output_{os.urandom(4).hex()}.wav"
            
        output_path = _resolve_safe_path(output_filename)
        
        # Initialize speech config
        speech_config = speechsdk.SpeechConfig(
            subscription=speech_key,
            region=speech_region
        )
        speech_config.speech_synthesis_voice_name = voice_name
        
        # Configure audio output
        audio_config = speechsdk.AudioConfig(filename=str(output_path))
        
        # Create synthesizer
        speech_synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=speech_config,
            audio_config=audio_config
        )
        
        # Add SSML for better control
        ssml = f"""
        <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="{language}">
            <voice name="{voice_name}">
                <prosody rate="0.9" pitch="+0Hz">
                    {text}
                </prosody>
            </voice>
        </speak>
        """
        
        # Synthesize speech
        result = speech_synthesizer.speak_ssml_async(ssml).get()
        
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            return f"Speech generated successfully: '{output_filename}'"
        else:
            return f"Error synthesizing speech: {result.reason}"
            
    except Exception as e:
        return f"Error in text-to-speech conversion: {str(e)}"