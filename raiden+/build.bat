@echo off
echo Building Raiden+ Desktop Application...

REM Check Python installation
python --version > nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo Error installing dependencies
    pause
    exit /b 1
)

REM Create build directories
echo Setting up build environment...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
mkdir dist\frontend
mkdir dist\tools

REM Copy necessary files
echo Copying files...
xcopy /s /e /y frontend\* dist\frontend\
xcopy /s /e /y tools\* dist\tools\

REM Create .env template
echo Creating .env template...
(
echo GOOGLE_API_KEY=your_google_api_key
echo GROQ_API_KEY=your_groq_api_key
echo TAVILY_API_KEY=your_tavily_api_key
echo BRAVE_SEARCH_API_KEY=your_brave_api_key
echo GITHUB_TOKEN=your_github_token
echo AWS_ACCESS_KEY_ID=your_aws_key_id
echo AWS_SECRET_ACCESS_KEY=your_aws_secret
echo GEMINI_API_KEY=your_gemini_api_key
) > dist\.env.template

REM Build the application
echo Building application...
python build.py
if errorlevel 1 (
    echo Build failed with error code %errorlevel%
    pause
    exit /b %errorlevel%
)

REM Create distribution package
echo Creating distribution package...
cd dist
powershell Compress-Archive -Path frontend,tools,.env.template,Raiden.exe -DestinationPath Raiden_Desktop_Package.zip
cd ..

echo Build complete! Check the dist folder for:
echo 1. Raiden.exe (Windows executable^)
echo 2. Raiden_Desktop_Package.zip (Complete package with dependencies^)
pause
