# 🚀 SSH Web Terminal for Pwnagotchi Torch

![License](https://img.shields.io/badge/license-GPL3-blue.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)
![Pwnagotchi](https://img.shields.io/badge/pwnagotchi--torch-compatible-green.svg)
![Version](https://img.shields.io/badge/version-2.0.0-brightgreen.svg)

[![Easy Install](https://img.shields.io/badge/Install-One%20Command-red.svg?style=for-the-badge)](https://github.com/Pureach22/pwnagotchi-ssh-plugin#-quick-start)

A **modern, feature-rich SSH Web Terminal** plugin specifically designed for **pwnagotchi-torch-plugins**. Provides a beautiful, responsive web-based terminal interface with real-time command execution, session management, and advanced features.

---

## ⚡ TL;DR - Super Quick Install

```bash
curl -sSL https://raw.githubusercontent.com/Pureach22/pwnagotchi-ssh-plugin/main/install.sh | sudo bash
```

Then visit: `http://your-pwnagotchi-ip:8080/plugins/ssh/terminal` 🚀

---

## ⚡ One-Command Installation

```bash
curl -sSL https://raw.githubusercontent.com/Pureach22/pwnagotchi-ssh-plugin/main/install.sh | sudo bash
```

**Done!** Access your terminal at: `http://your-pwnagotchi-ip:8080/plugins/ssh/terminal`

## ✨ Features

### 🖥️ **Modern Web Terminal**
- **Real-time Terminal Emulation**: Full bash shell with pty support
- **Responsive Design**: Beautiful gradient UI that works on all devices
- **Command History**: Navigate through previous commands with arrow keys
- **Session Management**: Multiple concurrent terminal sessions
- **Auto-reconnect**: Automatic connection handling with error recovery
- **Fullscreen Mode**: Immersive terminal experience

### 🎨 **Beautiful Interface**
- **Modern Design**: Gradient backgrounds and smooth animations
- **Dark Theme**: GitHub-inspired dark terminal theme
- **Mobile Responsive**: Works perfectly on phones and tablets
- **Status Indicators**: Real-time connection and service status
- **Interactive Controls**: Easy-to-use buttons and keyboard shortcuts

### 🔒 **Advanced Security**
- **SSH Service Control**: Start/stop SSH daemon from web interface
- **Connection Monitoring**: Real-time SSH connection tracking
- **Session Isolation**: Secure terminal session management
- **Cross-platform**: Works on Linux (pty) and Windows (PowerShell fallback)

### 📊 **System Integration**
- **Pwnagotchi Display**: Shows SSH status on device screen
- **Service Management**: Complete SSH daemon control
- **Connection Analytics**: Track active SSH connections
- **Resource Monitoring**: Monitor terminal sessions and resources

## 📸 Screenshots

### 🏠 Dashboard
![Dashboard Preview](https://via.placeholder.com/800x500/667eea/ffffff?text=Modern+SSH+Dashboard)
*Modern dashboard with service status, connection monitoring, and quick actions*

### 💻 Web Terminal
![Terminal Preview](https://via.placeholder.com/800x500/0d1117/58a6ff?text=Full-Featured+Web+Terminal)
*Full-featured web terminal with command history and real-time output*

### 📱 Mobile Interface
![Mobile Preview](https://via.placeholder.com/400x700/667eea/ffffff?text=Mobile+Responsive+Design)
*Fully responsive design that works perfectly on mobile devices*

## 🚀 Quick Start

### 📦 Easy Installation (Recommended)

Install with a single command - just like pwnagotchi-torch-plugins:

```bash
curl -sSL https://raw.githubusercontent.com/Pureach22/pwnagotchi-ssh-plugin/main/install.sh | sudo bash
```

**That's it!** The script will automatically:
- ✅ Download and install the plugin
- ✅ Install minimal Python dependencies
- ✅ Configure Pwnagotchi
- ✅ Enable SSH service
- ✅ Restart Pwnagotchi

*No system packages modified - uses existing Pwnagotchi infrastructure!*

### 🔄 Alternative Installation Methods

#### Method 1: Direct Download + Install
```bash
# Download and run installer
wget https://raw.githubusercontent.com/Pureach22/pwnagotchi-ssh-plugin/main/install.sh
sudo chmod +x install.sh
sudo ./install.sh
```

#### Method 2: Git Clone + Install
```bash
# Clone repository and install
git clone https://github.com/Pureach22/pwnagotchi-ssh-plugin.git
cd pwnagotchi-ssh-plugin
sudo ./install.sh
```

### 🔧 Manual Installation

For advanced users who prefer manual control:

```bash
# 1. Clone the repository
git clone https://github.com/Pureach22/pwnagotchi-ssh-plugin.git
cd pwnagotchi-ssh-plugin

# 2. Run installation script
sudo ./install.sh

# OR install manually:
sudo pip3 install flask jinja2 psutil paramiko cryptography
sudo cp ssh.py /usr/local/share/pwnagotchi/custom-plugins/
echo "main.plugins.ssh.enabled = true" | sudo tee -a /etc/pwnagotchi/config.toml
sudo systemctl enable ssh
sudo systemctl restart pwnagotchi
```

### Quick Access

Once installed, access your web terminal at:

```
🌐 Dashboard: http://your-pwnagotchi-ip:8080/plugins/ssh/
💻 Terminal:  http://your-pwnagotchi-ip:8080/plugins/ssh/terminal
```

## ⚙️ Configuration

Add these settings to your `/etc/pwnagotchi/config.toml`:

```toml
# SSH Web Terminal Configuration
[main.plugins.ssh]
enabled = true
display_on_screen = true
ssh_x_coord = 160
ssh_y_coord = 66
auto_start_ssh = true
enable_web_terminal = true
terminal_theme = "dark"
max_sessions = 5
```

### Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| `enabled` | `true` | Enable/disable the plugin |
| `display_on_screen` | `true` | Show SSH status on Pwnagotchi screen |
| `ssh_x_coord` | `160` | X coordinate for screen display |
| `ssh_y_coord` | `66` | Y coordinate for screen display |
| `auto_start_ssh` | `true` | Automatically start SSH service |
| `enable_web_terminal` | `true` | Enable web terminal interface |
| `terminal_theme` | `"dark"` | Terminal color theme |
| `max_sessions` | `5` | Maximum concurrent terminal sessions |

## 🛠️ Usage

### 🌐 Web Interface

1. **Dashboard Access**: Navigate to `http://your-pwnagotchi:8080/plugins/ssh/`
2. **Service Control**: Start/stop SSH service with one click
3. **Connection Monitoring**: View active SSH connections in real-time
4. **Terminal Access**: Launch web terminal directly from dashboard

### 💻 Web Terminal

1. **Auto-Connect**: Terminal automatically connects when page loads
2. **Command Execution**: Type commands and press Enter
3. **History Navigation**: Use ↑↓ arrow keys for command history
4. **Keyboard Shortcuts**:
   - `Ctrl+C`: Send interrupt signal
   - `↑/↓`: Navigate command history
   - `F11`: Toggle fullscreen mode

### 📱 Mobile Usage

- **Responsive Design**: Works perfectly on mobile browsers
- **Touch-Friendly**: Large buttons and easy navigation
- **Portrait/Landscape**: Adapts to screen orientation
- **iOS/Android**: Compatible with all mobile platforms

## 🔧 API Reference

### SSH Service Control

```http
GET  /plugins/ssh/api/ssh/status     # Get SSH service status
POST /plugins/ssh/api/ssh/start      # Start SSH service
POST /plugins/ssh/api/ssh/stop       # Stop SSH service
```

### Terminal Management

```http
POST /plugins/ssh/api/terminal/create              # Create new terminal session
POST /plugins/ssh/api/terminal/{id}/input          # Send input to terminal
GET  /plugins/ssh/api/terminal/{id}/output         # Get terminal output
POST /plugins/ssh/api/terminal/{id}/resize         # Resize terminal window
POST /plugins/ssh/api/terminal/{id}/close          # Close terminal session
GET  /plugins/ssh/api/terminal/{id}/history        # Get command history
```

### Example API Usage

```javascript
// Create terminal session
const response = await fetch('/plugins/ssh/api/terminal/create', {
    method: 'POST'
});
const data = await response.json();
const sessionId = data.session_id;

// Send command
await fetch(`/plugins/ssh/api/terminal/${sessionId}/input`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ input: 'ls -la\\n' })
});

// Get output
const output = await fetch(`/plugins/ssh/api/terminal/${sessionId}/output`);
const result = await output.json();
console.log(result.output);
```

## 🏗️ Architecture

### Plugin Structure

```
ssh.py
├── WebTerminalSession      # Individual terminal session management
├── WebTerminalManager      # Multi-session management
└── SSH (Plugin)           # Main Pwnagotchi plugin class
    ├── Dashboard          # Web UI dashboard
    ├── Terminal Interface # Web terminal page
    └── API Endpoints      # REST API for all operations
```

### Session Management

- **Multi-session Support**: Handle multiple concurrent terminals
- **Auto-cleanup**: Automatic cleanup of dead/inactive sessions
- **Cross-platform**: Linux (pty) and Windows (subprocess) support
- **Resource Management**: Efficient memory and process handling

### Security Features

- **Session Isolation**: Each terminal session is isolated
- **Timeout Handling**: Sessions automatically timeout after inactivity
- **Error Recovery**: Robust error handling and recovery mechanisms
- **Input Validation**: Secure input processing and validation

## 🧪 Development

### Local Development

```bash
# Clone repository
git clone https://github.com/Pureach22/pwnagotchi-ssh-plugin.git
cd pwnagotchi-ssh-plugin

# Install development dependencies
pip3 install -r requirements.txt
pip3 install pytest black flake8

# Run tests
pytest tests/

# Format code
black ssh.py

# Lint code
flake8 ssh.py
```

### Testing

```bash
# Unit tests
pytest tests/test_terminal.py

# Integration tests
pytest tests/test_api.py

# End-to-end tests
pytest tests/test_e2e.py
```

## 🐛 Troubleshooting

### Common Issues

**❌ Plugin not loading**
```bash
# Check Pwnagotchi logs
sudo journalctl -u pwnagotchi -f | grep ssh

# Verify plugin location
ls -la /usr/local/share/pwnagotchi/custom-plugins/ssh.py
```

**❌ Terminal not connecting**
```bash
# Check if SSH service is running
sudo systemctl status ssh

# Test API endpoint
curl http://localhost:8080/plugins/ssh/api/terminal/create
```

**❌ Dependencies missing**
```bash
# Install missing packages
sudo apt install python3-dev python3-pip
sudo pip3 install -r requirements.txt
```

**❌ Permission denied**
```bash
# Fix SSH permissions
sudo systemctl enable ssh
sudo ufw allow ssh
```

### Debug Mode

Enable debug logging in your config:

```toml
[main]
log_level = "DEBUG"

[main.plugins.ssh]
enabled = true
debug = true
```

## 🔄 Version History

### v2.0.0 (Latest)
- ✨ Complete rewrite with modern UI
- 🚀 Enhanced terminal emulation
- 📱 Mobile-responsive design
- 🔧 Improved API endpoints
- 🛡️ Better security and error handling

### v1.0.0
- 🎉 Initial release
- 💻 Basic web terminal
- 🔧 SSH service control
- 📊 Connection monitoring

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Workflow

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/amazing-feature`
3. **Commit** your changes: `git commit -m 'Add amazing feature'`
4. **Push** to the branch: `git push origin feature/amazing-feature`
5. **Open** a Pull Request

### Code Standards

- **Python**: Follow PEP 8 style guide
- **JavaScript**: Use modern ES6+ features
- **CSS**: Use consistent naming conventions
- **Documentation**: Update README for new features

## 📋 Requirements

### System Requirements

- **Pwnagotchi**: Latest torch version
- **Python**: 3.8 or higher
- **RAM**: Minimum 512MB available
- **Storage**: 50MB for plugin and dependencies

### Dependencies

```bash
# Core dependencies
flask>=2.2.0
jinja2>=3.1.0
psutil>=5.9.0
paramiko>=2.11.0
cryptography>=3.4.8

# Terminal utilities
ptyprocess>=0.7.0
pexpect>=4.8.0
```

## 📄 License

This project is licensed under the **GPL-3.0 License** - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- 🎯 **[Pwnagotchi Project](https://pwnagotchi.ai/)** - Amazing platform
- 🔥 **[jayofelony](https://github.com/jayofelony)** - Pwnagotchi Torch maintainer
- 👥 **Community Contributors** - Thank you for your support!
- 🎨 **Design Inspiration** - GitHub's terminal and VS Code themes

## 📞 Support & Community

- 🐛 **Issues**: [GitHub Issues](https://github.com/Pureach22/pwnagotchi-ssh-plugin/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/Pureach22/pwnagotchi-ssh-plugin/discussions)
- 🌐 **Community**: [Pwnagotchi Discord](https://discord.gg/pwnagotchi)
- 📧 **Email**: support@pwnagotchi-plugins.dev

## 🌟 Star History

[![Star History Chart](https://api.star-history.com/svg?repos=Pureach22/pwnagotchi-ssh-plugin&type=Date)](https://star-history.com/#Pureach22/pwnagotchi-ssh-plugin&Date)

---

<div align="center">

**Made with ❤️ for the Pwnagotchi Community**

![Pwnagotchi](https://img.shields.io/badge/Built%20for-Pwnagotchi%20Torch-ff69b4.svg?style=for-the-badge)

**⭐ Star this repository if you find it useful!**

</div>