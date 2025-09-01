# Changelog

All notable changes to the SSH Web Terminal Plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-09-01

### 🎉 Major Rewrite - Complete Redesign

This is a complete rewrite of the SSH Web Terminal plugin with modern architecture, beautiful UI, and enhanced functionality.

### ✨ Added

#### 🎨 Modern Web Interface
- **Beautiful Dashboard**: Modern gradient-based design with responsive layout
- **Enhanced Terminal UI**: GitHub-inspired dark theme with smooth animations
- **Mobile Support**: Fully responsive design that works on all devices
- **Fullscreen Mode**: Immersive terminal experience with F11 toggle
- **Status Indicators**: Real-time visual feedback for all operations

#### 💻 Advanced Terminal Features
- **Multi-Session Support**: Handle multiple concurrent terminal sessions
- **Command History**: Navigate through previous commands with arrow keys
- **Auto-Reconnect**: Automatic connection handling with error recovery
- **Session Management**: Intelligent cleanup of dead/inactive sessions
- **Cross-Platform**: Linux (pty) and Windows (PowerShell) support

#### 🔧 Enhanced API
- **RESTful Design**: Clean, well-structured API endpoints
- **Terminal Management**: Complete CRUD operations for terminal sessions
- **SSH Service Control**: Start/stop SSH daemon via API
- **Connection Monitoring**: Real-time SSH connection tracking
- **Error Handling**: Robust error responses with detailed messages

#### 🛡️ Security & Reliability
- **Session Isolation**: Each terminal session is securely isolated
- **Input Validation**: Secure processing of all user inputs
- **Timeout Handling**: Automatic session cleanup after inactivity
- **Resource Management**: Efficient memory and process handling
- **Error Recovery**: Graceful handling of connection failures

#### 📊 System Integration
- **Pwnagotchi Display**: Enhanced status display on device screen
- **Service Monitoring**: Real-time SSH service status tracking
- **Connection Analytics**: Detailed connection information and statistics
- **Resource Tracking**: Monitor active sessions and system resources

### 🔄 Changed

#### 🏗️ Architecture Improvements
- **Plugin Structure**: Modular design with separate classes for different concerns
- **Code Organization**: Clean separation of terminal, session, and plugin logic
- **Performance**: Optimized polling and resource usage
- **Maintainability**: Well-documented code with type hints and docstrings

#### 🎯 User Experience
- **Navigation**: Intuitive navigation between dashboard and terminal
- **Responsiveness**: Improved performance and faster response times
- **Accessibility**: Better keyboard navigation and screen reader support
- **Feedback**: Clear status messages and error reporting

### 🛠️ Technical Details

#### Dependencies
- **Flask**: Updated to 2.2.0+ for latest security features
- **Jinja2**: Updated to 3.1.0+ for improved templating
- **PSUtil**: Enhanced system monitoring capabilities
- **Paramiko**: Latest SSH library for better compatibility
- **Cryptography**: Updated security libraries

#### Browser Support
- **Modern Browsers**: Chrome 80+, Firefox 75+, Safari 13+, Edge 80+
- **Mobile Browsers**: iOS Safari 13+, Chrome Mobile 80+
- **Features**: ES6+, CSS Grid, Flexbox, WebSocket support

#### Performance Optimizations
- **Polling**: Reduced polling frequency for better performance
- **Memory**: Efficient session management with automatic cleanup
- **Network**: Optimized API calls and response sizes
- **Rendering**: Smooth animations and responsive UI updates

### 🐛 Fixed

#### Terminal Issues
- **Connection Stability**: Improved connection handling and recovery
- **Output Buffering**: Fixed issues with large output streams
- **Input Processing**: Better handling of special characters and commands
- **Session Cleanup**: Proper cleanup of terminated sessions

#### UI/UX Issues
- **Mobile Layout**: Fixed responsive design issues on small screens
- **Keyboard Shortcuts**: Improved keyboard navigation and shortcuts
- **Status Updates**: Real-time status updates without page refresh
- **Error Messages**: Clear, actionable error messages

#### Security Issues
- **Input Sanitization**: Enhanced input validation and sanitization
- **Session Security**: Improved session isolation and security
- **Error Disclosure**: Reduced information disclosure in error messages
- **CSRF Protection**: Enhanced cross-site request forgery protection

### 🗑️ Removed

#### Deprecated Features
- **Legacy UI**: Removed old table-based layout
- **Outdated Dependencies**: Removed support for older library versions
- **Deprecated APIs**: Cleaned up unused API endpoints
- **Legacy Code**: Removed compatibility code for very old Pwnagotchi versions

### 📋 Migration Guide

#### From v1.x to v2.0

1. **Backup Configuration**:
   ```bash
   sudo cp /etc/pwnagotchi/config.toml /etc/pwnagotchi/config.toml.backup
   ```

2. **Update Plugin**:
   ```bash
   sudo cp ssh.py /usr/local/share/pwnagotchi/custom-plugins/
   ```

3. **Install New Dependencies**:
   ```bash
   sudo pip3 install -r requirements.txt
   ```

4. **Update Configuration**:
   ```toml
   # New configuration options
   [main.plugins.ssh]
   enabled = true
   terminal_theme = "dark"
   max_sessions = 5
   ```

5. **Restart Pwnagotchi**:
   ```bash
   sudo systemctl restart pwnagotchi
   ```

#### Configuration Changes

| Old Option | New Option | Notes |
|------------|------------|-------|
| `ssh_enabled` | `enabled` | Renamed for consistency |
| `web_ui_enabled` | `enable_web_terminal` | More specific naming |
| - | `terminal_theme` | New: Theme customization |
| - | `max_sessions` | New: Session limit |

### 🔮 Upcoming Features (v2.1.0)

- **File Manager**: Web-based file browser and editor
- **Log Viewer**: Real-time log viewing and filtering
- **Theme Customization**: Multiple terminal themes
- **Plugin Extensions**: API for extending functionality
- **Backup/Restore**: Configuration backup and restore

---

## [1.0.0] - 2024-12-15

### 🎉 Initial Release

#### ✨ Added
- **Basic Web Terminal**: Simple web-based terminal interface
- **SSH Service Control**: Start/stop SSH daemon from web interface
- **Connection Monitoring**: View active SSH connections
- **Pwnagotchi Integration**: Status display on device screen
- **REST API**: Basic API endpoints for service control

#### 🔧 Features
- **Terminal Emulation**: Basic command execution with output display
- **Session Management**: Single terminal session support
- **Web Interface**: Simple HTML interface for terminal access
- **SSH Management**: Control SSH service from web interface

#### 🛡️ Security
- **Basic Authentication**: Simple session-based authentication
- **Input Validation**: Basic input sanitization
- **Service Control**: Secure SSH service management

---

## Development Notes

### Version Numbering

We use [Semantic Versioning](https://semver.org/):
- **MAJOR** version for incompatible API changes
- **MINOR** version for backwards-compatible functionality additions
- **PATCH** version for backwards-compatible bug fixes

### Release Process

1. Update version in `ssh.py`
2. Update CHANGELOG.md
3. Create release branch
4. Test thoroughly
5. Create GitHub release
6. Update documentation

### Support

- **v2.x**: Current stable version with active support
- **v1.x**: Legacy version with security updates only

---

**📞 Support**: [GitHub Issues](https://github.com/Pureach22/pwnagotchi-ssh-plugin/issues)
**💬 Discussions**: [GitHub Discussions](https://github.com/Pureach22/pwnagotchi-ssh-plugin/discussions)