import os
from pathlib import Path
from typing import Optional, Dict
import boto3
from botocore.exceptions import ClientError
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

# Initialize AWS Polly client
polly_client = None
if (aws_access_key_id := os.environ.get("AWS_ACCESS_KEY_ID")) and \
   (aws_secret_access_key := os.environ.get("AWS_SECRET_ACCESS_KEY")):
    try:
        polly_client = boto3.client(
            'polly',
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=os.environ.get("AWS_REGION", "us-east-1")
        )
        print(color_text("AWS Polly client initialized.", "GREEN"))
    except Exception as e:
        print(color_text(f"Error initializing AWS Polly: {e}", "RED"))

# Voice presets for different use cases
VOICE_PRESETS = {
    "neutral": {"VoiceId": "Matthew", "Engine": "neural"},
    "professional": {"VoiceId": "Joanna", "Engine": "neural"},
    "casual": {"VoiceId": "Kevin", "Engine": "neural"},
    "news": {"VoiceId": "Amy", "Engine": "neural"},
    "narrative": {"VoiceId": "Brian", "Engine": "neural"}
}

@tool
def text_to_speech(
    text: str,
    voice_preset: str = "neutral",
    language_code: str = "en-US",
    output_filename: Optional[str] = None,
    ssml: bool = False
) -> str:
    """
    Converts text to natural-sounding speech using AWS Polly.
    
    Args:
        text: Text to convert to speech
        voice_preset: Voice style ("neutral", "professional", "casual", "news", "narrative")
        language_code: Language code (e.g., 'en-US', 'es-ES')
        output_filename: Output filename (optional)
        ssml: Whether the input text is SSML markup
    
    Returns:
        str: Path to the generated audio file or error message
    """
    if not polly_client:
        return "Error: AWS Polly client not available. Check AWS credentials."
    
    print(color_text(f"--- Converting to Speech: {voice_preset} voice ---", "CYAN"))
    
    try:
        # Get voice settings from preset
        voice_settings = VOICE_PRESETS.get(voice_preset.lower(), VOICE_PRESETS["neutral"])
        
        # Generate output filename if not provided
        if not output_filename:
            output_filename = f"speech_{voice_preset}_{os.urandom(4).hex()}.mp3"
        
        output_path = _resolve_safe_path(output_filename)
        
        # Prepare Polly synthesis request
        synthesis_params = {
            "Engine": voice_settings["Engine"],
            "LanguageCode": language_code,
            "VoiceId": voice_settings["VoiceId"],
            "OutputFormat": "mp3"
        }
        
        # Add text with appropriate parameter based on SSML flag
        if ssml:
            synthesis_params["TextType"] = "ssml"
            synthesis_params["Text"] = text
        else:
            synthesis_params["TextType"] = "text"
            synthesis_params["Text"] = text
        
        # Request speech synthesis
        response = polly_client.synthesize_speech(**synthesis_params)
        
        # Save the audio stream to file
        if "AudioStream" in response:
            with open(output_path, 'wb') as audio_file:
                audio_file.write(response['AudioStream'].read())
            
            return f"Speech generated successfully: '{output_filename}'"
        else:
            return "Error: No audio stream in response"
            
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_msg = e.response['Error']['Message']
        print(color_text(f"AWS Polly error: {error_code} - {error_msg}", "RED"))
        return f"AWS Polly error: {error_code} - {error_msg}"
    except Exception as e:
        print(color_text(f"Error in text-to-speech conversion: {e}", "RED"))
        return f"Error: {str(e)}"

@tool
def get_available_voices() -> str:
    """Lists all available AWS Polly voices with their details."""
    if not polly_client:
        return "Error: AWS Polly client not available. Check AWS credentials."
    
    try:
        response = polly_client.describe_voices()
        voices = response['Voices']
        
        # Group voices by language
        voice_by_language = {}
        for voice in voices:
            lang = voice['LanguageCode']
            if lang not in voice_by_language:
                voice_by_language[lang] = []
            voice_by_language[lang].append({
                'name': voice['Id'],
                'gender': voice['Gender'],
                'engine': voice.get('SupportedEngines', ['standard'])[0]
            })
        
        # Format output
        output = ["Available AWS Polly Voices:"]
        for lang, lang_voices in sorted(voice_by_language.items()):
            output.append(f"\n{lang}:")
            for voice in lang_voices:
                output.append(f"  - {voice['name']} ({voice['gender']}, {voice['engine']})")
        
        return "\n".join(output)
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_msg = e.response['Error']['Message']
        print(color_text(f"AWS Polly error: {error_code} - {error_msg}", "RED"))
        return f"AWS Polly error: {error_code} - {error_msg}"
    except Exception as e:
        print(color_text(f"Error listing voices: {e}", "RED"))
        return f"Error: {str(e)}"

@tool
def create_speech_with_effects(
    text: str,
    effects: Dict[str, str],
    voice_preset: str = "neutral",
    output_filename: Optional[str] = None
) -> str:
    """
    Creates speech with SSML effects like prosody, emphasis, and breaks.
    
    Args:
        text: Text to convert to speech
        effects: Dictionary of effects to apply (rate, pitch, volume, breaks)
        voice_preset: Voice style preset to use
        output_filename: Output filename (optional)
    
    Returns:
        str: Path to the generated audio file or error message
    """
    if not polly_client:
        return "Error: AWS Polly client not available. Check AWS credentials."
    
    try:
        # Construct SSML with effects
        ssml = '<speak>'
        
        # Add prosody effects if specified
        prosody_attrs = []
        if 'rate' in effects:
            prosody_attrs.append(f'rate="{effects["rate"]}"')
        if 'pitch' in effects:
            prosody_attrs.append(f'pitch="{effects["pitch"]}"')
        if 'volume' in effects:
            prosody_attrs.append(f'volume="{effects["volume"]}"')
        
        if prosody_attrs:
            ssml += f'<prosody {" ".join(prosody_attrs)}>'
        
        # Add text with breaks if specified
        if 'breaks' in effects:
            segments = text.split()
            ssml += ' '.join(f'{segment} <break time="{effects["breaks"]}"/>' for segment in segments)
        else:
            ssml += text
        
        if prosody_attrs:
            ssml += '</prosody>'
        
        ssml += '</speak>'
        
        # Use the main text_to_speech function with SSML
        return text_to_speech(
            text=ssml,
            voice_preset=voice_preset,
            output_filename=output_filename,
            ssml=True
        )
        
    except Exception as e:
        print(color_text(f"Error creating speech with effects: {e}", "RED"))
        return f"Error: {str(e)}"