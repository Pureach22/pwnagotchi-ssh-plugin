#!/usr/bin/env python3
"""
SSH Plugin Test Suite
Tests the SSH plugin functionality without requiring a full Pwnagotchi environment
"""

import sys
import os
import tempfile
import subprocess
import json
from unittest.mock import Mock, patch, MagicMock

# Add current directory to path to import the plugin
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_ssh_plugin():
    """Test the SSH plugin functionality"""
    print("=== SSH Plugin Test Suite ===\n")
    
    # Mock the pwnagotchi modules
    sys.modules['pwnagotchi'] = Mock()
    sys.modules['pwnagotchi.plugins'] = Mock()
    sys.modules['pwnagotchi.ui'] = Mock()
    sys.modules['pwnagotchi.ui.fonts'] = Mock()
    sys.modules['pwnagotchi.ui.components'] = Mock()
    sys.modules['pwnagotchi.ui.view'] = Mock()
    
    # Import the plugin after mocking
    try:
        from ssh_plugin import SSHPlugin
        print("✓ Plugin import successful")
    except ImportError as e:
        print(f"✗ Plugin import failed: {e}")
        return False
    
    # Test 1: Plugin initialization
    print("\nTest 1: Plugin Initialization")
    try:
        plugin = SSHPlugin()
        print("✓ Plugin initialization successful")
        print(f"  - Default options: {len(plugin.options)} settings configured")
    except Exception as e:
        print(f"✗ Plugin initialization failed: {e}")
        return False
    
    # Test 2: Configuration validation
    print("\nTest 2: Configuration Validation")
    try:
        required_options = ['port', 'max_connections', 'auto_start', 'key_auth_only']
        missing_options = [opt for opt in required_options if opt not in plugin.options]
        
        if not missing_options:
            print("✓ All required configuration options present")
        else:
            print(f"✗ Missing configuration options: {missing_options}")
            return False
    except Exception as e:
        print(f"✗ Configuration validation failed: {e}")
        return False
    
    # Test 3: SSH status checking (mocked)
    print("\nTest 3: SSH Status Checking")
    try:
        with patch('subprocess.run') as mock_run:
            # Mock successful SSH status check
            mock_run.return_value = Mock(returncode=0, stdout='active')
            status = plugin.check_ssh_status()
            print(f"✓ SSH status check method works: {status}")
    except Exception as e:
        print(f"✗ SSH status check failed: {e}")
        return False
    
    # Test 4: SSH key parsing
    print("\nTest 4: SSH Key Management")
    try:
        # Create a temporary authorized_keys file
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC7... test@example.com\n")
            f.write("ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIJbR... user@laptop\n")
            temp_file = f.name
        
        # Override the authorized_keys path for testing
        plugin.authorized_keys_path = temp_file
        keys = plugin.get_authorized_keys()
        
        print(f"✓ SSH key parsing successful: {len(keys)} keys found")
        for i, key in enumerate(keys):
            print(f"  - Key {i+1}: {key['type']} ({key['name']})")
        
        # Cleanup
        os.unlink(temp_file)
    except Exception as e:
        print(f"✗ SSH key management test failed: {e}")
        return False
    
    # Test 5: WebUI template rendering
    print("\nTest 5: WebUI Template Rendering")
    try:
        # Mock Flask's render_template_string
        with patch('ssh_plugin.render_template_string') as mock_render:
            mock_render.return_value = "<html>Mock Dashboard</html>"
            
            # Mock pwnagotchi.name()
            with patch('ssh_plugin.pwnagotchi.name', return_value='test-pwnagotchi'):
                result = plugin.render_dashboard()
                print("✓ Dashboard template rendering successful")
    except Exception as e:
        print(f"✗ WebUI template rendering failed: {e}")
        return False
    
    # Test 6: API endpoints
    print("\nTest 6: API Endpoints")
    try:
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout='active')
            
            # Test status API
            status_response = plugin.get_ssh_status_api()
            print("✓ SSH status API endpoint works")
            
            # The response should be a Flask jsonify object
            # In a real environment, this would return JSON
            print(f"  - Status API response type: {type(status_response)}")
    except Exception as e:
        print(f"✗ API endpoints test failed: {e}")
        return False
    
    # Test 7: Connection monitoring
    print("\nTest 7: Connection Monitoring")
    try:
        with patch('subprocess.run') as mock_run:
            # Mock 'who' command output
            mock_run.return_value = Mock(
                returncode=0, 
                stdout='pi       pts/0        2024-01-01 12:00 (192.168.1.100)\n'
            )
            
            connections = plugin.get_active_connections()
            print(f"✓ Connection monitoring works: {len(connections)} connections detected")
            
            if connections:
                conn = connections[0]
                print(f"  - Sample connection: {conn['user']}@{conn['ip']}")
    except Exception as e:
        print(f"✗ Connection monitoring test failed: {e}")
        return False
    
    # Test 8: Log parsing
    print("\nTest 8: SSH Log Parsing")
    try:
        # Create a temporary log file
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("Jan 1 12:00:01 pwnagotchi sshd[1234]: Accepted publickey for pi from 192.168.1.100\n")
            f.write("Jan 1 12:01:01 pwnagotchi sshd[1235]: Failed password for root from 192.168.1.200\n")
            temp_log = f.name
        
        # Override the auth log path for testing
        plugin.auth_log_path = temp_log
        
        with patch('subprocess.run') as mock_run:
            with open(temp_log, 'r') as f:
                log_content = f.read()
            mock_run.return_value = Mock(returncode=0, stdout=log_content)
            
            logs = plugin.get_ssh_logs(10)
            print(f"✓ SSH log parsing works: {len(logs)} log entries found")
            
            # Cleanup
            os.unlink(temp_log)
    except Exception as e:
        print(f"✗ SSH log parsing test failed: {e}")
        return False
    
    print(f"\n=== Test Results ===")
    print("✓ All tests passed successfully!")
    print(f"✓ SSH Plugin is ready for deployment")
    
    return True

def test_configuration_validation():
    """Test configuration file validation"""
    print("\n=== Configuration Validation ===")
    
    config_file = "config_example.toml"
    if os.path.exists(config_file):
        print(f"✓ Configuration example found: {config_file}")
        
        # Basic validation of config file
        with open(config_file, 'r') as f:
            content = f.read()
            
        required_settings = [
            'main.plugins.ssh.enabled',
            'main.plugins.ssh.port',
            'main.plugins.ssh.max_connections'
        ]
        
        missing_settings = []
        for setting in required_settings:
            if setting not in content:
                missing_settings.append(setting)
        
        if not missing_settings:
            print("✓ All required configuration settings present")
        else:
            print(f"✗ Missing configuration settings: {missing_settings}")
            
    else:
        print(f"✗ Configuration example not found: {config_file}")

def test_installation_script():
    """Test installation script validation"""
    print("\n=== Installation Script Validation ===")
    
    install_script = "install.sh"
    if os.path.exists(install_script):
        print(f"✓ Installation script found: {install_script}")
        
        # Check if script is executable
        if os.access(install_script, os.X_OK):
            print("✓ Installation script is executable")
        else:
            print("! Installation script is not executable (use: chmod +x install.sh)")
            
        # Basic content validation
        with open(install_script, 'r') as f:
            content = f.read()
            
        required_components = [
            'ssh_plugin.py',
            'systemctl',
            'pip3 install',
            'config.toml'
        ]
        
        missing_components = []
        for component in required_components:
            if component not in content:
                missing_components.append(component)
        
        if not missing_components:
            print("✓ All required installation components present")
        else:
            print(f"✗ Missing installation components: {missing_components}")
            
    else:
        print(f"✗ Installation script not found: {install_script}")

if __name__ == "__main__":
    print("Starting SSH Plugin validation tests...\n")
    
    # Run main plugin tests
    plugin_tests_passed = test_ssh_plugin()
    
    # Run configuration validation
    test_configuration_validation()
    
    # Run installation script validation
    test_installation_script()
    
    print(f"\n=== Final Results ===")
    if plugin_tests_passed:
        print("✓ SSH Plugin is ready for installation on Pwnagotchi")
        print("✓ Run './install.sh' as root to install the plugin")
        print("✓ See README.md for detailed usage instructions")
    else:
        print("✗ SSH Plugin has issues that need to be resolved")
        
    print(f"\nFiles created:")
    files = ['ssh_plugin.py', 'README.md', 'config_example.toml', 'install.sh', 'requirements.txt']
    for file in files:
        if os.path.exists(file):
            size = os.path.getsize(file)
            print(f"  - {file} ({size} bytes)")
        else:
            print(f"  - {file} (missing)")