import os
import uuid
import mimetypes
import asyncio
import traceback
from pathlib import Path
from typing import Optional

# --- Google GenAI Client Library (Specific Imports) ---
from google import genai
from google.genai import types
from google.api_core import exceptions as google_api_exceptions

# --- Langchain Core ---
from langchain_core.tools import tool

# --- Project Imports ---
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

# --- API Key Check ---
gemini_api_key = os.environ.get("GEMINI_API_KEY")
if not gemini_api_key:
    print(color_text("Warning: GEMINI_API_KEY not found. Gemini image generation tool disabled.", "YELLOW"))

# --- Helper to Save Binary Data ---
def _save_binary_file(file_path: Path, data: bytes):
    """Safely writes binary data to a file, creating parent dirs."""
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "wb") as f:
            f.write(data)
    except IOError as e:
        print(color_text(f"Error saving file {file_path}: {e}", "RED"))
        raise

# --- Image Generation Tool ---
@tool
async def generate_image_gemini(prompt: str, output_filename_base: Optional[str] = None) -> str:
    """
    Generates an image using Google Gemini based on a textual prompt and saves it to the workspace.
    Requires the GEMINI_API_KEY environment variable.

    Args:
        prompt (str): Detailed description of the image.
        output_filename_base (Optional[str]): Base name for the output file (without extension).
                                              A unique name is generated if not provided.

    Returns:
        str: Confirmation message with the relative workspace path of the saved image, or an error message.
    """
    global gemini_api_key
    print(color_text(f"--- Tool: generate_image_gemini ---", "CYAN"))

    if not genai:
        return "Error: Google GenAI library components not available."
    if not gemini_api_key:
        return "Error: GEMINI_API_KEY is not configured."

    try:
        genai.configure(api_key=gemini_api_key)
    except Exception as e:
        return f"Error configuring Google GenAI client: {e}"

    model_name = "gemini-2.0-flash-exp-image-generation"
    generation_config = types.GenerateContentConfig(
        response_modalities=["image", "text"],
        response_mime_type="text/plain",
    )
    contents = [types.Content(role="user", parts=[types.Part.from_text(text=prompt)])]

    try:
        base_name = output_filename_base or f"gemini_image_{uuid.uuid4().hex}"
        safe_base_path = _resolve_safe_path(base_name)

        async def _generate_and_save_in_thread():
            saved_file_rel_path = None
            text_feedback = []

            try:
                client = genai.GenerativeModel(model_name=model_name)
                response_stream = client.generate_content(
                    contents=contents,
                    generation_config=generation_config,
                    stream=True
                )

                for chunk in response_stream:
                    if not chunk.candidates or not chunk.candidates[0].content or not chunk.candidates[0].content.parts:
                        continue

                    part = chunk.candidates[0].content.parts[0]
                    if part.inline_data:
                        inline_data = part.inline_data
                        file_extension = mimetypes.guess_extension(inline_data.mime_type) or ".png"
                        full_save_path = safe_base_path.with_suffix(file_extension)
                        _save_binary_file(full_save_path, inline_data.data)
                        saved_file_rel_path = str(full_save_path.relative_to(WORKSPACE_DIR.resolve()))
                        print(color_text(f"Image ({inline_data.mime_type}) saved: {saved_file_rel_path}", "GREEN"))
                        break
                    elif hasattr(part, 'text') and part.text:
                        text_feedback.append(part.text)

            except google_api_exceptions.GoogleAPIError as google_error:
                print(color_text(f"Google API Error during generation stream: {google_error}", "RED"))
                return f"Error communicating with Google API: {google_error}"
            except Exception as inner_e:
                print(color_text(f"Error within generation thread: {inner_e}", "RED"))
                traceback.print_exc()
                return f"Internal error during generation: {inner_e}"

            if saved_file_rel_path:
                return f"Generated image saved to workspace: '{saved_file_rel_path}'"
            else:
                full_text = "".join(text_feedback).strip()
                return f"Error: Image generation failed. Text response: '{full_text}'" if full_text else "Error: No image data received from API."

        print(color_text(f"Calling Gemini image generation...", "YELLOW"))
        result = await asyncio.to_thread(_generate_and_save_in_thread)
        return result

    except Exception as e:
        print(color_text(f"Error setting up image generation: {e}", "RED"))
        traceback.print_exc()
        return f"Setup error for image generation: {e}"
