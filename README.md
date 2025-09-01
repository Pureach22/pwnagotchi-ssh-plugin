# Pwnagotchi SSH Plugin

![License](https://img.shields.io/badge/license-GPL3-blue.svg)
![Python](https://img.shields.io/badge/python-3.7%2B-blue.svg)
![Pwnagotchi](https://img.shields.io/badge/pwnagotchi-compatible-green.svg)

A comprehensive SSH management plugin for Pwnagotchi that provides WebUI-based SSH server control, key management, and connection monitoring.

## 🚀 Features

### 🖥️ Display Integration
- **Real-time Status**: SSH service status on Pwnagotchi screen
- **Connection Count**: Shows number of active SSH connections
- **Configurable Position**: Customizable display coordinates

### 🌐 WebUI Management
- **Dashboard**: Service control and connection monitoring
- **Configuration**: SSH server settings management
- **Key Management**: Add/remove SSH public keys
- **REST API**: Programmatic control endpoints

### 🔒 Security Features
- **Key-only Authentication**: Disable password authentication
- **Connection Monitoring**: Real-time active connection tracking
- **Fail2ban Integration**: Brute force protection
- **Secure Key Management**: WebUI-based SSH key administration

## 📸 Screenshots

### Dashboard
Service status, connection monitoring, and control interface.

### Configuration
SSH server settings and security options.

### Key Management
Add, remove, and manage SSH public keys.

## 🛠️ Quick Installation

### Option 1: Automated Installation (Recommended)
```bash
# Download and run the installation script
wget https://raw.githubusercontent.com/your-username/pwnagotchi-ssh-plugin/main/install.sh
sudo bash install.sh
```

### Option 2: Manual Installation
```bash
# 1. Download the plugin
wget https://raw.githubusercontent.com/your-username/pwnagotchi-ssh-plugin/main/ssh_plugin.py

# 2. Copy to plugins directory
sudo cp ssh_plugin.py /usr/local/lib/python3.*/dist-packages/pwnagotchi/plugins/default/

# 3. Install dependencies
sudo pip3 install paramiko psutil cryptography

# 4. Add configuration to /etc/pwnagotchi/config.toml
echo "main.plugins.ssh.enabled = true" | sudo tee -a /etc/pwnagotchi/config.toml

# 5. Restart Pwnagotchi
sudo systemctl restart pwnagotchi
```

## ⚙️ Configuration

Add these settings to your `/etc/pwnagotchi/config.toml`:

```toml
# SSH Plugin Configuration
main.plugins.ssh.enabled = true
main.plugins.ssh.port = 22
main.plugins.ssh.max_connections = 5
main.plugins.ssh.auto_start = true
main.plugins.ssh.key_auth_only = true
main.plugins.ssh.display_on_screen = true
main.plugins.ssh.ssh_x_coord = 160
main.plugins.ssh.ssh_y_coord = 80
```

## 🌐 WebUI Access

Once installed, access the SSH management interface at:
```
http://your-pwnagotchi-ip:8080/plugins/ssh/
```

## 📱 Display Status

The plugin shows SSH status on your Pwnagotchi screen:
- **`OFF`** - SSH service is stopped
- **`ON`** - SSH service running, no connections
- **`[N]`** - SSH service running with N active connections

## 🔧 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/plugins/ssh/api/status` | GET | Get SSH service status |
| `/plugins/ssh/api/start` | POST | Start SSH service |
| `/plugins/ssh/api/stop` | POST | Stop SSH service |
| `/plugins/ssh/api/connections` | GET | Get active connections |

## 🔒 Security Best Practices

### SSH Key Setup
```bash
# Generate SSH key pair
ssh-keygen -t ed25519 -C "your-email@example.com"

# Copy public key to Pwnagotchi (replace with your key)
echo "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIJbR... your-email@example.com" >> ~/.ssh/authorized_keys
```

### Additional Security
- Use non-standard SSH ports if exposed to internet
- Implement firewall rules for SSH access
- Regular key rotation and access review
- Monitor authentication attempts

## 📂 Project Structure

```
pwnagotchi-ssh-plugin/
├── ssh_plugin.py          # Main plugin file
├── install.sh             # Automated installer
├── config_example.toml    # Configuration examples
├── requirements.txt       # Python dependencies
├── test_plugin.py         # Plugin validation tests
├── INSTALLATION.md        # Detailed installation guide
└── PROJECT_SUMMARY.md     # Complete project overview
```

## 🧪 Testing

Validate the plugin before installation:
```bash
python3 test_plugin.py
```

## 📖 Documentation

- **[Installation Guide](INSTALLATION.md)** - Detailed setup instructions
- **[Project Summary](PROJECT_SUMMARY.md)** - Complete feature overview
- **[Configuration Examples](config_example.toml)** - Sample configurations

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit changes: `git commit -am 'Add feature'`
4. Push to branch: `git push origin feature-name`
5. Submit a Pull Request

## 🐛 Troubleshooting

### Common Issues

**Plugin not loading:**
```bash
# Check Pwnagotchi logs
sudo journalctl -u pwnagotchi -f
```

**SSH service issues:**
```bash
# Check SSH status
sudo systemctl status ssh

# Test configuration
sudo sshd -t
```

**WebUI access problems:**
```bash
# Verify WebUI is running
curl http://localhost:8080/plugins/ssh/
```

## 📋 Requirements

- **Pwnagotchi**: Latest version
- **Python**: 3.7+
- **Dependencies**: paramiko, psutil, cryptography
- **SSH Server**: OpenSSH (automatically installed)

## 📄 License

This project is licensed under the GPL-3.0 License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Pwnagotchi Project](https://pwnagotchi.ai/) - For the amazing platform
- [evilsocket](https://github.com/evilsocket) - Original Pwnagotchi creator
- [jayofelony](https://github.com/jayofelony) - Pwnagotchi Torch maintainer
- Community contributors and testers

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/your-username/pwnagotchi-ssh-plugin/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-username/pwnagotchi-ssh-plugin/discussions)
- **Community**: [Pwnagotchi Community](https://pwnagotchi.ai/community/)

---

**Made with ❤️ for the Pwnagotchi community**

![Pwnagotchi](https://img.shields.io/badge/Built%20for-Pwnagotchi-ff69b4.svg?style=for-the-badge)