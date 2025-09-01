# Pwnagotchi SSH Plugin

![License](https://img.shields.io/badge/license-GPL3-blue.svg)
![Python](https://img.shields.io/badge/python-3.7%2B-blue.svg)
![Pwnagotchi](https://img.shields.io/badge/pwnagotchi-compatible-green.svg)

A comprehensive SSH management plugin for Pwnagotchi that provides WebUI-based SSH server control, key management, and connection monitoring.

**📦 Repository**: https://github.com/Pureach22/pwnagotchi-ssh-plugin

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

## 🛠️ Installation

### Manual Installation
```bash
# 1. Clone the repository
git clone https://github.com/Pureach22/pwnagotchi-ssh-plugin.git
cd pwnagotchi-ssh-plugin

# 2. Install dependencies using apt (recommended)
sudo apt update
sudo apt install python3-paramiko python3-psutil python3-cryptography

# 3. Copy to custom plugins directory
sudo mkdir -p /usr/local/share/pwnagotchi/custom-plugins/
sudo cp ssh_plugin.py /usr/local/share/pwnagotchi/custom-plugins/

# 4. Add configuration to /etc/pwnagotchi/config.toml
echo "main.plugins.ssh.enabled = true" | sudo tee -a /etc/pwnagotchi/config.toml

# 5. Restart Pwnagotchi
sudo systemctl restart pwnagotchi
```

### Alternative: Direct Download
```bash
# Create custom plugins directory
sudo mkdir -p /usr/local/share/pwnagotchi/custom-plugins/

# Download plugin file directly
sudo wget -O /usr/local/share/pwnagotchi/custom-plugins/ssh_plugin.py \
  https://raw.githubusercontent.com/Pureach22/pwnagotchi-ssh-plugin/main/ssh_plugin.py

# Install dependencies using apt (recommended)
sudo apt update
sudo apt install python3-paramiko python3-psutil python3-cryptography

# Enable plugin in config
echo "main.plugins.ssh.enabled = true" | sudo tee -a /etc/pwnagotchi/config.toml

# Restart service
sudo systemctl restart pwnagotchi
```

### Alternative: Using pip with override (not recommended)
```bash
# Only if apt packages are not available
sudo pip3 install paramiko psutil cryptography --break-system-packages
```

## ⚙️ Configuration

**Note**: This plugin should be installed in `/usr/local/share/pwnagotchi/custom-plugins/` for custom plugins.

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
├── requirements.txt       # Python dependencies
├── README.md             # This documentation
└── .gitignore            # Git ignore rules
```

**Installation Location**: `/usr/local/share/pwnagotchi/custom-plugins/ssh_plugin.py`

## 🧪 Testing

You can test the plugin functionality by examining the source code and following the installation steps.

## 📖 Documentation

For detailed information about the plugin features and configuration options, see the source code comments in `ssh_plugin.py`.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit changes: `git commit -am 'Add feature'`
4. Push to branch: `git push origin feature-name`
5. Submit a Pull Request

## 🐛 Troubleshooting

### Common Issues

**"externally-managed-environment" error:**
```bash
# Use apt instead of pip for system packages
sudo apt install python3-paramiko python3-psutil python3-cryptography

# OR override pip (not recommended)
sudo pip3 install paramiko psutil cryptography --break-system-packages
```

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
- **Dependencies**: 
  - `python3-paramiko` (SSH client library)
  - `python3-psutil` (System monitoring)
  - `python3-cryptography` (Cryptographic functions)
- **SSH Server**: OpenSSH (automatically installed)

### Installing Dependencies

**Recommended (using apt):**
```bash
sudo apt install python3-paramiko python3-psutil python3-cryptography
```

**Alternative (using pip):**
```bash
sudo pip3 install paramiko psutil cryptography --break-system-packages
```

## 📄 License

This project is licensed under the GPL-3.0 License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Pwnagotchi Project](https://pwnagotchi.ai/) - For the amazing platform
- [evilsocket](https://github.com/evilsocket) - Original Pwnagotchi creator
- [jayofelony](https://github.com/jayofelony) - Pwnagotchi Torch maintainer
- Community contributors and testers

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/Pureach22/pwnagotchi-ssh-plugin/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Pureach22/pwnagotchi-ssh-plugin/discussions)
- **Community**: [Pwnagotchi Community](https://pwnagotchi.ai/community/)

---

**Made with ❤️ for the Pwnagotchi community**

![Pwnagotchi](https://img.shields.io/badge/Built%20for-Pwnagotchi-ff69b4.svg?style=for-the-badge)