#!/bin/bash

# SSH Web Terminal Plugin Installer for Pwnagotchi Torch
# One-command installation script inspired by pwnagotchi-torch-plugins
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
PLUGIN_URL="https://raw.githubusercontent.com/Pureach22/pwnagotchi-ssh-plugin/main/ssh.py"
PLUGIN_DIR="/usr/local/share/pwnagotchi/custom-plugins"
CONFIG_FILE="/etc/pwnagotchi/config.toml"
TEMP_DIR="/tmp/pwnagotchi-ssh-install"

# Helper functions
print_banner() {
    echo -e "${PURPLE}"
    echo "╔═══════════════════════════════════════════╗"
    echo "║        SSH Web Terminal Installer        ║"
    echo "║     For Pwnagotchi Torch - v${PLUGIN_VERSION}        ║"
    echo "╚═══════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_info() {
    echo -e "${CYAN}[i]${NC} $1"
}

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "This script needs to be run with sudo privileges."
        print_info "Please run: curl -sSL https://raw.githubusercontent.com/Pureach22/pwnagotchi-ssh-plugin/main/install.sh | sudo bash"
        exit 1
    fi
}

# Detect system and check compatibility
check_system() {
    print_step "Checking system compatibility..."
    
    # Check if this looks like a Pwnagotchi system
    if [ -f "/etc/pwnagotchi/config.toml" ] || [ -d "/usr/local/share/pwnagotchi" ]; then
        print_success "Pwnagotchi system detected"
    else
        print_warning "This doesn't appear to be a Pwnagotchi system"
        echo -n "Continue installation anyway? (y/N): "
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            print_info "Installation cancelled"
            exit 0
        fi
    fi
    
    # Check Python version
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
        print_success "Python ${PYTHON_VERSION} found"
    else
        print_error "Python 3 not found"
        exit 1
    fi
}

# Install system dependencies
install_system_deps() {
    print_step "Installing system dependencies..."
    
    # Update package list quietly
    apt update -qq
    
    # Install required packages
    apt install -y curl wget python3-pip python3-dev openssh-server > /dev/null 2>&1
    
    # Enable SSH service
    systemctl enable ssh > /dev/null 2>&1
    
    print_success "System dependencies installed"
}

# Install Python dependencies
install_python_deps() {
    print_step "Installing Python dependencies..."
    
    # Install Python packages
    pip3 install flask jinja2 psutil paramiko cryptography ptyprocess pexpect > /dev/null 2>&1
    
    print_success "Python dependencies installed"
}

# Download and install plugin
install_plugin() {
    print_step "Downloading and installing plugin..."
    
    # Create directories
    mkdir -p "$PLUGIN_DIR"
    mkdir -p "$TEMP_DIR"
    
    # Download plugin file
    if curl -sSL "$PLUGIN_URL" -o "$TEMP_DIR/ssh.py"; then
        print_success "Plugin downloaded"
    else
        print_error "Failed to download plugin"
        exit 1
    fi
    
    # Install plugin
    cp "$TEMP_DIR/ssh.py" "$PLUGIN_DIR/"
    chmod 644 "$PLUGIN_DIR/ssh.py"
    
    # Cleanup
    rm -rf "$TEMP_DIR"
    
    print_success "Plugin installed to $PLUGIN_DIR/ssh.py"
}

# Configure plugin
configure_plugin() {
    print_step "Configuring plugin..."
    
    # Create config file if it doesn't exist
    if [ ! -f "$CONFIG_FILE" ]; then
        mkdir -p "$(dirname "$CONFIG_FILE")"
        touch "$CONFIG_FILE"
    fi
    
    # Check if already configured
    if grep -q "main.plugins.ssh.enabled" "$CONFIG_FILE"; then
        print_warning "SSH plugin already configured"
    else
        # Add configuration
        cat >> "$CONFIG_FILE" << 'EOF'

# SSH Web Terminal Plugin
[main.plugins.ssh]
enabled = true
display_on_screen = true
auto_start_ssh = true
enable_web_terminal = true
EOF
        print_success "Plugin configuration added"
    fi
}

# Start services
start_services() {
    print_step "Starting services..."
    
    # Start SSH service
    systemctl start ssh > /dev/null 2>&1
    print_success "SSH service started"
    
    # Restart Pwnagotchi
    print_info "Restarting Pwnagotchi service..."
    systemctl restart pwnagotchi > /dev/null 2>&1
    print_success "Pwnagotchi restarted"
}

# Show final results
show_results() {
    echo ""
    echo -e "${GREEN}╔═══════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║            INSTALLATION COMPLETE!        ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${CYAN}🌐 Access URLs:${NC}"
    echo "   Dashboard: http://$(hostname -I | awk '{print $1}'):8080/plugins/ssh/"
    echo "   Terminal:  http://$(hostname -I | awk '{print $1}'):8080/plugins/ssh/terminal"
    echo ""
    echo -e "${CYAN}� Mobile Access:${NC}"
    echo "   Works perfectly on phones and tablets!"
    echo ""
    echo -e "${CYAN}� Features Available:${NC}"
    echo "   ✓ Web-based terminal with command history"
    echo "   ✓ Multi-session support"
    echo "   ✓ Real-time command execution"
    echo "   ✓ Mobile-responsive interface"
    echo "   ✓ SSH service management"
    echo ""
    echo -e "${YELLOW}⚠️  Security Note:${NC}"
    echo "   SSH service is now running. Make sure you have"
    echo "   secure passwords and/or SSH keys configured."
    echo ""
    echo -e "${CYAN}📖 Need Help?${NC}"
    echo "   Documentation: https://github.com/Pureach22/pwnagotchi-ssh-plugin"
    echo "   Issues: https://github.com/Pureach22/pwnagotchi-ssh-plugin/issues"
    echo ""
    echo -e "${GREEN}Happy hacking! 🚀${NC}"
}

# Main installation function
main() {
    print_banner
    
    # Parse command line arguments for uninstall
    case "${1:-}" in
        "uninstall"|"remove"|"--uninstall")
            echo -e "${RED}Uninstall functionality not implemented in one-liner version${NC}"
            echo -e "${CYAN}To uninstall manually:${NC}"
            echo "  sudo rm -f /usr/local/share/pwnagotchi/custom-plugins/ssh.py"
            echo "  sudo sed -i '/main.plugins.ssh/d' /etc/pwnagotchi/config.toml"
            echo "  sudo systemctl restart pwnagotchi"
            exit 0
            ;;
        "help"|"-h"|"--help")
            echo "SSH Web Terminal Plugin Installer"
            echo "Usage: curl -sSL https://raw.githubusercontent.com/Pureach22/pwnagotchi-ssh-plugin/main/install.sh | sudo bash"
            exit 0
            ;;
    esac
    
    # Run installation steps
    check_root
    check_system
    install_system_deps
    install_python_deps
    install_plugin
    configure_plugin
    start_services
    show_results
}

# Trap errors and show helpful message
trap 'echo -e "\n${RED}[✗] Installation failed!${NC}"; echo "Please check the output above and try again."; echo "For help, visit: https://github.com/Pureach22/pwnagotchi-ssh-plugin/issues"' ERR

# Run main function with all arguments
main "$@"