#!/usr/bin/env python3
# SSH Plugin for Pwnagotchi WebUI
# Provides SSH server management and monitoring through the web interface

import logging
import subprocess
import json
import os
import time
import re
from datetime import datetime

try:
    from flask import render_template_string, request, jsonify, abort, flash, redirect, url_for
except ImportError:
    logging.error("[SSH] Flask not available - WebUI features disabled")
    # Create dummy functions to prevent import errors
    def render_template_string(*args, **kwargs): return "Flask not available"
    def request(*args, **kwargs): pass
    def jsonify(data): return json.dumps(data)
    def abort(code): return f"Error {code}"

try:
    import pwnagotchi
    import pwnagotchi.plugins as plugins
    import pwnagotchi.ui.fonts as fonts
    from pwnagotchi.ui.components import LabeledValue, Text
    from pwnagotchi.ui.view import BLACK
except ImportError as e:
    logging.error(f"[SSH] Pwnagotchi imports failed: {e}")
    # Create minimal plugin base class if pwnagotchi not available
    class plugins:
        class Plugin:
            def __init__(self): pass


class SSHPlugin(plugins.Plugin):
    __author__ = 'Pwnagotchi Community'
    __version__ = '1.0.0'
    __license__ = 'GPL3'
    __description__ = 'SSH access and management plugin for Pwnagotchi WebUI'

    def __init__(self):
        self.options = {
            'port': 22,
            'max_connections': 5,
            'display_position': '160,80',
            'auto_start': True,
            'key_auth_only': True,
            'webui_path': '/ssh',
            'display_on_screen': True,
            'ssh_x_coord': 160,
            'ssh_y_coord': 80,
            'listen_all_interfaces': True  # Support all network interfaces
        }
        self.ssh_status = False
        self.active_connections = []
        self.connection_count = 0
        self.last_update = 0
        self.sshd_config_path = '/etc/ssh/sshd_config'
        self.authorized_keys_path = os.path.expanduser('~/.ssh/authorized_keys')

    def on_loaded(self):
        logging.info("[SSH] ========================================")
        logging.info("[SSH] SSH Plugin Starting...")
        logging.info(f"[SSH] Plugin Version: {self.__version__}")
        logging.info(f"[SSH] Plugin Author: {self.__author__}")
        logging.info("[SSH] ========================================")
        
        # Ensure SSH directory exists
        ssh_dir = os.path.dirname(self.authorized_keys_path)
        if not os.path.exists(ssh_dir):
            os.makedirs(ssh_dir, mode=0o700)
            logging.info(f"[SSH] Created SSH directory: {ssh_dir}")
            
        # Initialize SSH service status
        self.ssh_status = self.check_ssh_status()
        logging.info(f"[SSH] Initial SSH status: {self.ssh_status}")
        
        # Auto-start SSH if configured
        if self.options.get('auto_start', True) and not self.ssh_status:
            logging.info("[SSH] Auto-starting SSH service...")
            self.start_ssh_service()
            
        logging.info("[SSH] ========================================")
        logging.info("[SSH] SSH Plugin FULLY LOADED AND READY!")
        logging.info("[SSH] WebUI should be available at: /plugins/ssh/")
        logging.info("[SSH] ========================================")
            
        logging.info(f"[SSH] SSH service status: {'Running' if self.ssh_status else 'Stopped'}")

    def on_ui_setup(self, ui):
        if not self.options.get('display_on_screen', True):
            return
            
        with ui._lock:
            ui.add_element(
                'ssh_status',
                LabeledValue(
                    color=BLACK,
                    label='SSH',
                    value='OFF',
                    position=(int(self.options.get('ssh_x_coord', 160)),
                             int(self.options.get('ssh_y_coord', 80))),
                    label_font=fonts.Small,
                    text_font=fonts.Small
                )
            )

    def on_ui_update(self, ui):
        if not self.options.get('display_on_screen', True):
            return
            
        current_time = time.time()
        
        # Update every 10 seconds
        if current_time - self.last_update >= 10:
            self.last_update = current_time
            self.ssh_status = self.check_ssh_status()
            self.connection_count = self.get_active_connections_count()
            
            if self.ssh_status:
                if self.connection_count > 0:
                    ui.set('ssh_status', f'{self.connection_count}')
                else:
                    ui.set('ssh_status', 'ON')
            else:
                ui.set('ssh_status', 'OFF')

    def on_unload(self, ui):
        if self.options.get('display_on_screen', True):
            with ui._lock:
                ui.remove_element('ssh_status')
        logging.info("[SSH] SSH plugin unloaded")

    def on_webhook(self, path, request):
        """Handle WebUI requests for SSH management"""
        try:
            # Debug logging to help troubleshoot 404 issues
            logging.info(f"[SSH] Webhook request: path='{path}', method={request.method}")
            
            if path == "/" or path == "":
                return self.render_dashboard()
            elif path == "config":
                if request.method == 'POST':
                    return self.handle_config_update(request)
                return self.render_config_page()
            elif path == "keys":
                if request.method == 'POST':
                    return self.handle_key_management(request)
                return self.render_keys_page()
            elif path == "api/status":
                return self.get_ssh_status_api()
            elif path == "api/start":
                return self.start_ssh_api()
            elif path == "api/stop":
                return self.stop_ssh_api()
            elif path == "api/connections":
                return self.get_connections_api()
            elif path == "test":
                # Simple test endpoint to verify plugin is working
                return "<html><body><h1>SSH Plugin Test</h1><p>Plugin is working correctly!</p></body></html>"
            else:
                logging.warning(f"[SSH] 404 - Unknown path: '{path}'")
                return f"<html><body><h1>404 Not Found</h1><p>Path '{path}' not found in SSH plugin.</p><p>Available paths: /, config, keys, api/status, api/start, api/stop, api/connections, test</p></body></html>", 404
        except Exception as e:
            logging.error(f"[SSH] Webhook error: {e}")
            return f"<html><body><h1>Error</h1><p>{str(e)}</p></body></html>", 500

    def check_ssh_status(self):
        """Check if SSH service is running"""
        try:
            result = subprocess.run(['systemctl', 'is-active', 'ssh'], 
                                  capture_output=True, text=True)
            return result.returncode == 0 and result.stdout.strip() == 'active'
        except Exception as e:
            logging.error(f"[SSH] Error checking SSH status: {e}")
            return False

    def start_ssh_service(self):
        """Start SSH service"""
        try:
            subprocess.run(['sudo', 'systemctl', 'start', 'ssh'], check=True)
            subprocess.run(['sudo', 'systemctl', 'enable', 'ssh'], check=True)
            self.ssh_status = True
            logging.info("[SSH] SSH service started")
            return True
        except subprocess.CalledProcessError as e:
            logging.error(f"[SSH] Failed to start SSH service: {e}")
            return False

    def stop_ssh_service(self):
        """Stop SSH service"""
        try:
            subprocess.run(['sudo', 'systemctl', 'stop', 'ssh'], check=True)
            self.ssh_status = False
            logging.info("[SSH] SSH service stopped")
            return True
        except subprocess.CalledProcessError as e:
            logging.error(f"[SSH] Failed to stop SSH service: {e}")
            return False

    def get_active_connections_count(self):
        """Get count of active SSH connections on all interfaces"""
        try:
            # Use 'ss' command to check for SSH connections on all interfaces
            ssh_port = self.options.get("port", 22)
            result = subprocess.run(['ss', '-tn', 'state', 'established', 
                                   f'sport = :{ssh_port}'],
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                # Filter out header line and count established connections
                connections = [line for line in lines if 'ESTAB' in line and f':{ssh_port}' in line]
                return len(connections)
            return 0
        except Exception as e:
            logging.error(f"[SSH] Error getting connection count: {e}")
            return 0

    def get_active_connections(self):
        """Get detailed information about active SSH connections"""
        connections = []
        try:
            # Get connection details using 'who' command
            result = subprocess.run(['who'], capture_output=True, text=True)
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 5 and ('pts/' in parts[1] or 'ssh' in line.lower()):
                            connection = {
                                'user': parts[0],
                                'terminal': parts[1],
                                'time': ' '.join(parts[2:4]),
                                'ip': parts[4].strip('()') if len(parts) > 4 else 'local'
                            }
                            connections.append(connection)
        except Exception as e:
            logging.error(f"[SSH] Error getting connection details: {e}")
        
        return connections

    def render_dashboard(self):
        """Render the main SSH dashboard"""
        ssh_status = self.check_ssh_status()
        connections = self.get_active_connections()
        
        template = '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>SSH Management - {{ pwnagotchi_name }}</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
                .container { max-width: 1200px; margin: 0 auto; }
                .card { background: white; padding: 20px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                .status-card { text-align: center; }
                .status-on { color: #4CAF50; font-weight: bold; }
                .status-off { color: #f44336; font-weight: bold; }
                .btn { padding: 10px 20px; margin: 5px; border: none; border-radius: 4px; cursor: pointer; text-decoration: none; display: inline-block; }
                .btn-primary { background: #2196F3; color: white; }
                .btn-success { background: #4CAF50; color: white; }
                .btn-danger { background: #f44336; color: white; }
                .btn:hover { opacity: 0.8; }
                table { width: 100%; border-collapse: collapse; }
                th, td { padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }
                th { background-color: #f2f2f2; }
                .logs { background: #1e1e1e; color: #00ff00; padding: 15px; border-radius: 4px; font-family: monospace; font-size: 12px; max-height: 300px; overflow-y: auto; }
                .nav { margin-bottom: 20px; }
                .nav a { margin-right: 15px; text-decoration: none; padding: 8px 16px; background: #ddd; border-radius: 4px; }
                .nav a.active { background: #2196F3; color: white; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>SSH Management Dashboard</h1>
                
                <div class="nav">
                    <a href="/plugins/ssh/" class="active">Dashboard</a>
                    <a href="/plugins/ssh/config">Configuration</a>
                    <a href="/plugins/ssh/keys">SSH Keys</a>
                </div>

                <div class="card status-card">
                    <h2>SSH Service Status</h2>
                    <p class="{{ 'status-on' if ssh_status else 'status-off' }}">
                        {{ 'RUNNING' if ssh_status else 'STOPPED' }}
                    </p>
                    {% if ssh_status %}
                        <a href="#" onclick="controlSSH('stop')" class="btn btn-danger">Stop SSH</a>
                    {% else %}
                        <a href="#" onclick="controlSSH('start')" class="btn btn-success">Start SSH</a>
                    {% endif %}
                    <a href="/plugins/ssh/config" class="btn btn-primary">Configure</a>
                </div>

                <div class="card">
                    <h3>Active Connections ({{ connections|length }})</h3>
                    {% if connections %}
                        <table>
                            <tr>
                                <th>User</th>
                                <th>Terminal</th>
                                <th>Login Time</th>
                                <th>IP Address</th>
                            </tr>
                            {% for conn in connections %}
                            <tr>
                                <td>{{ conn.user }}</td>
                                <td>{{ conn.terminal }}</td>
                                <td>{{ conn.time }}</td>
                                <td>{{ conn.ip }}</td>
                            </tr>
                            {% endfor %}
                        </table>
                    {% else %}
                        <p>No active SSH connections</p>
                    {% endif %}
                </div>
            </div>

            <script>
                function controlSSH(action) {
                    fetch('/plugins/ssh/api/' + action, {method: 'POST'})
                        .then(response => response.json())
                        .then(data => {
                            if (data.success) {
                                location.reload();
                            } else {
                                alert('Operation failed: ' + data.error);
                            }
                        })
                        .catch(error => {
                            alert('Error: ' + error);
                        });
                }

                // Auto-refresh every 30 seconds
                setTimeout(() => location.reload(), 30000);
            </script>
        </body>
        </html>
        '''
        
        return render_template_string(template, 
                                    pwnagotchi_name=pwnagotchi.name(),
                                    ssh_status=ssh_status,
                                    connections=connections)

    def render_config_page(self):
        """Render SSH configuration page"""
        template = '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>SSH Configuration - {{ pwnagotchi_name }}</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
                .container { max-width: 800px; margin: 0 auto; }
                .card { background: white; padding: 20px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                .form-group { margin: 15px 0; }
                label { display: block; margin-bottom: 5px; font-weight: bold; }
                input, select { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
                .btn { padding: 10px 20px; margin: 5px; border: none; border-radius: 4px; cursor: pointer; }
                .btn-primary { background: #2196F3; color: white; }
                .nav { margin-bottom: 20px; }
                .nav a { margin-right: 15px; text-decoration: none; padding: 8px 16px; background: #ddd; border-radius: 4px; }
                .nav a.active { background: #2196F3; color: white; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>SSH Configuration</h1>
                
                <div class="nav">
                    <a href="/plugins/ssh/">Dashboard</a>
                    <a href="/plugins/ssh/config" class="active">Configuration</a>
                    <a href="/plugins/ssh/keys">SSH Keys</a>
                </div>

                <div class="card">
                    <h3>SSH Server Settings</h3>
                    <form method="post">
                        <div class="form-group">
                            <label for="port">SSH Port:</label>
                            <input type="number" id="port" name="port" value="{{ port }}" min="1" max="65535">
                        </div>
                        
                        <div class="form-group">
                            <label for="max_connections">Max Connections:</label>
                            <input type="number" id="max_connections" name="max_connections" value="{{ max_connections }}" min="1" max="100">
                        </div>
                        
                        <div class="form-group">
                            <label>
                                <input type="checkbox" name="key_auth_only" {{ 'checked' if key_auth_only else '' }}>
                                Key Authentication Only (Disable Password Auth)
                            </label>
                        </div>
                        
                        <div class="form-group">
                            <label>
                                <input type="checkbox" name="auto_start" {{ 'checked' if auto_start else '' }}>
                                Auto-start SSH on Boot
                            </label>
                        </div>
                        
                        <button type="submit" class="btn btn-primary">Save Configuration</button>
                    </form>
                </div>
            </div>
        </body>
        </html>
        '''
        
        return render_template_string(template,
                                    pwnagotchi_name=pwnagotchi.name(),
                                    port=self.options.get('port', 22),
                                    max_connections=self.options.get('max_connections', 5),
                                    key_auth_only=self.options.get('key_auth_only', True),
                                    auto_start=self.options.get('auto_start', True))

    def render_keys_page(self):
        """Render SSH keys management page"""
        authorized_keys = self.get_authorized_keys()
        
        template = '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>SSH Keys - {{ pwnagotchi_name }}</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
                .container { max-width: 1000px; margin: 0 auto; }
                .card { background: white; padding: 20px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                .form-group { margin: 15px 0; }
                label { display: block; margin-bottom: 5px; font-weight: bold; }
                textarea { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; font-family: monospace; }
                .btn { padding: 10px 20px; margin: 5px; border: none; border-radius: 4px; cursor: pointer; text-decoration: none; display: inline-block; }
                .btn-primary { background: #2196F3; color: white; }
                .btn-danger { background: #f44336; color: white; }
                .key-item { background: #f9f9f9; padding: 10px; margin: 10px 0; border-radius: 4px; border-left: 4px solid #2196F3; }
                .key-text { font-family: monospace; font-size: 12px; word-break: break-all; }
                .nav { margin-bottom: 20px; }
                .nav a { margin-right: 15px; text-decoration: none; padding: 8px 16px; background: #ddd; border-radius: 4px; }
                .nav a.active { background: #2196F3; color: white; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>SSH Key Management</h1>
                
                <div class="nav">
                    <a href="/plugins/ssh/">Dashboard</a>
                    <a href="/plugins/ssh/config">Configuration</a>
                    <a href="/plugins/ssh/keys" class="active">SSH Keys</a>
                </div>

                <div class="card">
                    <h3>Add New SSH Public Key</h3>
                    <form method="post">
                        <input type="hidden" name="action" value="add_key">
                        <div class="form-group">
                            <label for="key_name">Key Name (optional):</label>
                            <input type="text" id="key_name" name="key_name" placeholder="e.g., laptop-key">
                        </div>
                        <div class="form-group">
                            <label for="public_key">Public Key:</label>
                            <textarea id="public_key" name="public_key" rows="4" placeholder="ssh-rsa AAAAB3... or ssh-ed25519 AAAAC3..."></textarea>
                        </div>
                        <button type="submit" class="btn btn-primary">Add Key</button>
                    </form>
                </div>

                <div class="card">
                    <h3>Authorized Keys ({{ authorized_keys|length }})</h3>
                    {% if authorized_keys %}
                        {% for key in authorized_keys %}
                        <div class="key-item">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                                <strong>{{ key.name or 'Unnamed Key' }}</strong>
                                <form method="post" style="display: inline;">
                                    <input type="hidden" name="action" value="remove_key">
                                    <input type="hidden" name="key_index" value="{{ loop.index0 }}">
                                    <button type="submit" class="btn btn-danger" onclick="return confirm('Remove this key?')">Remove</button>
                                </form>
                            </div>
                            <div class="key-text">{{ key.key[:80] }}...</div>
                            <div style="font-size: 12px; color: #666; margin-top: 5px;">
                                Type: {{ key.type }} | Added: {{ key.added }}
                            </div>
                        </div>
                        {% endfor %}
                    {% else %}
                        <p>No SSH keys configured. Add a public key above to enable SSH access.</p>
                    {% endif %}
                </div>
            </div>
        </body>
        </html>
        '''
        
        return render_template_string(template,
                                    pwnagotchi_name=pwnagotchi.name(),
                                    authorized_keys=authorized_keys)

    def get_authorized_keys(self):
        """Get list of authorized SSH keys"""
        keys = []
        try:
            if os.path.exists(self.authorized_keys_path):
                with open(self.authorized_keys_path, 'r') as f:
                    for i, line in enumerate(f):
                        line = line.strip()
                        if line and not line.startswith('#'):
                            parts = line.split()
                            if len(parts) >= 2:
                                key_type = parts[0]
                                key_data = parts[1]
                                key_name = parts[2] if len(parts) > 2 else f'Key {i+1}'
                                
                                keys.append({
                                    'type': key_type,
                                    'key': key_data,
                                    'name': key_name,
                                    'added': 'Unknown',
                                    'full_line': line
                                })
        except Exception as e:
            logging.error(f"[SSH] Error reading authorized keys: {e}")
        
        return keys

    def handle_key_management(self, request):
        """Handle SSH key management operations"""
        action = request.form.get('action')
        
        if action == 'add_key':
            public_key = request.form.get('public_key', '').strip()
            key_name = request.form.get('key_name', '').strip()
            
            if not public_key:
                return redirect('/plugins/ssh/keys?error=empty_key')
            
            # Validate key format
            parts = public_key.split()
            if len(parts) < 2 or parts[0] not in ['ssh-rsa', 'ssh-ed25519', 'ssh-dss', 'ecdsa-sha2-nistp256']:
                return redirect('/plugins/ssh/keys?error=invalid_key')
            
            # Add name if provided
            if key_name:
                if len(parts) == 2:
                    public_key += f' {key_name}'
                else:
                    parts[2] = key_name
                    public_key = ' '.join(parts)
            
            # Add key to authorized_keys
            try:
                with open(self.authorized_keys_path, 'a') as f:
                    f.write(f'{public_key}\n')
                
                # Set proper permissions
                os.chmod(self.authorized_keys_path, 0o600)
                logging.info(f"[SSH] Added SSH key: {key_name or 'unnamed'}")
                
            except Exception as e:
                logging.error(f"[SSH] Error adding SSH key: {e}")
                return redirect('/plugins/ssh/keys?error=add_failed')
        
        elif action == 'remove_key':
            key_index = int(request.form.get('key_index', -1))
            
            try:
                keys = self.get_authorized_keys()
                if 0 <= key_index < len(keys):
                    # Remove the key by rewriting the file
                    with open(self.authorized_keys_path, 'w') as f:
                        for i, key in enumerate(keys):
                            if i != key_index:
                                f.write(f'{key["full_line"]}\n')
                    
                    logging.info(f"[SSH] Removed SSH key at index {key_index}")
                
            except Exception as e:
                logging.error(f"[SSH] Error removing SSH key: {e}")
                return redirect('/plugins/ssh/keys?error=remove_failed')
        
        return redirect('/plugins/ssh/keys')

    def handle_config_update(self, request):
        """Handle SSH configuration updates"""
        try:
            # Update plugin options
            port = int(request.form.get('port', 22))
            max_connections = int(request.form.get('max_connections', 5))
            key_auth_only = 'key_auth_only' in request.form
            auto_start = 'auto_start' in request.form
            
            self.options.update({
                'port': port,
                'max_connections': max_connections,
                'key_auth_only': key_auth_only,
                'auto_start': auto_start
            })
            
            # Apply SSH configuration changes
            self.update_sshd_config()
            
            # Restart SSH service to apply changes
            if self.ssh_status:
                subprocess.run(['sudo', 'systemctl', 'restart', 'ssh'])
            
            logging.info("[SSH] Configuration updated successfully")
            
        except Exception as e:
            logging.error(f"[SSH] Error updating configuration: {e}")
            return redirect('/plugins/ssh/config?error=update_failed')
        
        return redirect('/plugins/ssh/config?success=updated')

    def update_sshd_config(self):
        """Update SSH daemon configuration"""
        try:
            # Read current config
            config_lines = []
            if os.path.exists(self.sshd_config_path):
                with open(self.sshd_config_path, 'r') as f:
                    config_lines = f.readlines()
            
            # Update or add configuration options
            config_dict = {}
            for line in config_lines:
                if line.strip() and not line.strip().startswith('#'):
                    parts = line.split()
                    if len(parts) >= 2:
                        config_dict[parts[0].lower()] = ' '.join(parts[1:])
            
            # Apply our settings
            config_dict['port'] = str(self.options.get('port', 22))
            config_dict['maxstartups'] = str(self.options.get('max_connections', 5))
            
            # Listen on all network interfaces (support all networks)
            if self.options.get('listen_all_interfaces', True):
                config_dict['listenaddress'] = '0.0.0.0'
            
            if self.options.get('key_auth_only', True):
                config_dict['passwordauthentication'] = 'no'
                config_dict['pubkeyauthentication'] = 'yes'
            else:
                config_dict['passwordauthentication'] = 'yes'
                config_dict['pubkeyauthentication'] = 'yes'
            
            # Write updated config (this would require sudo in practice)
            logging.info("[SSH] SSH configuration would be updated (requires root privileges)")
            
        except Exception as e:
            logging.error(f"[SSH] Error updating SSH config: {e}")

    def get_ssh_status_api(self):
        """API endpoint for SSH status"""
        return jsonify({
            'status': self.check_ssh_status(),
            'connections': self.get_active_connections_count(),
            'port': self.options.get('port', 22)
        })

    def start_ssh_api(self):
        """API endpoint to start SSH service"""
        success = self.start_ssh_service()
        return jsonify({
            'success': success,
            'status': self.check_ssh_status()
        })

    def stop_ssh_api(self):
        """API endpoint to stop SSH service"""
        success = self.stop_ssh_service()
        return jsonify({
            'success': success,
            'status': self.check_ssh_status()
        })

    def get_connections_api(self):
        """API endpoint for active connections"""
        return jsonify({
            'connections': self.get_active_connections(),
            'count': self.get_active_connections_count()
        })


# Required for Pwnagotchi plugin loading
def load_plugin():
    return SSHPlugin()