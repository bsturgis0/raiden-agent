# 🤖 Raiden Agent Desktop

The desktop version of Raiden Agent provides a seamless, native-like experience for interacting with the AI assistant.

## Features

### 🖥️ Desktop Integration
- System tray integration with custom Raiden icon
- Native desktop notifications
- File drag & drop support
- Cross-platform compatibility (Windows, macOS, Linux)

### 💻 User Interface
- Modern, responsive design
- Dark mode support
- Real-time status indicators
- Tool output visualization
- Code syntax highlighting

### 🔒 Security
- Secure credential storage using system keyring
- Sandboxed workspace
- Action confirmation system
- Encrypted API communication

## Installation

### Windows
1. Download the latest `RaidenSetup.exe`
2. Run the installer
3. Launch from Start Menu or desktop shortcut

### macOS
1. Download `Raiden.dmg`
2. Drag to Applications folder
3. Launch from Applications

### Linux
1. Download `Raiden.AppImage`
2. Make executable: `chmod +x Raiden.AppImage`
3. Run the AppImage

## Configuration

1. On first launch, configure your API keys:
   - Google API Key
   - Groq API Key
   - Other optional APIs

2. Set up your workspace directory (default: ~/RaidenWorkspace)

3. Configure system tray preferences

## System Requirements

- Windows 10/11 or
- macOS 10.14+ or
- Linux with GTK 3.0+
- 4GB RAM minimum
- 1GB free disk space
- Internet connection

## Troubleshooting

Common issues and solutions:

1. **System Tray Icon Not Showing**
   - Ensure system tray is enabled
   - Restart the application

2. **API Connection Issues**
   - Verify internet connection
   - Check API keys in settings
   - Confirm firewall settings

3. **Workspace Access**
   - Verify write permissions
   - Check disk space

## Support

For issues or questions:
1. Check the [FAQ](docs/faq.md)
2. Visit our [Support Forum](https://github.com/bsturgis0/raiden-agent/discussions)
3. Open an issue on GitHub

## Updates

The desktop app auto-updates by default. Manual updates available through:
- System tray menu
- Help → Check for Updates
- `--update` command line flag

## Development

Building from source:
```bash
python build.py
```

Creating installers:
```bash
python installer.py
```

## License

MIT License - see [LICENSE](LICENSE)
