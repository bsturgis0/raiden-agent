# Installation Guide

## Prerequisites

- Python 3.9+
- Git
- Node.js (optional, for frontend development)
- Docker (optional, for containerized deployment)

## Quick Start

1. **Clone the Repository**
   ```bash
   git clone https://github.com/bsturgis0/raiden-agent.git
   cd raiden-agent
   ```

2. **Install Dependencies**
   ```bash
   pip install -r raiden+/requirements.txt
   ```

3. **Configure Environment**
   ```bash
   cp raiden+/.env.template raiden+/.env
   # Edit .env with your API keys
   ```

4. **Start Raiden**
   ```bash
   cd raiden+
   python app.py
   ```

## Desktop Application

See the [Desktop Installation Guide](desktop-installation.md) for instructions on installing the desktop version.

## Docker Installation

1. **Build the Image**
   ```bash
   docker build -t raiden-agent .
   ```

2. **Run the Container**
   ```bash
   docker run -p 5000:5000 -v ./workspace:/app/workspace raiden-agent
   ```

## Verification

To verify your installation:

1. Open http://localhost:5000 in your browser
2. The status should show "Connected"
3. Try a test command: "Hello Raiden"
