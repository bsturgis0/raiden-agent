# Tools Overview

## Core Tools

### Search Tools
- **Brave Search**: Web search using Brave's API
- **Tavily Search**: Enhanced search with summarization

### File Operations
- **File Reader**: Safe file reading within workspace
- **Directory Lister**: Workspace directory navigation
- **File Writer**: Confirmation-protected file writing

### Image Tools
- **Image Analysis**: AWS Rekognition integration
- **Face Comparison**: Face matching and analysis
- **PPE Detection**: Safety equipment detection
- **Image Generation**: Gemini-powered image creation

### Development Tools
- **Python REPL**: Live code execution
- **GitHub Integration**: Repository management
- **Code Analysis**: Static analysis and formatting

### Communication
- **Email Drafting**: Professional email composition
- **Weather Information**: Location-based weather data
- **PDF Processing**: Document manipulation

### Monitoring
- **System Monitor**: Resource usage tracking
- **Network Analysis**: Connection monitoring
- **Performance Metrics**: System statistics

## Tool Usage

Example using Python REPL:
```python
result = await python_repl.ainvoke({
    "command": "print('Hello Raiden')"
})
```

## Security Considerations

- All file operations are workspace-restricted
- Sensitive operations require confirmation
- API keys are securely stored
