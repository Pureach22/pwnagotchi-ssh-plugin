#!/bin/bash
# Pwnagotchi SSH Plugin Installation Script
# Run with: sudo bash install.sh

set -e

echo "=== Pwnagotchi SSH Plugin Installer ==="
echo

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Error: This script must be run as root (use sudo)"
    exit 1
fi

# Define paths
PLUGIN_SOURCE="ssh_plugin.py"
PLUGIN_DIR="/usr/local/lib/python3.9/dist-packages/pwnagotchi/plugins/default"
BACKUP_DIR="/opt/pwnagotchi/backups"
CONFIG_FILE="/etc/pwnagotchi/config.toml"

echo "Step 1: Creating backup directory..."
mkdir -p "$BACKUP_DIR"

echo "Step 2: Checking for existing SSH plugin..."
if [ -f "$PLUGIN_DIR/ssh_plugin.py" ]; then
    echo "  - Backing up existing SSH plugin..."
    cp "$PLUGIN_DIR/ssh_plugin.py" "$BACKUP_DIR/ssh_plugin_backup_$(date +%Y%m%d_%H%M%S).py"
fi

echo "Step 3: Installing SSH plugin..."
if [ ! -f "$PLUGIN_SOURCE" ]; then
    echo "Error: ssh_plugin.py not found in current directory"
    exit 1
fi

# Find the correct Python plugin directory
PYTHON_DIRS=$(find /usr/local/lib -name "pwnagotchi" -type d 2>/dev/null | head -1)
if [ -z "$PYTHON_DIRS" ]; then
    echo "Error: Could not find Pwnagotchi installation directory"
    exit 1
fi

PLUGIN_DIR="$PYTHON_DIRS/plugins/default"
mkdir -p "$PLUGIN_DIR"

cp "$PLUGIN_SOURCE" "$PLUGIN_DIR/"
chmod 644 "$PLUGIN_DIR/ssh_plugin.py"
echo "  - Plugin installed to: $PLUGIN_DIR/ssh_plugin.py"

echo "Step 4: Installing Python dependencies..."
pip3 install paramiko psutil cryptography || {
    echo "Warning: Some dependencies may have failed to install"
    echo "Please install manually: pip3 install paramiko psutil cryptography"
}

echo "Step 5: Setting up SSH server..."
# Install openssh-server if not present
if ! command -v sshd &> /dev/null; then
    echo "  - Installing OpenSSH server..."
    apt update
    apt install -y openssh-server
fi

# Enable SSH service
systemctl enable ssh
echo "  - SSH service enabled"

echo "Step 6: Configuring SSH security..."
# Backup original SSH config
if [ ! -f "/etc/ssh/sshd_config.backup" ]; then
    cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup
    echo "  - SSH config backed up to /etc/ssh/sshd_config.backup"
fi

# Create secure SSH configuration
cat >> /etc/ssh/sshd_config << 'EOF'

# Pwnagotchi SSH Plugin Security Settings
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
MaxAuthTries 3
ClientAliveInterval 300
ClientAliveCountMax 2
EOF

echo "  - Applied security settings to SSH config"

echo "Step 7: Setting up SSH directory for default user..."
# Setup SSH directory for pi user
if id "pi" &>/dev/null; then
    sudo -u pi mkdir -p /home/pi/.ssh
    sudo -u pi chmod 700 /home/pi/.ssh
    sudo -u pi touch /home/pi/.ssh/authorized_keys
    sudo -u pi chmod 600 /home/pi/.ssh/authorized_keys
    echo "  - SSH directory configured for user 'pi'"
fi

echo "Step 8: Adding plugin configuration..."
if [ -f "$CONFIG_FILE" ]; then
    # Check if SSH plugin config already exists
    if ! grep -q "main.plugins.ssh.enabled" "$CONFIG_FILE"; then
        echo "" >> "$CONFIG_FILE"
        echo "# SSH Plugin Configuration" >> "$CONFIG_FILE"
        echo "main.plugins.ssh.enabled = true" >> "$CONFIG_FILE"
        echo "main.plugins.ssh.port = 22" >> "$CONFIG_FILE"
        echo "main.plugins.ssh.max_connections = 5" >> "$CONFIG_FILE"
        echo "main.plugins.ssh.auto_start = true" >> "$CONFIG_FILE"
        echo "main.plugins.ssh.key_auth_only = true" >> "$CONFIG_FILE"
        echo "main.plugins.ssh.display_on_screen = true" >> "$CONFIG_FILE"
        echo "main.plugins.ssh.ssh_x_coord = 160" >> "$CONFIG_FILE"
        echo "main.plugins.ssh.ssh_y_coord = 80" >> "$CONFIG_FILE"
        echo "  - Added SSH plugin configuration to config.toml"
    else
        echo "  - SSH plugin configuration already exists in config.toml"
    fi
else
    echo "  - Warning: Pwnagotchi config file not found at $CONFIG_FILE"
    echo "  - Please add configuration manually using config_example.toml"
fi

echo "Step 9: Installing fail2ban (optional security)..."
if ! command -v fail2ban-server &> /dev/null; then
    apt install -y fail2ban
    
    # Configure fail2ban for SSH
    cat > /etc/fail2ban/jail.local << 'EOF'
[sshd]
enabled = true
port = 22
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 3600
findtime = 600
EOF
    
    systemctl enable fail2ban
    systemctl start fail2ban
    echo "  - Fail2ban installed and configured"
else
    echo "  - Fail2ban already installed"
fi

echo "Step 10: Restarting services..."
systemctl restart ssh
echo "  - SSH service restarted"

if systemctl is-active --quiet pwnagotchi; then
    echo "  - Restarting Pwnagotchi service..."
    systemctl restart pwnagotchi
    echo "  - Pwnagotchi service restarted"
else
    echo "  - Pwnagotchi service not running, will start with plugin on next boot"
fi

echo
echo "=== Installation Complete! ==="
echo
echo "SSH Plugin has been successfully installed. Here's what you can do next:"
echo
echo "1. Access the SSH management interface at:"
echo "   http://your-pwnagotchi-ip:8080/plugins/ssh/"
echo
echo "2. Add your SSH public key through the web interface or manually:"
echo "   echo 'your-ssh-public-key' >> ~/.ssh/authorized_keys"
echo
echo "3. Connect via SSH:"
echo "   ssh pi@your-pwnagotchi-ip"
echo
echo "4. Monitor the installation:"
echo "   sudo journalctl -u pwnagotchi -f"
echo
echo "5. View SSH logs:"
echo "   sudo tail -f /var/log/auth.log"
echo
echo "Important Security Notes:"
echo "- Password authentication has been disabled for security"
echo "- Only SSH key authentication is allowed"
echo "- Add your SSH public key before the next reboot"
echo "- The plugin will show SSH status on the Pwnagotchi display"
echo
echo "Configuration file: $CONFIG_FILE"
echo "Plugin location: $PLUGIN_DIR/ssh_plugin.py"
echo "Backup location: $BACKUP_DIR/"
echo
echo "For troubleshooting, see README.md"