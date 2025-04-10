#!/bin/bash

echo "Building Raiden+ Application..."

# Ensure we're in the right directory
cd "$(dirname "$0")"

# Install system dependencies if on Linux
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "Installing Linux dependencies..."
    sudo apt-get update
    sudo apt-get install -y \
        python3-dev \
        build-essential \
        libsqlite3-dev \
        python3.12-dev \
        libgtk-3-dev \
        libwebkit2gtk-4.0-dev \
        libglib2.0-dev \
        libappindicator3-dev \
        libgirepository1.0-dev \
        gir1.2-gtk-3.0 \
        gir1.2-webkit2-4.0
    pip install pysqlite3-binary
fi

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Create build environment
echo "Setting up build environment..."
mkdir -p dist
mkdir -p build
mkdir -p dist/frontend
mkdir -p dist/tools

# Copy necessary files
echo "Copying files..."
cp -r frontend/* dist/frontend/
cp -r tools/* dist/tools/

# Create .env template
echo "Creating .env template..."
cat > dist/.env.template << EOL
GOOGLE_API_KEY=your_google_api_key
GROQ_API_KEY=your_groq_api_key
TAVILY_API_KEY=your_tavily_api_key
BRAVE_SEARCH_API_KEY=your_brave_api_key
GITHUB_TOKEN=your_github_token
AWS_ACCESS_KEY_ID=your_aws_key_id
AWS_SECRET_ACCESS_KEY=your_aws_secret
GEMINI_API_KEY=your_gemini_api_key
EOL

# Build the application
echo "Building application..."
python build.py

# Create distribution package
echo "Creating distribution package..."
cd dist
zip -r Raiden_Desktop_Package.zip frontend tools .env.template Raiden* >/dev/null 2>&1

echo "Build complete! Check the dist folder for:"
echo "1. Raiden executable (platform specific)"
echo "2. Raiden_Desktop_Package.zip (Complete package with dependencies)"
