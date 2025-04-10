# Raiden+ Desktop Installation Guide

## Quick Start
1. Download and run the installer (RaidenSetup.exe) from the latest release
2. Follow the installation wizard
3. Start Raiden+ from your desktop or start menu
4. Configure your API keys and services in the Settings panel

## Configuration
Create or edit the `.env` file in your Raiden+ installation directory:

```env
# Required API Keys
GOOGLE_API_KEY=your_google_api_key
GROQ_API_KEY=your_groq_api_key
TAVILY_API_KEY=your_tavily_api_key
BRAVE_SEARCH_API_KEY=your_brave_api_key
GITHUB_TOKEN=your_github_token
AWS_ACCESS_KEY_ID=your_aws_key_id
AWS_SECRET_ACCESS_KEY=your_aws_secret
AWS_REGION=us-east-1

# Memory Management (Required for conversation history)
UPSTASH_REDIS_REST_URL=your_upstash_redis_url
UPSTASH_REDIS_REST_TOKEN=your_upstash_redis_token
UPSTASH_REDIS_TTL=86400
REDIS_PASSWORD=your_redis_password

# Optional Email Configuration
GMAIL_ADDRESS=your_email@gmail.com
GMAIL_APP_PASSWORD=your_app_password

# Optional Additional LLM APIs
TOGETHER_API_KEY=your_together_api_key
DEEPSEEK_API_KEY=your_deepseek_api_key
```

## Features
- Unified desktop application with embedded server
- System tray integration for quick access
- Native file dialogs for uploads
- Auto-start capability
- Persistent conversation memory using Redis
- Offline mode support with local fallback
- Secure API key storage
- Local file indexing and search
- Multiple LLM model support
- Built-in visualization tools

## Workspace Location
Your Raiden+ workspace will be created at:
- Windows: `C:\Users\<username>\RaidenWorkspace`
- macOS: `/Users/<username>/RaidenWorkspace`
- Linux: `/home/<username>/RaidenWorkspace`

## Build from Source
1. Clone the repository:
```bash
git clone https://github.com/yourusername/raiden-agent.git
cd raiden-agent/raiden+
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Build the desktop app:
```bash
# Windows
python build.py

# macOS/Linux
python3 build.py
```

4. Find the executable in the `dist` folder

## Troubleshooting
- If the application doesn't start:
  - Check that all required API keys are in the .env file
  - Look for error messages in `%APPDATA%\Raiden+\logs\raiden.log`
  - Ensure you have internet connectivity
  - Try running as administrator

- If you see a "Windows protected your PC" message:
  1. Click "More info"
  2. Click "Run anyway"
  3. The app is safe but not yet signed with a certificate

- If API keys are not being recognized:
  1. Open Settings in the app
  2. Click "Reset API Keys"
  3. Enter your keys again
  4. Click "Save and Restart"

## Security Features
- API keys are stored securely using system keyring
- Workspace encryption for sensitive data
- Sandboxed execution environment
- Network activity monitoring

## Updates
The application will automatically check for updates on startup. You can also:
1. Click the system tray icon
2. Select "Check for Updates"
3. Follow the update prompts if available

## Support
For help or issues:
- Visit our GitHub repository
- Open an issue for bugs
- Join our Discord community
- Email support@raidenplus.com

## Data Privacy
- All data is stored locally in your workspace
- No data is sent to external servers except API calls
- You can delete all data by removing the RaidenWorkspace folder
