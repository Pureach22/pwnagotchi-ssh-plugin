#!/bin/bash

# SSH Web Terminal Plugin - Easy Install
# One-command installation for Pwnagotchi Torch
# Usage: curl -sSL https://raw.githubusercontent.com/Pureach22/pwnagotchi-ssh-plugin/main/easy-install.sh | sudo bash

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🚀 SSH Web Terminal Plugin - Easy Install${NC}"
echo -e "${BLUE}==========================================${NC}"

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}❌ This script must be run as root (use sudo)${NC}"
   exit 1
fi

echo -e "${BLUE}📥 Downloading plugin...${NC}"

# Create temp directory
TMP_DIR=$(mktemp -d)
cd "$TMP_DIR"

# Download latest release
wget -q https://github.com/Pureach22/pwnagotchi-ssh-plugin/archive/main.zip
unzip -q main.zip
cd pwnagotchi-ssh-plugin-main

echo -e "${BLUE}🔧 Installing...${NC}"

# Run the installer
chmod +x install.sh
./install.sh

# Cleanup
cd /
rm -rf "$TMP_DIR"

echo -e "${GREEN}✅ Installation complete!${NC}"
echo -e "${YELLOW}🌐 Access your terminal at: http://$(hostname -I | awk '{print $1}'):8080/plugins/ssh/${NC}"