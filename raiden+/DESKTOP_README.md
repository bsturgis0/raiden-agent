# Raiden+ Desktop Installation Guide

## Quick Start
1. Download the latest release of Raiden.exe
2. Create a folder called "Raiden" on your computer (e.g., C:\Raiden)
3. Place Raiden.exe in this folder
4. Create a file called `.env` in the same folder with your API keys (see Configuration below)
5. Double-click Raiden.exe to start the application

## Configuration
Create a file named `.env` with your API keys:

```env
GOOGLE_API_KEY=your_google_api_key
GROQ_API_KEY=your_groq_api_key
TAVILY_API_KEY=your_tavily_api_key
BRAVE_SEARCH_API_KEY=your_brave_api_key
GITHUB_TOKEN=your_github_token
AWS_ACCESS_KEY_ID=your_aws_key_id
AWS_SECRET_ACCESS_KEY=your_aws_secret
```

## First Launch
1. The first time you run Raiden.exe, you may see a Windows security warning
2. Click "More info" and then "Run anyway" to proceed
3. A new window will open with the Raiden+ interface
4. Your data and files will be stored in "RaidenWorkspace" in your home directory

## Troubleshooting
- If the application doesn't start, check that all required API keys are in the .env file
- Look for error messages in the raiden.log file
- Make sure you have internet connectivity

## Support
For help or issues, please visit our GitHub repository or contact support@raidenplus.com
