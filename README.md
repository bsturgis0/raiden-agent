# 🤖 Raiden Agent

A powerful, versatile AI agent that combines state-of-the-art language models with a comprehensive suite of tools for desktop automation, knowledge management, and intelligent assistance.

## Key Features

🧠 **Multiple AI Models**
- Google Gemini Flash
- Groq Llama 3
- Together Llama 3
- DeepSeek Chat

⚡ **Core Capabilities**
- Natural language processing and understanding
- Context-aware responses
- Multi-turn conversations
- Tool-augmented intelligence

🛠️ **Integrated Tools**
- File & Document Management
- Code Analysis & Generation
- Image Analysis & Generation
- PDF Processing
- Network Tools
- System Monitoring
- Weather Information
- Data Format Conversion
- Media Processing
- GitHub Integration

## Getting Started

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
- Copy `.env.template` to `.env`
- Add your API keys and credentials

4. **Launch the Agent**
```bash
cd raiden+
python app.py
```

## Architecture

- **Backend**: FastAPI + LangChain
- **Frontend**: Modern web interface
- **Storage**: ChromaDB + Redis
- **Tools**: 25+ integrated capabilities

## Security Features

🔒 **Built-in Security**
- Secure API key storage
- Sandboxed execution
- Permission-based actions
- Request confirmation system

## Documentation

Detailed documentation is available in the `docs` directory:
- [Installation Guide](docs/installation.md)
- [API Reference](docs/api.md)
- [Tool Documentation](docs/tools.md)
- [Security Guide](docs/security.md)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to contribute to the project.

## License

This project is licensed under the MIT License - see [LICENSE](LICENSE) for details.