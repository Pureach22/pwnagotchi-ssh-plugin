#!/bin/bash

# SSH Web Terminal Plugin Installer for Pwnagotchi Torch
# Version 2.0.0
# https://github.com/Pureach22/pwnagotchi-ssh-plugin

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Plugin information
PLUGIN_NAME="SSH Web Terminal"
PLUGIN_VERSION="2.0.0"
PLUGIN_FILE="ssh.py"
PLUGIN_DIR="/usr/local/share/pwnagotchi/custom-plugins"
CONFIG_FILE="/etc/pwnagotchi/config.toml"
BACKUP_DIR="/tmp/pwnagotchi-ssh-backup-$(date +%Y%m%d-%H%M%S)"

# Helper functions
print_header() {
    echo -e "${PURPLE}================================${NC}"
    echo -e "${PURPLE}  $1${NC}"
    echo -e "${PURPLE}================================${NC}"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_info() {
    echo -e "${CYAN}[INFO]${NC} $1"
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        print_warning "Running as root. This is OK for installation."
    else
        print_error "This script needs to be run with sudo privileges."
        print_info "Please run: sudo $0"
        exit 1
    fi
}

# Check if we're on a Pwnagotchi system
check_pwnagotchi() {
    print_step "Checking Pwnagotchi environment..."
    
    if [ ! -f "/etc/pwnagotchi/config.toml" ]; then
        print_warning "Pwnagotchi config file not found. This might not be a Pwnagotchi system."
        echo -n "Continue anyway? (y/N): "
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            print_info "Installation cancelled."
            exit 0
        fi
    else
        print_success "Pwnagotchi environment detected."
    fi
}

# Create backup
create_backup() {
    print_step "Creating backup..."
    
    mkdir -p "$BACKUP_DIR"
    
    # Backup existing plugin if it exists
    if [ -f "$PLUGIN_DIR/$PLUGIN_FILE" ]; then
        cp "$PLUGIN_DIR/$PLUGIN_FILE" "$BACKUP_DIR/"
        print_success "Existing plugin backed up to $BACKUP_DIR/"
    fi
    
    # Backup config file
    if [ -f "$CONFIG_FILE" ]; then
        cp "$CONFIG_FILE" "$BACKUP_DIR/"
        print_success "Config file backed up to $BACKUP_DIR/"
    fi
}

# Install system dependencies
install_dependencies() {
    print_step "Installing system dependencies..."
    
    # Update package list
    apt update -q
    
    # Install required packages
    apt install -y python3-dev python3-pip openssh-server
    
    # Enable SSH service
    systemctl enable ssh
    
    print_success "System dependencies installed."
}

# Install Python dependencies
install_python_deps() {
    print_step "Installing Python dependencies..."
    
    # Check if requirements.txt exists
    if [ -f "requirements.txt" ]; then
        pip3 install -r requirements.txt
        print_success "Python dependencies installed from requirements.txt"
    else
        # Install dependencies manually
        pip3 install flask jinja2 psutil paramiko cryptography ptyprocess pexpect
        print_success "Python dependencies installed manually"
    fi
}

# Install plugin
install_plugin() {
    print_step "Installing SSH Web Terminal plugin..."
    
    # Create plugin directory if it doesn't exist
    mkdir -p "$PLUGIN_DIR"
    
    # Copy plugin file
    if [ -f "$PLUGIN_FILE" ]; then
        cp "$PLUGIN_FILE" "$PLUGIN_DIR/"
        chmod 644 "$PLUGIN_DIR/$PLUGIN_FILE"
        print_success "Plugin installed to $PLUGIN_DIR/$PLUGIN_FILE"
    else
        print_error "Plugin file $PLUGIN_FILE not found in current directory."
        print_info "Please run this script from the plugin directory."
        exit 1
    fi
}

# Configure plugin
configure_plugin() {
    print_step "Configuring plugin..."
    
    # Create config file if it doesn't exist
    if [ ! -f "$CONFIG_FILE" ]; then
        mkdir -p "$(dirname "$CONFIG_FILE")"
        touch "$CONFIG_FILE"
        print_info "Created new config file: $CONFIG_FILE"
    fi
    
    # Check if plugin is already configured
    if grep -q "main.plugins.ssh.enabled" "$CONFIG_FILE"; then
        print_warning "SSH plugin configuration already exists in config file."
        echo -n "Update configuration? (y/N): "
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            print_info "Skipping configuration update."
            return
        fi
        
        # Remove existing configuration
        sed -i '/\[main\.plugins\.ssh\]/,/^$/d' "$CONFIG_FILE"
        sed -i '/main\.plugins\.ssh\./d' "$CONFIG_FILE"
    fi
    
    # Add plugin configuration
    cat >> "$CONFIG_FILE" << EOF

# SSH Web Terminal Plugin Configuration
[main.plugins.ssh]
enabled = true
display_on_screen = true
auto_start_ssh = true
enable_web_terminal = true
ssh_x_coord = 160
ssh_y_coord = 66
terminal_theme = "dark"
max_sessions = 5
EOF
    
    print_success "Plugin configuration added to $CONFIG_FILE"
}

# Start services
start_services() {
    print_step "Starting services..."
    
    # Start SSH service
    systemctl start ssh
    print_success "SSH service started"
    
    # Restart Pwnagotchi
    echo -n "Restart Pwnagotchi service now? (Y/n): "
    read -r response
    if [[ "$response" =~ ^[Nn]$ ]]; then
        print_warning "Pwnagotchi service not restarted."
        print_info "Please restart manually: sudo systemctl restart pwnagotchi"
    else
        systemctl restart pwnagotchi
        print_success "Pwnagotchi service restarted"
    fi
}

# Test installation
test_installation() {
    print_step "Testing installation..."
    
    sleep 5  # Wait for services to start
    
    # Check if SSH is running
    if systemctl is-active --quiet ssh; then
        print_success "SSH service is running"
    else
        print_warning "SSH service is not running"
    fi
    
    # Check if Pwnagotchi is running
    if systemctl is-active --quiet pwnagotchi; then
        print_success "Pwnagotchi service is running"
    else
        print_warning "Pwnagotchi service is not running"
    fi
    
    # Check if plugin file exists and is readable
    if [ -r "$PLUGIN_DIR/$PLUGIN_FILE" ]; then
        print_success "Plugin file is installed and readable"
    else
        print_error "Plugin file is not accessible"
    fi
}

# Show final information
show_final_info() {
    print_header "Installation Complete!"
    
    echo -e "${GREEN}🎉 SSH Web Terminal Plugin v$PLUGIN_VERSION installed successfully!${NC}"
    echo ""
    echo -e "${CYAN}📍 Access URLs:${NC}"
    echo "   Dashboard: http://$(hostname -I | awk '{print $1}'):8080/plugins/ssh/"
    echo "   Terminal:  http://$(hostname -I | awk '{print $1}'):8080/plugins/ssh/terminal"
    echo ""
    echo -e "${CYAN}🔧 Configuration:${NC}"
    echo "   Config file: $CONFIG_FILE"
    echo "   Plugin file: $PLUGIN_DIR/$PLUGIN_FILE"
    echo "   Backup: $BACKUP_DIR"
    echo ""
    echo -e "${CYAN}📊 Service Status:${NC}"
    echo "   SSH: $(systemctl is-active ssh)"
    echo "   Pwnagotchi: $(systemctl is-active pwnagotchi)"
    echo ""
    echo -e "${CYAN}🛠️ Troubleshooting:${NC}"
    echo "   Check logs: sudo journalctl -u pwnagotchi -f | grep ssh"
    echo "   Restart service: sudo systemctl restart pwnagotchi"
    echo "   Test API: curl http://localhost:8080/plugins/ssh/api/ssh/status"
    echo ""
    echo -e "${YELLOW}⚠️  Important Notes:${NC}"
    echo "   • Make sure your firewall allows port 8080"
    echo "   • SSH service is now enabled and running"
    echo "   • Web terminal provides direct shell access"
    echo "   • Default SSH credentials may apply"
    echo ""
    echo -e "${GREEN}📖 Documentation:${NC}"
    echo "   README: https://github.com/Pureach22/pwnagotchi-ssh-plugin"
    echo "   Issues: https://github.com/Pureach22/pwnagotchi-ssh-plugin/issues"
    echo ""
}

# Uninstall function
uninstall() {
    print_header "Uninstalling SSH Web Terminal Plugin"
    
    print_step "Removing plugin file..."
    rm -f "$PLUGIN_DIR/$PLUGIN_FILE"
    print_success "Plugin file removed"
    
    print_step "Removing configuration..."
    if [ -f "$CONFIG_FILE" ]; then
        sed -i '/\[main\.plugins\.ssh\]/,/^$/d' "$CONFIG_FILE"
        sed -i '/main\.plugins\.ssh\./d' "$CONFIG_FILE"
        print_success "Configuration removed"
    fi
    
    echo -n "Stop SSH service? (y/N): "
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        systemctl stop ssh
        systemctl disable ssh
        print_success "SSH service stopped and disabled"
    fi
    
    echo -n "Restart Pwnagotchi? (Y/n): "
    read -r response
    if [[ ! "$response" =~ ^[Nn]$ ]]; then
        systemctl restart pwnagotchi
        print_success "Pwnagotchi restarted"
    fi
    
    print_success "SSH Web Terminal plugin uninstalled"
}

# Main installation function
main() {
    print_header "$PLUGIN_NAME v$PLUGIN_VERSION Installer"
    
    # Parse command line arguments
    case "${1:-}" in
        "uninstall"|"remove")
            check_root
            uninstall
            exit 0
            ;;
        "help"|"-h"|"--help")
            echo "Usage: $0 [command]"
            echo ""
            echo "Commands:"
            echo "  install     Install the plugin (default)"
            echo "  uninstall   Remove the plugin"
            echo "  help        Show this help"
            echo ""
            exit 0
            ;;
    esac
    
    # Run installation steps
    check_root
    check_pwnagotchi
    create_backup
    install_dependencies
    install_python_deps
    install_plugin
    configure_plugin
    start_services
    test_installation
    show_final_info
}

# Run main function
main "$@"