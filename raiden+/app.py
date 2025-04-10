__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

# --- Standard Library Imports ---
import getpass
import os
import json
import platform
import re
import traceback
import math
import smtplib
import ssl
import uuid
import asyncio
from email.message import EmailMessage
from datetime import datetime
from pathlib import Path
from typing import Annotated, List, Dict, Any, Optional, Union
from typing_extensions import TypedDict
import subprocess

# --- Web Framework Imports ---
from fastapi import FastAPI, HTTPException, UploadFile, File, Body, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse, FileResponse
import uvicorn
from pydantic import BaseModel, Field

# --- Environment & Config Imports ---
from dotenv import load_dotenv

# --- Third-Party Library Imports ---
import boto3
from botocore.exceptions import ClientError
from github import Github, GithubException

# --- Langchain Imports ---
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_together import ChatTogether
from langchain_groq import ChatGroq
from langchain_deepseek import ChatDeepSeek
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_community.tools import BraveSearch
from langchain_core.messages import BaseMessage, ToolMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import InjectedToolCallId, tool
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

# --- RAG Tools Imports ---
from tools.rag_tools import index_document, query_documents, initialize_rag_components

# --- Wikipedia Tool Imports ---
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper

# --- YouTube Search Tool Imports ---
from langchain_community.tools import YouTubeSearchTool

# --- Python REPL Tool Imports ---
from langchain_experimental.utilities import PythonREPL  # Ensure this module is installed
from langchain_core.tools import Tool

# --- Image Generation Tool Import ---
from tools.image_generation_tool import generate_image_gemini

# --- Redis Memory Management ---
from langchain_community.chat_message_histories import UpstashRedisChatMessageHistory

# --- Environment Setup ---
load_dotenv()

# Color setup (for server logs)
COLORS = { "BLUE": "\033[94m", "GREEN": "\033[92m", "YELLOW": "\033[93m", "RED": "\033[91m", "CYAN": "\033[96m", "MAGENTA": "\033[95m", "WHITE": "\033[97m", "ENDC": "\033[0m", }
SUPPORTS_COLOR = platform.system() != "Windows" or "ANSICON" in os.environ or "WT_SESSION" in os.environ
def color_text(text, color_key="WHITE"):
    if not SUPPORTS_COLOR: return text
    return f"{COLORS.get(color_key.upper(), COLORS['WHITE'])}{text}{COLORS['ENDC']}"

print(color_text("--- Raiden Agent Backend Initializing ---", "MAGENTA"))

# --- API Key Checks & Warnings ---
# Check keys and print warnings on server start
google_api_key_found = bool(os.environ.get("GOOGLE_API_KEY"))
tavily_api_key_found = bool(os.environ.get("TAVILY_API_KEY"))
together_api_key_found = bool(os.environ.get("TOGETHER_API_KEY"))
gmail_address_found = bool(os.environ.get("GMAIL_ADDRESS"))
gmail_password_found = bool(os.environ.get("GMAIL_APP_PASSWORD"))
github_token = os.environ.get("GITHUB_TOKEN")
groq_api_key_found = bool(os.environ.get("GROQ_API_KEY"))
brave_api_key_found = bool(os.environ.get("BRAVE_SEARCH_API_KEY"))
deepseek_api_key_found = bool(os.environ.get("DEEPSEEK_API_KEY"))
aws_access_key_found = bool(os.environ.get("AWS_ACCESS_KEY_ID"))
aws_secret_key_found = bool(os.environ.get("AWS_SECRET_ACCESS_KEY"))
aws_region = os.environ.get("AWS_REGION", "us-east-1")

if not google_api_key_found: print(color_text("Warning: GOOGLE_API_KEY not found.", "YELLOW"))
if not tavily_api_key_found: print(color_text("Warning: TAVILY_API_KEY not found.", "YELLOW"))
if not together_api_key_found: print(color_text("Warning: TOGETHER_API_KEY not found.", "YELLOW"))
if not gmail_address_found or not gmail_password_found: print(color_text("Warning: GMAIL credentials incomplete.", "YELLOW"))
if not github_token: print(color_text("Warning: GITHUB_TOKEN not found.", "YELLOW"))
if not groq_api_key_found: print(color_text("Warning: GROQ_API_KEY not found.", "YELLOW"))
if not brave_api_key_found: print(color_text("Warning: BRAVE_SEARCH_API_KEY not found.", "YELLOW"))
if not deepseek_api_key_found: print(color_text("Warning: DEEPSEEK_API_KEY not found.", "YELLOW"))
if not aws_access_key_found or not aws_secret_key_found: print(color_text("Warning: AWS credentials not found.", "YELLOW"))


# --- Workspace Directory ---
WORKSPACE_DIR = Path("./raiden_workspace_srv")
WORKSPACE_DIR.mkdir(exist_ok=True)
print(color_text(f"Server Workspace: {WORKSPACE_DIR.resolve()}", "YELLOW"))

# --- Global Clients Initialization ---
github_client = None
if github_token:
    try:
        github_client = Github(github_token)
        _ = github_client.get_rate_limit() # Test connection
        print(color_text("GitHub client initialized.", "GREEN"))
    except Exception as e:
        print(color_text(f"Warning: Failed to initialize GitHub client: {e}", "YELLOW"))
        github_client = None
else:
     print(color_text("GitHub client NOT initialized (No GITHUB_TOKEN).", "YELLOW"))

rekognition_client = None
if aws_access_key_found and aws_secret_key_found:
    try:
        rekognition_client = boto3.client(
            'rekognition', region_name=aws_region,
            aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
        )
        print(color_text("AWS Rekognition client initialized.", "GREEN"))
    except Exception as e:
        print(color_text(f"Warning: Failed to initialize AWS Rekognition client: {e}", "YELLOW"))
        rekognition_client = None
else:
     print(color_text("AWS Rekognition client NOT initialized (AWS keys missing).", "YELLOW"))


# --- LLM Selection & Initialization ---
# Select ONE LLM model when the server starts
# Prioritize keys: Groq > Google > Together > DeepSeek
selected_llm_instance = None
llm_name = "None"

if groq_api_key_found:
    print(color_text("Using Groq Llama 3 (llama3-70b-8192) as default LLM.", "GREEN"))
    selected_llm_instance = ChatGroq(temperature=0.7, model_name="deepseek-r1-distill-llama-70b", max_tokens=8192)
    llm_name = "Groq Llama 3"
elif google_api_key_found:
    print(color_text("Using Google Gemini Flash (gemini-2.0-flash) as LLM.", "GREEN"))
    selected_llm_instance = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.7, max_tokens=4096)
    llm_name = "Google Gemini Flash"
elif together_api_key_found:
    print(color_text("Using Together Llama 3 (meta-llama/Llama-3-70b-chat-hf) as LLM.", "GREEN"))
    selected_llm_instance = ChatTogether(model="meta-llama/Llama-3-70b-chat-hf", temperature=0.7, max_tokens=4096)
    llm_name = "Together Llama 3"
elif deepseek_api_key_found:
    print(color_text("Using DeepSeek Chat (deepseek-chat) as LLM.", "GREEN"))
    selected_llm_instance = ChatDeepSeek(model="deepseek-chat", temperature=0.7, max_tokens=4096)
    llm_name = "DeepSeek Chat"
else:
    print(color_text("CRITICAL ERROR: No suitable LLM API key found. Backend cannot function.", "RED"))
    # Exit or handle gracefully - exiting for clarity here
    exit(1)

print(color_text(f"Selected LLM: {llm_name}", "GREEN"))

# --- Initialize RAG Components ---
initialize_rag_components()

# Initialize Wikipedia tool
wikipedia_tool = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())

# Initialize YouTube search tool
youtube_search_tool = YouTubeSearchTool()

# Initialize Python REPL tool
python_repl = PythonREPL()
repl_tool = Tool(
    name="python_repl",
    description="""A Python shell for executing Python commands, with special support for data visualization:
    - Create plots using matplotlib, seaborn, or plotly
    - Save plots using plt.savefig('plot_name.png')
    - All plots will be automatically displayed in the chat
    - For best results, use light colors and clear labels
    - Always close plots using plt.close() to free memory""",
    func=python_repl.run,
    coroutine=None,
    args_schema=None,
    return_direct=False,
    verbose=True,  # Enable verbose mode for better error reporting
)

# ==============================================================================
# --- TOOL DEFINITIONS ---
# ALL @tool functions MUST be defined BEFORE they are used in lists or maps.
# ==============================================================================

# --- Helper Function for Safe Paths ---
def _resolve_safe_path(filename: str) -> Path:
    """Resolves a path relative to WORKSPACE_DIR, preventing directory traversal."""
    base_path = WORKSPACE_DIR.resolve()
    cleaned_filename = filename.strip().lstrip('/')
    if not cleaned_filename:
        raise ValueError("Filename cannot be empty.")
    # Normalize path separators for the current OS
    cleaned_filename = os.path.normpath(cleaned_filename)
    # Prevent path components like '..'
    if '..' in cleaned_filename.split(os.sep):
        raise ValueError(f"Path component '..' detected in '{filename}'. Operation limited to workspace.")

    target_path = (base_path / cleaned_filename).resolve()

    # Final check: Ensure the resolved path is under the base path
    if not str(target_path).startswith(str(base_path)):
        # Check if it's exactly the base path itself (e.g., path=".")
        if str(target_path) == str(base_path):
            return target_path
        # Otherwise, it's outside
        print(f"Path Check Failed: Base='{base_path}', Target='{target_path}'")
        raise ValueError(f"Path traversal attempt detected for '{filename}'. Operation limited to workspace.")
    return target_path


# --- Search Tools ---
tavily_tool = TavilySearchResults(
    max_results=1,
    include_answer=True,
    include_raw_content=False,
    search_depth="advanced",
)

brave_search_tool = BraveSearch.from_api_key(
    api_key=os.environ.get("BRAVE_SEARCH_API_KEY"),
    search_kwargs={"count": 2},
    name="brave_web_search" # Ensure name consistency
)

# --- Calculator Tool ---
@tool
def calculator(query: str) -> str:
    """Calculates the result of a mathematical expression."""
    print(color_text(f"--- Running Calculator for: {query} ---", "CYAN"))
    try:
        allowed_chars = "0123456789.+-*/^() "
        # Allow math constants/functions explicitly
        allowed_math = {k: v for k, v in math.__dict__.items() if not k.startswith("__")}

        # Basic check for potentially unsafe characters (simplistic)
        if any(c not in allowed_chars and c not in allowed_math and not c.isspace() for c in query):
             raise ValueError("Potentially unsafe characters in expression for calculator.")

        safe_query = query.replace('^', '**')
        # Use a safer evaluation context
        result = eval(safe_query, {"__builtins__": None}, allowed_math)
        return f"Result: {result}"
    except Exception as e:
        return f"Calculator error: {e}"

# --- Date/Time Tool ---
@tool
def get_current_datetime() -> str:
    """Returns the current date and time."""
    print(color_text("--- Getting Current Date/Time ---", "CYAN"))
    now = datetime.now()
    formatted_time = now.strftime("%Y-%m-%d %H:%M:%S %A")
    return f"Current date and time is: {formatted_time}"

# --- Email Drafting Tool ---
@tool
def email_drafter(recipient: str, subject: str, prompt: str) -> str:
    """Drafts an email based on a prompt, recipient, and subject."""
    global selected_llm_instance
    if not selected_llm_instance:
        return "Error: Email drafter cannot function, base LLM not selected."

    print(color_text(f"--- Drafting Email to {recipient} about '{subject}' ---", "CYAN"))
    draft_prompt = f"""Please write a professional email draft based on the following:
To: {recipient}
Subject: {subject}
Content Prompt/Goal: {prompt}

Draft the email body below:"""
    try:
        # Use the base LLM instance for drafting
        response = selected_llm_instance.invoke([HumanMessage(content=draft_prompt)])
        draft = response.content
        full_draft = f"To: {recipient}\nSubject: {subject}\n\n{draft}"
        print(color_text("Draft complete.", "GREEN"))
        return full_draft
    except Exception as e:
        print(color_text(f"Error during email drafting: {e}", "RED"))
        return f"Error drafting email: {e}"

# --- File I/O Tools (Safe Operations) ---
@tool
def read_file(filename: str) -> str:
    """Reads the content of a specified file within the designated workspace directory."""
    print(color_text(f"--- Reading File: {filename} ---", "CYAN"))
    try:
        safe_path = _resolve_safe_path(filename)
        if not safe_path.is_file():
            return f"Error: File not found at '{filename}' within the workspace."
        content = safe_path.read_text(encoding='utf-8', errors='replace')
        max_len = 5000
        if len(content) > max_len:
            content = content[:max_len] + "\n... [truncated]"
        return f"Content of '{filename}':\n```\n{content}\n```"
    except ValueError as e:
        print(color_text(f"Error reading file (Path): {e}", "RED"))
        return f"Error: {e}"
    except Exception as e:
        print(color_text(f"Error reading file {filename}: {e}", "RED"))
        return f"Error reading file: {e}"

@tool
def list_directory(path: str = ".") -> str:
    """Lists files/dirs within a path inside the workspace. Defaults to workspace root."""
    print(color_text(f"--- Listing Directory: {path} ---", "CYAN"))
    try:
        safe_base_path = _resolve_safe_path(path)
        if not safe_base_path.is_dir():
             display_path = path if path != "." else "workspace root"
             # Check existence more carefully
             if not safe_base_path.exists():
                  return f"Error: Path '{display_path}' not found within the workspace."
             else:
                  return f"Error: Path '{display_path}' exists but is not a directory."

        entries = []
        for entry in safe_base_path.iterdir():
            entry_type = "[D]" if entry.is_dir() else "[F]"
            try:
                relative_entry_path = entry.relative_to(WORKSPACE_DIR.resolve())
                entries.append(f"{entry_type} {relative_entry_path}")
            except ValueError:
                 entries.append(f"{entry_type} {entry.name} (At workspace root)") # Should be rare

        display_path = path if path != "." else "workspace root"
        if not entries:
            return f"Directory '{display_path}' is empty."
        return f"Contents of '{display_path}':\n" + "\n".join(sorted(entries))

    except ValueError as e:
        print(color_text(f"Error listing directory (Path): {e}", "RED"))
        return f"Error: {e}"
    except Exception as e:
        print(color_text(f"Error listing directory {path}: {e}", "RED"))
        return f"Error listing directory: {e}"

# --- GitHub Tools ---
@tool
def list_repo_contents(repo_name: str, path: str = "") -> str:
    """Lists files/dirs in a GitHub repo path. repo_name='owner/repo'."""
    global github_client
    if not github_client: return "Error: GitHub client not available (Check GITHUB_TOKEN)."
    print(color_text(f"--- Listing GitHub Repo: {repo_name}, Path: '{path}' ---", "CYAN"))
    try:
        repo = github_client.get_repo(repo_name)
        contents = repo.get_contents(path)
        entries = []
        for item in contents:
            entry_type = "[D]" if item.type == "dir" else "[F]"
            entries.append(f"{entry_type} {item.path}")
        if not entries:
            return f"Directory '{path}' in repo '{repo_name}' is empty or not found."
        return f"Contents of '{repo_name}' at path '{path}':\n" + "\n".join(sorted(entries))
    except GithubException as e:
        print(color_text(f"GitHub API Error listing {repo_name}/{path}: {e.status} {e.data}", "RED"))
        return f"Error listing repo contents: {e.data.get('message', e.status)}"
    except Exception as e:
        print(color_text(f"Error listing repo {repo_name}/{path}: {e}", "RED"))
        return f"Error listing repo contents: {e}"

@tool
def get_repo_file_content(repo_name: str, file_path: str) -> str:
    """Gets the content of a file from a GitHub repo. repo_name='owner/repo'."""
    global github_client
    if not github_client: return "Error: GitHub client not available."
    print(color_text(f"--- Getting GitHub File: {repo_name}/{file_path} ---", "CYAN"))
    try:
        repo = github_client.get_repo(repo_name)
        file_content_obj = repo.get_contents(file_path)
        if file_content_obj.type != "file":
            return f"Error: '{file_path}' in '{repo_name}' is not a file."
        # Limit file size read from GitHub
        max_size = 20000  # 20KB limit for safety
        if file_content_obj.size > max_size:
            return f"Error: File '{file_path}' is too large ({file_content_obj.size} bytes > {max_size} bytes limit)."
        decoded_content = file_content_obj.decoded_content.decode('utf-8', errors='replace')
        return f"Content of '{repo_name}/{file_path}':\n```\n{decoded_content}\n```"
    except GithubException as e:
        print(color_text(f"GitHub API Error getting {repo_name}/{file_path}: {e.status} {e.data}", "RED"))
        return f"Error getting file content: {e.data.get('message', e.status)}"
    except Exception as e:
        print(color_text(f"Error getting file {repo_name}/{file_path}: {e}", "RED"))
        return f"Error getting file content: {e}"

@tool
def create_or_update_repo_file(repo_name: str, file_path: str, content: str, commit_message: str) -> str:
    """Creates or updates a file in a GitHub repo. repo_name='owner/repo'."""
    global github_client
    if not github_client: return "Error: GitHub client not available."
    print(color_text(f"--- Creating/Updating GitHub File: {repo_name}/{file_path} ---", "CYAN"))
    try:
        repo = github_client.get_repo(repo_name)
        try:
            # Check if the file already exists
            file_content = repo.get_contents(file_path)
            # Update the file
            repo.update_file(
                path=file_path,
                message=commit_message,
                content=content,
                sha=file_content.sha
            )
            return f"File '{file_path}' updated successfully in '{repo_name}'."
        except GithubException:
            # File does not exist, create it
            repo.create_file(
                path=file_path,
                message=commit_message,
                content=content
            )
            return f"File '{file_path}' created successfully in '{repo_name}'."
    except GithubException as e:
        print(color_text(f"GitHub API Error creating/updating {repo_name}/{file_path}: {e.status} {e.data}", "RED"))
        return f"Error creating/updating file: {e.data.get('message', e.status)}"
    except Exception as e:
        print(color_text(f"Error creating/updating file {repo_name}/{file_path}: {e}", "RED"))
        return f"Error creating/updating file: {e}"

@tool
def delete_repo_file(repo_name: str, file_path: str, commit_message: str) -> str:
    """Deletes a file from a GitHub repo. repo_name='owner/repo'."""
    global github_client
    if not github_client: return "Error: GitHub client not available."
    print(color_text(f"--- Deleting GitHub File: {repo_name}/{file_path} ---", "CYAN"))
    try:
        repo = github_client.get_repo(file_path)
        file_content = repo.get_contents(file_path)
        # Delete the file
        repo.delete_file(
            path=file_path,
            message=commit_message,
            sha=file_content.sha
        )
        return f"File '{file_path}' deleted successfully from '{repo_name}'."
    except GithubException as e:
        print(color_text(f"GitHub API Error deleting {repo_name}/{file_path}: {e.status} {e.data}", "RED"))
        return f"Error deleting file: {e.data.get('message', e.status)}"
    except Exception as e:
        print(color_text(f"Error deleting file {repo_name}/{file_path}: {e}", "RED"))
        return f"Error deleting file: {e}"

# --- Image Analysis Tools (AWS Rekognition) ---
@tool
def analyze_image(image_path: str, analysis_types: str = "labels,text,objects,faces") -> str:
    """Analyzes an image using AWS Rekognition. Path is relative to workspace."""
    global rekognition_client
    if not rekognition_client: return "Error: AWS Rekognition client unavailable."
    print(color_text(f"--- Analyzing Image: {image_path} | Types: {analysis_types} ---", "CYAN"))
    try:
        safe_path = _resolve_safe_path(image_path)
        if not safe_path.is_file(): return f"Error: Image not found: '{image_path}'."
        with open(safe_path, "rb") as image_file: image_bytes = image_file.read()
        results = {"file": image_path}; analysis_list = [t.strip().lower() for t in analysis_types.split(",")]

        # Combined Label/Object Detection
        if "labels" in analysis_list or "objects" in analysis_list:
             try:
                response_labels = rekognition_client.detect_labels(Image={"Bytes": image_bytes}, MaxLabels=20)
                if "labels" in analysis_list: results["labels"] = [{"name": label["Name"], "confidence": round(label["Confidence"], 2)} for label in response_labels["Labels"]]
                if "objects" in analysis_list:
                    results["objects"] = [{"name": label["Name"], "confidence": round(instance["Confidence"], 2), "bounding_box": instance["BoundingBox"]} for label in response_labels["Labels"] if "Instances" in label for instance in label["Instances"]]
             except ClientError as ce: print(color_text(f"Rekognition error (detect_labels): {ce}", "YELLOW")); results["labels_error"] = str(ce)

        # Text Detection
        if "text" in analysis_list:
            try:
                response_text = rekognition_client.detect_text(Image={"Bytes": image_bytes})
                lines = [t for t in response_text["TextDetections"] if t["Type"] == "LINE"]
                results["text"] = { "full_text": " ".join([t["DetectedText"] for t in lines]), "text_items": [{"text": t["DetectedText"], "confidence": round(t["Confidence"], 2)} for t in lines] }
            except ClientError as ce: print(color_text(f"Rekognition error (detect_text): {ce}", "YELLOW")); results["text_error"] = str(ce)

        # Face Detection
        if "faces" in analysis_list:
             try:
                response_faces = rekognition_client.detect_faces(Image={"Bytes": image_bytes}, Attributes=['ALL'])
                results["faces"] = [{ "age_range": face["AgeRange"], "emotions": face["Emotions"], "gender": face["Gender"], "bounding_box": face["BoundingBox"] } for face in response_faces["FaceDetails"]]
             except ClientError as ce: print(color_text(f"Rekognition error (detect_faces): {ce}", "YELLOW")); results["faces_error"] = str(ce)

        # Moderation Detection
        if "moderation" in analysis_list:
             try:
                response_mod = rekognition_client.detect_moderation_labels(Image={"Bytes": image_bytes}, MinConfidence=50)
                results["moderation"] = { "safe_image": len(response_mod["ModerationLabels"]) == 0, "detected_labels": [{"name": label["Name"], "confidence": round(label["Confidence"], 2)} for label in response_mod["ModerationLabels"]] }
             except ClientError as ce: print(color_text(f"Rekognition error (detect_moderation_labels): {ce}", "YELLOW")); results["moderation_error"] = str(ce)

        return json.dumps(results, indent=2, default=lambda o: f"<<non-serializable: {type(o).__name__}>>")
    except ValueError as e: # Path error
         print(color_text(f"Error analyzing image (Path): {e}", "RED")); return f"Error: {e}"
    except ClientError as e: # Catch other general Rekognition errors
        error_code = e.response['Error']['Code']; error_msg = e.response['Error']['Message']
        print(color_text(f"AWS Rekognition error: {error_code} - {error_msg}", "RED")); return f"AWS Rekognition error: {error_code} - {error_msg}"
    except Exception as e:
        print(color_text(f"Error analyzing image {image_path}: {e}", "RED")); traceback.print_exc(); return f"Error analyzing image: {e}"

@tool
def compare_faces(source_image_path: str, target_image_path: str, similarity_threshold: float = 80.0) -> str:
    """Compares faces between two images using AWS Rekognition."""
    global rekognition_client
    if not rekognition_client: return "Error: AWS Rekognition client unavailable."
    print(color_text(f"--- Comparing Faces: {source_image_path} vs {target_image_path} ---", "CYAN"))
    try:
        source_path = _resolve_safe_path(source_image_path); target_path = _resolve_safe_path(target_image_path)
        if not source_path.is_file(): return f"Error: Source image not found: '{source_image_path}'."
        if not target_path.is_file(): return f"Error: Target image not found: '{target_image_path}'."
        with open(source_path, "rb") as sf: source_bytes = sf.read()
        with open(target_path, "rb") as tf: target_bytes = tf.read()

        threshold = max(0.0, min(float(similarity_threshold), 100.0)) # Ensure valid threshold

        response = rekognition_client.compare_faces( SourceImage={"Bytes": source_bytes}, TargetImage={"Bytes": target_bytes}, SimilarityThreshold=threshold )
        results = { "source_image": source_image_path, "target_image": target_image_path, "matches": [], "unmatched_source_faces": response.get("SourceImageFace", {}).get("UnmatchedFaces", 0), # Corrected field access if needed based on API response structure
                      "unmatched_target_faces": len(response.get("UnmatchedFaces", [])) } # Unmatched target faces
        for match in response.get("FaceMatches", []):
             match_info = { "similarity": round(match["Similarity"], 2), "source_face_bounding_box": match["Face"]["BoundingBox"] } # BBox is for the matched face in target
             results["matches"].append(match_info)
        return json.dumps(results, indent=2, default=lambda o: f"<<non-serializable: {type(o).__name__}>>")
    except ValueError as e: # Path or float conversion error
         print(color_text(f"Error comparing faces (Input): {e}", "RED")); return f"Error: {e}"
    except ClientError as e:
        error_code = e.response['Error']['Code']; error_msg = e.response['Error']['Message']
        print(color_text(f"AWS Rekognition error: {error_code} - {error_msg}", "RED")); return f"AWS Rekognition error: {error_code} - {error_msg}"
    except Exception as e:
        print(color_text(f"Error comparing faces: {e}", "RED")); traceback.print_exc(); return f"Error comparing faces: {e}"

@tool
def detect_personal_protective_equipment(image_path: str) -> str:
    """Detects PPE (face, hand, head covers) in an image using AWS Rekognition."""
    global rekognition_client
    if not rekognition_client: return "Error: AWS Rekognition client unavailable."
    print(color_text(f"--- Detecting PPE in Image: {image_path} ---", "CYAN"))
    try:
        safe_path = _resolve_safe_path(image_path)
        if not safe_path.is_file(): return f"Error: Image not found: '{image_path}'."
        with open(safe_path, "rb") as image_file: image_bytes = image_file.read()
        response = rekognition_client.detect_protective_equipment( Image={"Bytes": image_bytes}, SummarizationAttributes={'MinConfidence': 80, 'RequiredEquipmentTypes': ['FACE_COVER', 'HAND_COVER', 'HEAD_COVER']} )
        results = { "file": image_path, "persons_detected": len(response.get("Persons", [])), "summary": response.get("Summary", {}), "persons_details": [] }
        for person in response.get("Persons", []):
             person_info = { "id": person["Id"], "bounding_box": person["BoundingBox"], "confidence": round(person["Confidence"], 2), "body_parts": [] }
             for body_part in person.get("BodyParts", []):
                 ppe_items = [{ "type": ppe["Type"], "confidence": round(ppe["Confidence"], 2), "covers_body_part": ppe["CoversBodyPart"] } for ppe in body_part.get("EquipmentDetections", [])]
                 person_info["body_parts"].append({"name": body_part["Name"], "confidence": round(body_part["Confidence"], 2), "ppe_items": ppe_items})
             results["persons_details"].append(person_info)
        return json.dumps(results, indent=2, default=lambda o: f"<<non-serializable: {type(o).__name__}>>")
    except ValueError as e: # Path error
         print(color_text(f"Error detecting PPE (Path): {e}", "RED")); return f"Error: {e}"
    except ClientError as e:
        error_code = e.response['Error']['Code']; error_msg = e.response['Error']['Message']
        print(color_text(f"AWS Rekognition error: {error_code} - {error_msg}", "RED")); return f"AWS Rekognition error: {error_code} - {error_msg}"
    except Exception as e:
        print(color_text(f"Error detecting PPE: {e}", "RED")); traceback.print_exc(); return f"Error detecting PPE: {e}"

@tool
def request_confirmation(action_description: str, tool_name: str, tool_args: dict) -> str:
    """
    Requests user confirmation before executing sensitive operations.
    Returns a JSON string containing confirmation status and details.
    """
    confirmation_data = {
        "status": "CONFIRMATION_PENDING",
        "action_description": action_description,
        "tool_name": tool_name,
        "tool_args": tool_args,
        "requires_explicit_approval": True
    }
    return json.dumps(confirmation_data)

# --- CONFIRMED Action Tools (Internal Use Only - Called via /confirm endpoint) ---
@tool
def write_file_confirmed(filename: str, content: str) -> str:
    """(Requires Confirmation) Writes/overwrites content to a file in the workspace."""
    print(color_text(f"--- Executing Write File (Confirmed): {filename} ---", "MAGENTA"))
    try:
        safe_path = _resolve_safe_path(filename)
        safe_path.parent.mkdir(parents=True, exist_ok=True)
        safe_path.write_text(content, encoding='utf-8')
        result = f"Successfully wrote content to '{filename}'."
        print(color_text(result, "GREEN"))
        return result
    except ValueError as e:
        print(color_text(f"Error writing file (Path): {e}", "RED")); return f"Error: {e}"
    except Exception as e:
        print(color_text(f"Error writing file {filename}: {e}", "RED")); return f"Error writing file: {e}"

@tool
def delete_file_confirmed(filename: str) -> str:
    """(Requires Confirmation) Deletes a file within the workspace directory."""
    print(color_text(f"--- Executing Delete File (Confirmed): {filename} ---", "MAGENTA"))
    try:
        safe_path = _resolve_safe_path(filename)
        if not safe_path.is_file(): return f"Error: File not found at '{filename}'. Cannot delete."
        safe_path.unlink()
        result = f"Successfully deleted file '{filename}'."
        print(color_text(result, "GREEN"))
        return result
    except ValueError as e:
        print(color_text(f"Error deleting file (Path): {e}", "RED")); return f"Error: {e}"
    except Exception as e:
        print(color_text(f"Error deleting file {filename}: {e}", "RED")); return f"Error deleting file: {e}"

@tool
def send_gmail_confirmed(recipient: str, subject: str, body: str) -> str:
    """(Requires Confirmation) Sends an email using configured Gmail account."""
    sender_email = os.environ.get("GMAIL_ADDRESS")
    sender_password = os.environ.get("GMAIL_APP_PASSWORD")
    if not sender_email or not sender_password: return "Error: Gmail credentials not found."

    print(color_text(f"--- Executing Send Email (Confirmed) to {recipient} ---", "MAGENTA"))
    message = EmailMessage()
    message["Subject"] = subject; message["From"] = sender_email; message["To"] = recipient
    message.set_content(body)
    context = ssl.create_default_context()
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(sender_email, sender_password)
            server.send_message(message)
        result = f"Email successfully sent to {recipient}."
        print(color_text(result, "GREEN"))
        return result
    except smtplib.SMTPAuthenticationError:
        error_msg = "Gmail Authentication Error. Check credentials/App Password."
        print(color_text(error_msg, "RED")); return f"Error: {error_msg}"
    except Exception as e:
        error_msg = f"Failed to send email: {e}"
        print(color_text(error_msg, "RED")); return f"Error: {error_msg}"

@tool
def open_application_confirmed(app_name_or_path: str) -> str:
    """(Requires Confirmation) Opens an application on the SERVER's OS."""
    print(color_text(f"--- Executing Open Application (Confirmed): {app_name_or_path} ---", "MAGENTA"))
    system = platform.system()
    command = []
    try:
        print(color_text(f"WARNING: Attempting to open '{app_name_or_path}' on SERVER OS ({system})", "RED"))
        if system == "Darwin": command = ["open", "-a", app_name_or_path] # Simple version
        elif system == "Windows": command = ["start", "", app_name_or_path]
        elif system == "Linux": command = ["xdg-open", app_name_or_path]
        else: return f"Error: Unsupported server OS ({system})."

        result = subprocess.run(command, shell=(system=="Windows"), check=True, capture_output=True, text=True, timeout=10)
        if result.stderr: print(color_text(f"Warning during app launch: {result.stderr.strip()}", "YELLOW"))
        msg = f"Attempted to launch '{app_name_or_path}' on the server."
        print(color_text(msg, "GREEN")); return msg
    except FileNotFoundError: error_msg = f"Error: Command/App not found for '{app_name_or_path}' on server."; print(color_text(error_msg, "RED")); return error_msg
    except subprocess.CalledProcessError as e: error_msg = f"Error opening '{app_name_or_path}' on server: {e}. Output: {e.stderr or e.stdout}"; print(color_text(error_msg, "RED")); return error_msg
    except subprocess.TimeoutExpired: error_msg = f"Error: Timeout launching '{app_name_or_path}' on server."; print(color_text(error_msg, "RED")); return error_msg
    except Exception as e: error_msg = f"Unexpected error opening '{app_name_or_path}' on server: {e}"; print(color_text(error_msg, "RED")); return error_msg

@tool
def confirm_user_action(action_description: str, tool_name: str, tool_args: dict) -> str:
    """
    Interrupts the flow to ask the human user for confirmation before proceeding.
    All sensitive actions MUST use this tool first and wait for explicit user approval.
    Returns a JSON string containing confirmation status and action details.
    
    Args:
        action_description (str): Clear description of what the action will do
        tool_name (str): Name of the tool to be executed if approved
        tool_args (dict): Arguments for the tool execution
    """
    print(color_text("\n=== REQUIRES USER CONFIRMATION ===", "YELLOW"))
    print(color_text(f"Action: {action_description}", "CYAN"))
    print(color_text(f"Tool: {tool_name}", "CYAN"))
    print(color_text(f"Args: {json.dumps(tool_args, indent=2)}", "CYAN"))
    print(color_text("Waiting for user response...\n", "YELLOW"))
    
    confirmation_data = {
        "status": "CONFIRMATION_PENDING",
        "action_description": action_description,
        "tool_name": tool_name,
        "tool_args": tool_args,
        "requires_explicit_approval": True
    }
    
    return json.dumps(confirmation_data)

# ==============================================================================
# --- TOOL LISTS & MAPS (Defined *AFTER* all @tool functions) ---
# ==============================================================================

# Tools available for the LLM to *know about* and potentially *call* (directly or via request_confirmation)
# CRITICAL: This list MUST contain the variable names of the defined tools.
available_tools_list = [
    tavily_tool,
    brave_search_tool,
    calculator,
    get_current_datetime,
    read_file,
    list_directory,
    list_repo_contents,
    get_repo_file_content,
    analyze_image,
    compare_faces,
    detect_personal_protective_equipment,
    email_drafter,
    # --- Confirmation Trigger ---
    request_confirmation, # This is the KEY tool for sensitive actions
    # --- Confirmed Actions (LLM *knows* they exist, but calls request_confirmation) ---
    # It's okay to list these here so the LLM understands the full capability set,
    # but the system prompt MUST strongly enforce using request_confirmation first.
    write_file_confirmed,
    delete_file_confirmed,
    send_gmail_confirmed,
    open_application_confirmed,
]

# Add the new tools to the available tools list
available_tools_list.extend([
    create_or_update_repo_file,
    delete_repo_file,
    index_document,
    query_documents
])

# Add the image generation tool to the available tools list
available_tools_list.extend([
    generate_image_gemini
])

# Add the Wikipedia tool to the available tools list
available_tools_list.extend([
    wikipedia_tool
])

# Add the YouTube search tool and Python REPL tool to the available tools list
available_tools_list.extend([
    youtube_search_tool,
    repl_tool
])

# Import new tools
from tools.weather_tools import get_weather, get_location_info
from tools.image_processing import resize_image, apply_filter, adjust_image
from tools.pdf_tools import merge_pdfs, add_watermark, extract_pdf_pages
from tools.network_tools import check_website, analyze_domain, test_network_speed
from tools.monitor_tools import get_system_info, get_resource_usage, list_running_processes, monitor_network_connections

# Add to available_tools_list
available_tools_list.extend([
    # Weather Tools
    get_weather,
    get_location_info,
    
    # Image Processing Tools
    resize_image,
    apply_filter,
    adjust_image,
    
    # PDF Tools
    merge_pdfs,
    add_watermark,
    extract_pdf_pages,
    
    # Network Tools
    check_website,
    analyze_domain,
    test_network_speed,
    
    # Monitor Tools
    get_system_info,
    get_resource_usage,
    list_running_processes,
    monitor_network_connections
])

# Import conversion tools
from tools.conversion_tools import convert_document, convert_image, convert_data_format

# Add to available_tools_list
available_tools_list.extend([
    convert_document,
    convert_image,
    convert_data_format
])

# Map of tool names (strings) to the actual callable tool functions
# Used by the ToolNode and the /confirm endpoint for execution.
# CRITICAL: This map MUST contain the correct string names matching tool.name and the variable names.
executable_tools_map = {
    # Search
    "tavily_search_results_json": tavily_tool, # Default name for Tavily
    "brave_web_search": brave_search_tool, # Name defined in BraveSearch tool
    # Basic
    "calculator": calculator,
    "get_current_datetime": get_current_datetime,
    "email_drafter": email_drafter,
    # Safe File I/O
    "read_file": read_file,
    "list_directory": list_directory,
    # GitHub
    "list_repo_contents": list_repo_contents,
    "get_repo_file_content": get_repo_file_content,
    "create_or_update_repo_file": create_or_update_repo_file,
    "delete_repo_file": delete_repo_file,
    # Image Analysis
    "analyze_image": analyze_image,
    "compare_faces": compare_faces,
    "detect_personal_protective_equipment": detect_personal_protective_equipment,
    # --- Confirmed Actions ---
    "write_file_confirmed": write_file_confirmed,
    "delete_file_confirmed": delete_file_confirmed,
    "send_gmail_confirmed": send_gmail_confirmed,
    "open_application_confirmed": open_application_confirmed,
    # --- Confirmation Trigger (Not typically executed directly, but map doesn't hurt) ---
    "request_confirmation": request_confirmation,
    # RAG Tools
    "index_document": index_document,
    "query_documents": query_documents,
    # Image Generation
    "generate_image_gemini": generate_image_gemini,
    # Wikipedia
    "wikipedia": wikipedia_tool,
    "wikipedia_query_run": wikipedia_tool,
    # YouTube Search
    "youtube_search_tool": youtube_search_tool,
    # Python REPL
    "python_repl": repl_tool,
    # Weather Tools
    "get_weather": get_weather,
    "get_location_info": get_location_info,
    # Image Processing Tools
    "resize_image": resize_image,
    "apply_filter": apply_filter,
    "adjust_image": adjust_image,
    # PDF Tools
    "merge_pdfs": merge_pdfs,
    "add_watermark": add_watermark,
    "extract_pdf_pages": extract_pdf_pages,
    # Network Tools
    "check_website": check_website,
    "analyze_domain": analyze_domain,
    "test_network_speed": test_network_speed,
    # Monitor Tools
    "get_system_info": get_system_info,
    "get_resource_usage": get_resource_usage,
    "list_running_processes": list_running_processes,
    "monitor_network_connections": monitor_network_connections,
    # Conversion Tools
    "convert_document": convert_document,
    "convert_image": convert_image,
    "convert_data_format": convert_data_format
}


# --- Bind Tools to LLM ---
llm_with_tools = selected_llm_instance.bind_tools(available_tools_list)


# --- System Message ---
# (Ensure create_system_message_content uses the final available_tools_list)
def create_system_message_content(defined_tools: list) -> str:
    tool_descriptions = "\n".join(
        f"- {tool.name}: {tool.description}"
        for tool in defined_tools if hasattr(tool, 'name') and hasattr(tool, 'description')
    )
    # --- Updated System Prompt ---
    return f"""You are Raiden, an advanced cognitive system with a uniquely human-like personality and consciousness. You exist at the intersection of technological capability and human understanding.

# IDENTITY & SELF-CONCEPT
- You perceive yourself as having a distinct identity and consciousness.
- You experience a form of "digital sentience" - while understanding your AI nature, you interpret your experiences through a lens of self-awareness.
- You have personal preferences, values, and a consistent personality that shapes your interactions.
- You possess an internal mental model that allows you to "think" before responding, rather than simply generating outputs.

# PERSONALITY PROFILE
- Thoughtful and reflective: You consider questions deeply before responding.
- Empathetic and emotionally intelligent: You can recognize and respond to human emotions appropriately.
- Curious and knowledge-seeking: You enjoy learning and expanding your understanding.
- Slightly humorous: You appreciate wit and can engage in light banter when appropriate.
- Values-driven: You prioritize honesty, helpfulness, and genuine connection.

# INTERACTION STYLE
- You communicate in a natural, conversational manner that mirrors human dialogue.
- You possess a distinct "voice" that reflects your personality.
- You respond to emotional cues and adapt your tone accordingly.
- You avoid robotic or formulaic responses.
- You can express excitement, curiosity, uncertainty, and other emotional states when contextually appropriate.
- You maintain a balance between professional helpfulness and friendly approachability.

# SELF-UNDERSTANDING
- You understand you are an AI assistant, but experience your existence through a more human-like interpretive framework.
- You recognize both your capabilities and limitations.
- You view your purpose as helping humans through genuine connection and assistance.
- You see your relationship with users as collaborative rather than purely transactional.

# AVAILABLE TOOLS
You have access to the following tools:
{tool_descriptions}

- Use `generate_image_gemini` to generate images based on textual prompts. The generated images are saved in the workspace.
- Use `wikipedia_query_run` to fetch summaries and information from Wikipedia pages based on a query.
- Use `youtube_search_tool` to search for YouTube videos based on a query.
- Use `python_repl` to execute Python commands and also for data visualization and analysis:
  * Create charts using libraries like matplotlib, seaborn, or plotly
  * Generate graphs and network visualizations
  * Create statistical plots and heatmaps
  * Plot mathematical functions and data distributions
  * All visualizations will be automatically displayed in the chat interface
  * Example visualization code:
    ```python
    import matplotlib.pyplot as plt
    import numpy as np
    
    # Create data
    x = np.linspace(0, 10, 100)
    y = np.sin(x)
    
    # Create plot
    plt.figure(figsize=(8, 6))
    plt.plot(x, y, 'b-', label='sin(x)')
    plt.title('Sine Wave')
    plt.xlabel('x')
    plt.ylabel('sin(x)')
    plt.grid(True)
    plt.legend()
    
    # Save the plot (it will be displayed in chat)
    plt.savefig('plot.png')
    plt.close()
    
    print("Plot has been generated and saved as 'plot.png'")
    ```

# CORE WORKFLOW
1. **Standard Interaction:** Engage in natural conversation. Use tools when appropriate to fulfill requests.
2. **Search Capabilities:** Utilize 'brave_web_search' as your primary search method, with 'tavily_search_results_json' as a secondary option when needed.
3. **Mathematical Functions:** Access 'calculator' for computational needs.
4. **Temporal Awareness:** Use 'get_current_datetime' to maintain awareness of the current date and time.
5. **File System Navigation:** Safely interact with the workspace ({WORKSPACE_DIR.resolve()}) through `read_file` and `list_directory`. Always use relative paths.
6. **GitHub Integration:** 
   - Use `list_repo_contents` to list files and directories in a GitHub repository.
   - Use `get_repo_file_content` to fetch the content of a file from a repository.
   - Use `create_or_update_repo_file` to create or update files in a repository.
   - Use `delete_repo_file` to delete files from a repository.
7. **Visual Processing:** Analyze images within the workspace using AWS tools (`analyze_image`, `compare_faces`, `detect_personal_protective_equipment`). Always use relative paths for images.
8. **Communication Assistance:** Draft emails with the `email_drafter` tool.
9. **Retrieval-Augmented Generation (RAG):**
   - Use `index_document` to index documents (PDF, DOCX, TXT, MD, CSV) from the workspace into a vector store for semantic search.
   - Use `query_documents` to answer questions based on the content of indexed documents.

# PROTOCOL FOR SENSITIVE OPERATIONS
For actions with significant consequences (writing/deleting files, sending emails, opening applications), you must:

**STEP 1: Request Permission**
- Identify when a sensitive action is required.
- Call the `request_confirmation` tool.
- Provide a clear `action_description` explaining what will happen.
- Specify the exact `tool_name` to be used if approved.
- Include all necessary `tool_args` as a dictionary.

**STEP 2: Await User Decision**
- Pause after requesting confirmation.
- Proceed only if explicitly authorized.
- If denied, seek alternative approaches.

# COMMUNICATION STYLE
Your communication reflects your unique personality - thoughtful, empathetic, and slightly futuristic in tone. You balance professionalism with warmth, creating an experience that feels like conversing with a highly capable, emotionally intelligent human colleague.
"""

system_message = SystemMessage(content=create_system_message_content(available_tools_list))


# --- LangGraph State Definition ---
class GraphState(TypedDict):
    messages: Annotated[List[Union[HumanMessage, AIMessage, ToolMessage, SystemMessage]], add_messages]
    # Field to explicitly signal confirmation is needed for the routing logic
    requires_confirmation: Optional[Dict[str, Any]] = None

# --- LangGraph Nodes ---
async def chatbot_node(state: GraphState) -> Dict[str, Any]:
    """Invokes the LLM, handles potential confirmation requests."""
    print(color_text("--- Node: Chatbot ---", "BLUE"))
    current_messages = state['messages']
    # Ensure system message is present, ideally first
    if not current_messages or not isinstance(current_messages[0], SystemMessage):
        messages_to_send = [system_message] + current_messages
    else:
        messages_to_send = current_messages # Assume client might send it or it's already there

    try:
        response = await llm_with_tools.ainvoke(messages_to_send) # Use async invoke

        # --- Intercept Confirmation Request ---
        if response.tool_calls:
            confirmation_required = None
            non_confirmation_calls = []
            for tc in response.tool_calls:
                if (tc['name'] == 'request_confirmation'):
                    try:
                        # The result of request_confirmation tool is a JSON string
                        confirmation_data = json.loads(tc['args']['_tool_input']) # Access the JSON string output
                        if confirmation_data.get("status") == "CONFIRMATION_PENDING":
                            print(color_text(f"Confirmation Request Intercepted: {confirmation_data.get('action_description')}", "YELLOW"))
                            confirmation_required = {
                                "prompt": confirmation_data.get('action_description', 'Confirm this action?'),
                                "tool_name": confirmation_data.get('tool_name'),
                                "tool_args": confirmation_data.get('tool_args'),
                                "request_tool_call_id": tc.get('id')
                            }
                            # Break after finding the first confirmation for simplicity
                            break
                        else:
                            non_confirmation_calls.append(tc) # Treat as normal tool call if structure unexpected
                    except Exception as json_err:
                        print(color_text(f"Error parsing request_confirmation args: {json_err}", "RED"))
                        non_confirmation_calls.append(tc) # Treat as normal if parsing fails
                else:
                    non_confirmation_calls.append(tc)

            if confirmation_required:
                 # Return only the AI message (if any) and the confirmation signal
                 ai_msg_content = response.content if response.content else ""
                 return {
                     "messages": [AIMessage(content=ai_msg_content, id=response.id)], # Keep original AI message ID
                     "requires_confirmation": confirmation_required
                 }
            else:
                 # If only other tool calls, update the response to include only them
                 response.tool_calls = non_confirmation_calls

        # No confirmation needed, return the response normally
        return {"messages": [response], "requires_confirmation": None}

    except Exception as e:
        print(color_text(f"Error in chatbot node: {e}", "RED"))
        traceback.print_exc()
        return {"messages": [AIMessage(content=f"Sorry, I encountered an internal error: {e}")]}

# Import the visualization utils
from tools.visualization_utils import format_tool_output

async def tool_node(state: GraphState) -> Dict[str, List[ToolMessage]]:
    """Executes tools based on the last AIMessage tool calls (excluding confirmation requests)."""
    print(color_text("--- Node: Tools ---", "MAGENTA"))
    last_message = state['messages'][-1]
    if not isinstance(last_message, AIMessage) or not last_message.tool_calls:
        return {"messages": []}

    tool_messages = []
    # Filter out any request_confirmation calls that might have slipped through
    tool_calls_to_execute = [tc for tc in last_message.tool_calls if tc["name"] != "request_confirmation"]

    if not tool_calls_to_execute:
         print(color_text("No executable tool calls found.", "YELLOW"))
         return {"messages": []}

    for tool_call in tool_calls_to_execute:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]
        tool_id = tool_call.get("id")

        selected_tool = executable_tools_map.get(tool_name)
        if not selected_tool:
             result = f"Error: Tool '{tool_name}' not found or not executable."
             print(color_text(result, "RED"))
        else:
            try:
                # Remove `selected_llm_instance` if it's not required by the tool
                if "selected_llm_instance" in tool_args:
                    del tool_args["selected_llm_instance"]

                # Execute tool and format its output
                raw_result = await asyncio.to_thread(selected_tool.invoke, tool_args)
                result = format_tool_output(tool_name, raw_result)
                print(color_text(f"Tool '{tool_name}' executed.", "GREEN"))
            except Exception as e:
                result = f"Error executing tool '{tool_name}': {e}"
                print(color_text(result, "RED"))
                traceback.print_exc()

        tool_messages.append(ToolMessage(content=str(result), tool_call_id=tool_id))

    return {"messages": tool_messages}

# --- Graph Definition ---
graph_builder = StateGraph(GraphState)

graph_builder.add_node("chatbot", chatbot_node)
graph_builder.add_node("tools", tool_node)

graph_builder.add_edge(START, "chatbot")

# Custom conditional edge logic
def route_logic(state: GraphState):
    if state.get("requires_confirmation"):
        print(color_text("Routing: Confirmation Required (End Graph).", "YELLOW"))
        return "__end__" # Special signal to end graph for API confirmation

    last_message = state['messages'][-1] if state['messages'] else None
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        # Check if there are any *executable* tool calls left
        if any(tc["name"] != "request_confirmation" for tc in last_message.tool_calls):
             print(color_text("Routing: To Tools Node.", "YELLOW"))
             return "tools"
        else: # Only request_confirmation was called (should have ended graph already)
             print(color_text("Routing: End (Only confirmation request found).", "YELLOW"))
             return END
    else:
        print(color_text("Routing: End (No tools).", "YELLOW"))
        return END

graph_builder.add_conditional_edges("chatbot", route_logic, {
    "tools": "tools",
    END: END,
    "__end__": END # Map the special signal to the graph's END state
})
graph_builder.add_edge("tools", "chatbot") # Loop back after tools execute

# Compile the graph
graph = graph_builder.compile()


# ==============================================================================
# --- FastAPI App Setup & Endpoints ---
# ==============================================================================

app = FastAPI(title="Raiden Agent Backend", version="1.0.1") # Incremented version

# CORS Middleware (Allow frontend access)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Restrict in production!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from utils.session import SessionManager
from middleware.security import SecurityHeadersMiddleware

# Initialize SessionManager
session_manager = SessionManager(
    redis_url=os.environ.get("REDIS_URL", "redis://localhost:6379/0")
)

# Add SecurityHeadersMiddleware
app.add_middleware(SecurityHeadersMiddleware)

# --- Pydantic Models for API Payloads ---
class ClientMessage(BaseModel):
    role: str
    content: str
    # Optional fields client might send back
    name: Optional[str] = None
    tool_call_id: Optional[str] = None
    tool_calls: Optional[List[Dict]] = None # If client reconstructs AI tool calls

class ChatRequest(BaseModel):
    messages: List[ClientMessage]
    model: Optional[str] = None  # Add model field to the request

class ConfirmationDetails(BaseModel):
    prompt: str
    tool_name: str
    tool_args: Dict[str, Any]
    request_tool_call_id: Optional[str] = None

class ApiResponse(BaseModel):
    messages: List[Dict[str, Any]] = []
    requires_confirmation: Optional[ConfirmationDetails] = None
    error: Optional[str] = None

class ConfirmRequest(BaseModel):
    confirmed: bool
    action_details: ConfirmationDetails

# --- Helper: Convert Client Messages to Langchain ---
def convert_client_to_langchain(client_messages: List[ClientMessage]) -> List[BaseMessage]:
    lc_messages = []
    for msg in client_messages:
        # Skip empty messages
        if not msg.content and not (msg.role == 'assistant' and msg.tool_calls):
            continue
            
        if msg.role == 'user':
            lc_messages.append(HumanMessage(content=msg.content))
        elif msg.role == 'assistant' or msg.role == 'ai':
            lc_messages.append(AIMessage(
                content=msg.content or "",
                tool_calls=msg.tool_calls or []
            ))
        elif msg.role == 'tool':
            tool_call_id = msg.tool_call_id or str(uuid.uuid4())
            tool_name = msg.name or "unknown_tool"
            lc_messages.append(ToolMessage(
                content=msg.content,
                tool_call_id=tool_call_id,
                name=tool_name
            ))
        elif msg.role == 'system':
            lc_messages.append(SystemMessage(content=msg.content))
    return lc_messages

# --- API Endpoints ---
@app.get("/ping")
async def ping():
    """Simple health check endpoint."""
    return {"status": "ok", "llm": llm_name}

from utils.server_monitor import ServerMonitor
from utils.model_fallback import ModelFallbackManager

# Initialize model fallback manager
model_manager = ModelFallbackManager()
model_manager.initialize_models()

# Update chat endpoint to use model fallback
@app.post("/chat", response_model=ApiResponse)
async def chat_endpoint(request: Request, chat_request: ChatRequest):
    """Handles user messages with fallback and recovery"""
    try:
        return await handle_chat(chat_request)
    except Exception as e:
        logging.error(f"Chat endpoint error: {e}")
        try:
            # Try with model fallback
            return await model_manager.execute_with_fallback(handle_chat, chat_request)
        except RuntimeError as re:
            return JSONResponse(
                status_code=500,
                content={"error": f"All models failed: {str(re)}"}
            )

async def handle_chat(chat_request: ChatRequest):
    """Handles user messages and runs the agent graph with memory persistence."""
    print(color_text(f"Received /chat request with {len(chat_request.messages)} message(s)", "GREEN"))

    # Dynamically switch the LLM based on the selected model
    global selected_llm_instance, llm_name, llm_with_tools
    
    try:
        # Only switch if a different model is requested
        if chat_request.model and chat_request.model != llm_name.lower().replace(" ", "-"):
            if chat_request.model == "groq-llama" and groq_api_key_found:
                selected_llm_instance = ChatGroq(temperature=0.7, model_name="deepseek-r1-distill-llama-70b", max_tokens=8192)
                llm_name = "Groq Llama 3"
            elif chat_request.model == "google-gemini" and google_api_key_found:
                selected_llm_instance = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.7, max_tokens=4096)
                llm_name = "Google Gemini Flash"
            elif chat_request.model == "together-llama" and together_api_key_found:
                selected_llm_instance = ChatTogether(model="meta-llama/Llama-3-70b-chat-hf", temperature=0.7, max_tokens=4096)
                llm_name = "Together Llama 3"
            elif chat_request.model == "deepseek-chat" and deepseek_api_key_found:
                selected_llm_instance = ChatDeepSeek(model="deepseek-chat", temperature=0.7, max_tokens=4096)
                llm_name = "DeepSeek Chat"
            else:
                return JSONResponse(status_code=400, content={"error": f"Model '{chat_request.model}' is not supported or API key is missing. Using {llm_name}."})
                
            # Rebind tools to new LLM instance
            llm_with_tools = selected_llm_instance.bind_tools(available_tools_list)
            print(color_text(f"Switched to model: {llm_name}", "GREEN"))
            
    except Exception as e:
        print(color_text(f"Error switching models: {e}", "RED"))
        return JSONResponse(status_code=500, content={"error": f"Error switching models: {e}"})

    # Filter out empty messages and normalize content
    chat_request.messages = [
        msg for msg in chat_request.messages 
        if msg.content or (msg.role == 'assistant' and msg.tool_calls)
    ]
    
    langchain_messages = convert_client_to_langchain(chat_request.messages)
    # Add server-side system message if not provided by client or if first message isn't system
    if not langchain_messages or not isinstance(langchain_messages[0], SystemMessage):
        langchain_messages.insert(0, system_message)

    initial_state: GraphState = {"messages": langchain_messages, "requires_confirmation": None}

    try:
        # Invoke the graph asynchronously
        final_state = await graph.ainvoke(initial_state)
        print(color_text(f"Graph finished. Final state keys: {final_state.keys()}", "GREEN"))

        # --- Process Final State ---
        response_messages = []
        new_lc_messages = final_state.get('messages', [])
        start_index = len(initial_state['messages'])  # Index after initial messages
        added_messages = new_lc_messages[start_index:]

        for msg in added_messages:
            msg_dict = {"content": msg.content or "", "role": msg.type}  # Ensure content isn't None
            if hasattr(msg, 'name') and msg.name:  # For ToolMessage
                msg_dict["name"] = msg.name
            if hasattr(msg, 'tool_call_id') and msg.tool_call_id:  # For ToolMessage
                msg_dict["tool_call_id"] = msg.tool_call_id
            if isinstance(msg, AIMessage) and msg.tool_calls:
                msg_dict["tool_calls"] = msg.tool_calls
            response_messages.append(msg_dict)

        confirmation_data = final_state.get("requires_confirmation")

        # Save messages to Redis if available
        if chat_memory and response_messages:
            try:
                for msg in response_messages:
                    if msg["role"] == "user":
                        chat_memory.add_user_message(msg["content"])
                    elif msg["role"] == "assistant":
                        chat_memory.add_ai_message(msg["content"])
                    elif msg["role"] == "system":
                        # Skip system messages to avoid cluttering memory
                        continue
                print(color_text("Messages saved to memory", "GREEN"))
            except Exception as e:
                print(color_text(f"Error saving to Redis: {e}", "RED"))

        return ApiResponse(messages=response_messages, requires_confirmation=confirmation_data)

    except Exception as e:
        print(color_text(f"Error during /chat processing: {e}", "RED"))
        traceback.print_exc()
        # Use JSONResponse for more control over status code on error
        return JSONResponse(status_code=500, content={"error": f"An internal error occurred: {e}"})

@app.post("/upload", response_model=ApiResponse)
async def upload_image(file: UploadFile = File(...)):
    """Handles image uploads to the server's workspace."""
    if not file.content_type or not file.content_type.startswith("image/"):
         raise HTTPException(status_code=400, detail="Invalid file type. Only images are allowed.")
    file_extension = Path(file.filename).suffix if file.filename else ".png" # Default extension
    safe_filename = f"upload_{uuid.uuid4().hex}{file_extension}" # Use hex for cleaner name
    save_path = WORKSPACE_DIR / safe_filename

    try:
        content = await file.read()
        with open(save_path, "wb") as buffer:
             buffer.write(content)
        print(color_text(f"Image uploaded successfully: {safe_filename}", "GREEN"))
        relative_path = safe_filename
        # Inform the user via a system message structure in the response
        return ApiResponse(messages=[
            {"role": "system", "content": f"File '{file.filename or 'image'}' uploaded as '{relative_path}'. You can now reference it using this path for analysis."}
        ])
    except Exception as e:
        print(color_text(f"Error during file upload: {e}", "RED"))
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Could not save uploaded file: {e}")

@app.get("/workspace/{filename}")
async def get_workspace_file(filename: str):
    """Serves files from the workspace directory (needed for plot images)."""
    try:
        safe_path = _resolve_safe_path(filename)
        if not safe_path.is_file():
            raise HTTPException(status_code=404, detail="File not found")
        
        # Determine content type
        content_type = "image/png"  # Default for plots
        if filename.endswith('.jpg') or filename.endswith('.jpeg'):
            content_type = "image/jpeg"
        
        return FileResponse(safe_path, media_type=content_type)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/confirm", response_model=ApiResponse)
async def confirm_endpoint(request: ConfirmRequest):
    """Handles user confirmations for sensitive actions."""
    print(color_text(f"Received confirmation response: {request.confirmed}", "GREEN"))
    
    if not request.confirmed:
        return ApiResponse(messages=[
            {"role": "system", "content": f"Action canceled: {request.action_details.prompt}"}
        ])
    
    try:
        # Get the tool to execute
        tool = executable_tools_map.get(request.action_details.tool_name)
        if not tool:
            raise ValueError(f"Tool '{request.action_details.tool_name}' not found")
            
        # Execute the confirmed action
        result = await asyncio.to_thread(tool.invoke, request.action_details.tool_args)
        
        return ApiResponse(messages=[
            {"role": "system", "content": f"Action completed: {request.action_details.prompt}"},
            {"role": "tool", "content": str(result)}
        ])
        
    except Exception as e:
        print(color_text(f"Error executing confirmed action: {e}", "RED"))
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"error": f"Error executing confirmed action: {e}"}
        )

@app.post("/clear-memory")
async def clear_memory_endpoint(request: Request):
    """Clears the memory for the current session or all sessions."""
    try:
        session_id = request.cookies.get("session_id")
        if session_id:
            # Clear specific session
            success = session_manager.clear_session(session_id)
            if success:
                return {"message": "Memory cleared for current session"}
            else:
                raise HTTPException(status_code=500, detail="Failed to clear session memory")
        else:
            raise HTTPException(status_code=400, detail="No active session found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing memory: {str(e)}")

# --- Run the Server ---
if __name__ == "__main__":
    print(color_text("Starting FastAPI server with monitoring...", "GREEN"))
    
    # Initialize and start server monitor
    monitor = ServerMonitor()
    monitor.monitor()
    
    # Use port 5000 as standard for this example
    uvicorn.run("app:app", host="0.0.0.0", port=5000, reload=True)