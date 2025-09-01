# Pwnagotchi SSH Plugin Installation Guide

## Overview
This SSH plugin provides comprehensive SSH server management and monitoring capabilities through the Pwnagotchi WebUI. It allows you to:

- Start/stop SSH service remotely
- Monitor active SSH connections
- Manage SSH keys through the web interface
- Configure SSH server settings

## Installation

### 1. Plugin Installation

Copy the SSH plugin file to your Pwnagotchi plugins directory:

```bash
# Method 1: Direct copy
sudo cp ssh_plugin.py /usr/local/lib/python3.*/dist-packages/pwnagotchi/plugins/default/

# Method 2: Using custom plugins directory
sudo mkdir -p /opt/pwnagotchi/plugins
sudo cp ssh_plugin.py /opt/pwnagotchi/plugins/
```

### 2. Install Dependencies

Install the required Python packages:

```bash
sudo pip3 install paramiko psutil cryptography
```

### 3. Configuration

Add the following configuration to your `/etc/pwnagotchi/config.toml`:

```toml
# SSH Plugin Configuration
main.plugins.ssh.enabled = true
main.plugins.ssh.port = 22
main.plugins.ssh.max_connections = 5
main.plugins.ssh.display_position = "160,80"
main.plugins.ssh.auto_start = true
main.plugins.ssh.key_auth_only = true
main.plugins.ssh.webui_path = "/ssh"
main.plugins.ssh.display_on_screen = true
main.plugins.ssh.ssh_x_coord = 160
main.plugins.ssh.ssh_y_coord = 80
```

#### Configuration Options

- `enabled`: Enable/disable the SSH plugin
- `port`: SSH server port (default: 22)
- `max_connections`: Maximum concurrent SSH connections
- `display_position`: Position of SSH status on screen (x,y coordinates)
- `auto_start`: Automatically start SSH service on boot
- `key_auth_only`: Only allow SSH key authentication (disable passwords)
- `webui_path`: WebUI path for SSH management (default: /ssh)
- `display_on_screen`: Show SSH status on Pwnagotchi display
- `ssh_x_coord`: X coordinate for SSH status display
- `ssh_y_coord`: Y coordinate for SSH status display

### 4. SSH Server Setup

Ensure SSH server is installed and properly configured:

```bash
# Install SSH server if not already installed
sudo apt update
sudo apt install openssh-server

# Enable SSH service
sudo systemctl enable ssh

# Create SSH directory for keys
mkdir -p ~/.ssh
chmod 700 ~/.ssh
```

### 5. Security Configuration

For enhanced security, configure SSH to use key-only authentication:

```bash
# Edit SSH configuration
sudo nano /etc/ssh/sshd_config

# Add or modify these lines:
PasswordAuthentication no
PubkeyAuthentication yes
PermitRootLogin no
MaxAuthTries 3
ClientAliveInterval 300
ClientAliveCountMax 2
```

## Usage

### WebUI Access

Once the plugin is installed and configured, access the SSH management interface through:

```
http://your-pwnagotchi-ip:8080/plugins/ssh/
```

### WebUI Features

#### 1. Dashboard (`/plugins/ssh/`)
- View SSH service status (Running/Stopped)
- See active SSH connections with details
- Start/stop SSH service

#### 2. Configuration (`/plugins/ssh/config`)
- Change SSH port
- Set maximum connections
- Enable/disable key-only authentication
- Configure auto-start behavior

#### 3. SSH Keys Management (`/plugins/ssh/keys`)
- Add new SSH public keys
- Remove existing keys
- View all authorized keys
- Manage key names and metadata

### Display Integration

The plugin shows SSH status on the Pwnagotchi screen:
- `OFF`: SSH service is stopped
- `ON`: SSH service is running with no active connections
- `[number]`: Number of active SSH connections

### API Endpoints

The plugin provides REST API endpoints for programmatic access:

- `GET /plugins/ssh/api/status` - Get SSH service status
- `POST /plugins/ssh/api/start` - Start SSH service
- `POST /plugins/ssh/api/stop` - Stop SSH service
- `GET /plugins/ssh/api/connections` - Get active connections

## Security Considerations

### SSH Key Management
- Always use SSH keys instead of passwords
- Regularly rotate SSH keys
- Remove unused keys promptly
- Use strong, unique keys for each device

### Network Security
- Change default SSH port if exposed to internet
- Use firewall rules to restrict access
- Monitor authentication logs regularly
- Implement fail2ban for brute force protection

### Access Control
- Limit maximum concurrent connections
- Use strong usernames (avoid 'root', 'admin', etc.)
- Regularly review authorized keys
- Monitor active sessions

## Troubleshooting

### Common Issues

#### Plugin Not Loading
```bash
# Check plugin directory
ls -la /usr/local/lib/python3.*/dist-packages/pwnagotchi/plugins/default/ssh_plugin.py

# Check Pwnagotchi logs
sudo journalctl -u pwnagotchi -f
```

#### SSH Service Issues
```bash
# Check SSH service status
sudo systemctl status ssh

# View SSH logs
sudo journalctl -u ssh -f

# Test SSH configuration
sudo sshd -t
```

#### Permission Issues
```bash
# Fix SSH directory permissions
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys

# Fix SSH configuration permissions
sudo chmod 644 /etc/ssh/sshd_config
```

#### WebUI Access Issues
```bash
# Check if WebUI is running
curl http://localhost:8080/plugins/ssh/

# Check Pwnagotchi WebUI logs
sudo journalctl -u pwnagotchi -f | grep ssh
```

### Debug Mode

Enable debug logging by adding to config.toml:

```toml
main.log.level = "DEBUG"
```

## Advanced Features

### Custom SSH Keys Location
```bash
# Use custom location for authorized keys
sudo mkdir -p /opt/pwnagotchi/ssh-keys
sudo chown pi:pi /opt/pwnagotchi/ssh-keys
chmod 700 /opt/pwnagotchi/ssh-keys
```

### Integration with Fail2Ban
```bash
# Install fail2ban
sudo apt install fail2ban

# Configure SSH protection
sudo nano /etc/fail2ban/jail.local

# Add SSH jail configuration
[sshd]
enabled = true
port = 22
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 3600
```

### Monitoring Integration
The plugin can be extended to integrate with monitoring systems:
- Prometheus metrics export
- SNMP monitoring
- Syslog integration
- Email alerts

## Updates and Maintenance

### Plugin Updates
```bash
# Backup current plugin
sudo cp /usr/local/lib/python3.*/dist-packages/pwnagotchi/plugins/default/ssh_plugin.py /opt/backup/

# Update plugin
sudo cp new_ssh_plugin.py /usr/local/lib/python3.*/dist-packages/pwnagotchi/plugins/default/ssh_plugin.py

# Restart Pwnagotchi
sudo systemctl restart pwnagotchi
```

### Log Rotation
```bash
# Configure log rotation for SSH logs
sudo nano /etc/logrotate.d/ssh-plugin

# Add rotation configuration
/var/log/ssh-plugin.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    postrotate
        systemctl reload pwnagotchi
    endscript
}
```

## Support and Contributing

### Reporting Issues
- Check existing issues in the repository
- Provide detailed error logs
- Include configuration details
- Describe steps to reproduce

### Contributing
- Follow Pwnagotchi plugin development guidelines
- Test changes thoroughly
- Document new features
- Submit pull requests with clear descriptions

For additional help and community support, visit the Pwnagotchi community forums and GitHub repository.