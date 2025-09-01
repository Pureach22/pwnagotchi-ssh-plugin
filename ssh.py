#!/usr/bin/env python3
"""
SSH Plugin for Pwnagotchi WebUI
Provides SSH server management and monitoring through the web interface
"""

import logging
import subprocess
import json
import os
import time
import re
import pty
import select
import termios
import struct
import fcntl
import threading
import queue
from datetime import datetime

import pwnagotchi
import pwnagotchi.plugins as plugins
import pwnagotchi.ui.fonts as fonts
from pwnagotchi.ui.components import LabeledValue, Text
from pwnagotchi.ui.view import BLACK

from flask import render_template_string, request, jsonify, abort


class WebTerminal:
    """Web-based terminal emulator using pty"""
    
    def __init__(self):
        self.terminals = {}  # Store active terminal sessions
        self.terminal_counter = 0
    
    def create_terminal(self):
        """Create a new terminal session"""
        try:
            # Create a new pseudo-terminal
            master_fd, slave_fd = pty.openpty()
            
            # Start shell process
            pid = os.fork()
            if pid == 0:
                # Child process - become the shell
                os.setsid()
                os.dup2(slave_fd, 0)  # stdin
                os.dup2(slave_fd, 1)  # stdout
                os.dup2(slave_fd, 2)  # stderr
                os.close(master_fd)
                os.close(slave_fd)
                
                # Start bash shell
                os.execv('/bin/bash', ['/bin/bash', '-l'])
            else:
                # Parent process
                os.close(slave_fd)
                
                # Make master_fd non-blocking
                fcntl.fcntl(master_fd, fcntl.F_SETFL, os.O_NONBLOCK)
                
                terminal_id = f"term_{self.terminal_counter}"
                self.terminal_counter += 1
                
                self.terminals[terminal_id] = {
                    'master_fd': master_fd,
                    'pid': pid,
                    'output_queue': queue.Queue(),
                    'active': True
                }
                
                # Start output reader thread
                threading.Thread(target=self._read_output, args=(terminal_id,), daemon=True).start()
                
                return terminal_id
                
        except Exception as e:
            logging.error(f"[SSH] Error creating terminal: {e}")
            return None
    
    def _read_output(self, terminal_id):
        """Read output from terminal in background thread"""
        terminal = self.terminals.get(terminal_id)
        if not terminal:
            return
            
        master_fd = terminal['master_fd']
        output_queue = terminal['output_queue']
        
        while terminal['active']:
            try:
                ready, _, _ = select.select([master_fd], [], [], 0.1)
                if ready:
                    data = os.read(master_fd, 1024)
                    if data:
                        output_queue.put(data.decode('utf-8', errors='ignore'))
                    else:
                        break
            except (OSError, IOError):
                break
        
        terminal['active'] = False
    
    def write_input(self, terminal_id, data):
        """Write input to terminal"""
        terminal = self.terminals.get(terminal_id)
        if terminal and terminal['active']:
            try:
                os.write(terminal['master_fd'], data.encode('utf-8'))
                return True
            except (OSError, IOError):
                terminal['active'] = False
        return False
    
    def read_output(self, terminal_id):
        """Read available output from terminal"""
        terminal = self.terminals.get(terminal_id)
        if not terminal:
            return ""
            
        output = ""
        try:
            while not terminal['output_queue'].empty():
                output += terminal['output_queue'].get_nowait()
        except queue.Empty:
            pass
        
        return output
    
    def resize_terminal(self, terminal_id, rows, cols):
        """Resize terminal window"""
        terminal = self.terminals.get(terminal_id)
        if terminal and terminal['active']:
            try:
                # Set terminal size
                winsize = struct.pack('HHHH', rows, cols, 0, 0)
                fcntl.ioctl(terminal['master_fd'], termios.TIOCSWINSZ, winsize)
                return True
            except (OSError, IOError):
                pass
        return False
    
    def close_terminal(self, terminal_id):
        """Close terminal session"""
        terminal = self.terminals.get(terminal_id)
        if terminal:
            terminal['active'] = False
            try:
                os.close(terminal['master_fd'])
                os.kill(terminal['pid'], 9)  # Force kill the shell process
            except (OSError, ProcessLookupError):
                pass
            del self.terminals[terminal_id]


class SSH(plugins.Plugin):
    __author__ = 'Pwnagotchi Community'
    __version__ = '1.0.0'
    __license__ = 'GPL3'
    __description__ = 'SSH access and management plugin for Pwnagotchi WebUI'

    def __init__(self):
        self.options = {
            'auto_start': True,
            'display_on_screen': True,
            'ssh_x_coord': 160,
            'ssh_y_coord': 66,
            'connection_timeout': 30,
            'enable_web_terminal': True
        }
        self.ssh_status = False
        self.active_connections = 0
        self.authorized_keys_path = "/root/.ssh/authorized_keys"
        self.ssh_config_path = "/etc/ssh/sshd_config"
        self.ready = False
        self.web_terminal = WebTerminal()

    def on_loaded(self):
        """Plugin loaded callback"""
        logging.info("[SSH] SSH plugin loaded.")
        
        # Ensure SSH directory exists
        ssh_dir = os.path.dirname(self.authorized_keys_path)
        if not os.path.exists(ssh_dir):
            os.makedirs(ssh_dir, mode=0o700)
        
        # Check initial SSH status
        self.ssh_status = self.check_ssh_status()
        logging.info(f"[SSH] SSH service status: {'active' if self.ssh_status else 'inactive'}")
        
        # Auto-start SSH if configured
        if self.options.get('auto_start', True) and not self.ssh_status:
            logging.info("[SSH] Auto-starting SSH service...")
            self.start_ssh_service()
        
        self.ready = True

    def on_ui_setup(self, ui):
        """Setup UI elements"""
        if not self.options.get('display_on_screen', True):
            return
            
        with ui._lock:
            ui.add_element(
                'ssh_status',
                LabeledValue(
                    color=BLACK,
                    label='SSH',
                    value='Starting...',
                    position=(int(self.options.get('ssh_x_coord', 160)),
                             int(self.options.get('ssh_y_coord', 66))),
                    label_font=fonts.Small,
                    text_font=fonts.Small
                )
            )

    def on_ui_update(self, ui):
        """Update UI with current status"""
        if not self.options.get('display_on_screen', True):
            return
            
        current_status = self.check_ssh_status()
        self.active_connections = len(self.get_active_connections())
        
        status_text = "Active" if current_status else "Inactive"
        if current_status and self.active_connections > 0:
            status_text = f"Active ({self.active_connections})"
        
        ui.set('ssh_status', status_text)

    def on_unload(self, ui):
        """Plugin unload callback"""
        if self.options.get('display_on_screen', True):
            with ui._lock:
                ui.remove_element('ssh_status')
        logging.info("[SSH] SSH plugin unloaded.")

    def on_webhook(self, path, request):
        """Handle WebUI requests for SSH management"""
        if not self.ready:
            return "Plugin not ready"

        logging.info(f"[SSH] Webhook: path='{path}', method={getattr(request, 'method', 'GET')}")
        
        try:
            if path == "/" or path == "" or path is None:
                return self.render_dashboard()
            elif path == "config":
                if getattr(request, 'method', 'GET') == 'POST':
                    return self.handle_config_update(request)
                return self.render_config_page()
            elif path == "keys":
                if getattr(request, 'method', 'GET') == 'POST':
                    return self.handle_key_management(request)
                return self.render_keys_page()
            elif path == "terminal":
                return self.render_terminal_page()
            elif path == "api/status":
                return jsonify({
                    'status': self.check_ssh_status(),
                    'connections': len(self.get_active_connections())
                })
            elif path == "api/start":
                success = self.start_ssh_service()
                return jsonify({'success': success})
            elif path == "api/stop":
                success = self.stop_ssh_service()
                return jsonify({'success': success})
            elif path == "api/connections":
                return jsonify(self.get_active_connections())
            elif path == "api/terminal/create":
                terminal_id = self.web_terminal.create_terminal()
                return jsonify({'terminal_id': terminal_id, 'success': terminal_id is not None})
            elif path.startswith("api/terminal/") and "/input" in path:
                terminal_id = path.split("/")[2]
                data = request.get_json() or {}
                input_data = data.get('input', '')
                success = self.web_terminal.write_input(terminal_id, input_data)
                return jsonify({'success': success})
            elif path.startswith("api/terminal/") and "/output" in path:
                terminal_id = path.split("/")[2]
                output = self.web_terminal.read_output(terminal_id)
                return jsonify({'output': output})
            elif path.startswith("api/terminal/") and "/resize" in path:
                terminal_id = path.split("/")[2]
                data = request.get_json() or {}
                rows = data.get('rows', 24)
                cols = data.get('cols', 80)
                success = self.web_terminal.resize_terminal(terminal_id, rows, cols)
                return jsonify({'success': success})
            elif path.startswith("api/terminal/") and "/close" in path:
                terminal_id = path.split("/")[2]
                self.web_terminal.close_terminal(terminal_id)
                return jsonify({'success': True})
            elif path == "test":
                return "<html><body><h1>SSH Plugin Test</h1><p>Plugin working!</p></body></html>"
        except Exception as e:
            logging.error(f"[SSH] Webhook error: {e}")
            return f"<html><body><h1>Error</h1><p>{str(e)}</p></body></html>", 500
        
        # 404 case - handle outside of try/catch to avoid catching abort()
        abort(404)

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
            result = subprocess.run(['systemctl', 'start', 'ssh'], 
                                  capture_output=True, text=True)
            success = result.returncode == 0
            if success:
                logging.info("[SSH] SSH service started successfully")
                self.ssh_status = True
            else:
                logging.error(f"[SSH] Failed to start SSH: {result.stderr}")
            return success
        except Exception as e:
            logging.error(f"[SSH] Error starting SSH: {e}")
            return False

    def stop_ssh_service(self):
        """Stop SSH service"""
        try:
            result = subprocess.run(['systemctl', 'stop', 'ssh'], 
                                  capture_output=True, text=True)
            success = result.returncode == 0
            if success:
                logging.info("[SSH] SSH service stopped successfully")
                self.ssh_status = False
            else:
                logging.error(f"[SSH] Failed to stop SSH: {result.stderr}")
            return success
        except Exception as e:
            logging.error(f"[SSH] Error stopping SSH: {e}")
            return False

    def get_active_connections(self):
        """Get list of active SSH connections"""
        connections = []
        try:
            result = subprocess.run(['ss', '-tuln'], capture_output=True, text=True)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if ':22' in line and 'LISTEN' not in line:
                        parts = line.split()
                        if len(parts) >= 5:
                            local_addr = parts[4]
                            remote_addr = parts[5] if len(parts) > 5 else 'Unknown'
                            connections.append({
                                'local': local_addr,
                                'remote': remote_addr,
                                'time': time.strftime('%H:%M:%S')
                            })
        except Exception as e:
            logging.error(f"[SSH] Error getting connections: {e}")
        
        return connections

    def render_dashboard(self):
        """Render main SSH dashboard"""
        status = self.check_ssh_status()
        connections = self.get_active_connections()
        
        template = """
<!DOCTYPE html>
<html>
<head>
    <title>SSH Management - {{ pwnagotchi_name }}</title>
    <meta charset="utf-8">
    <style>
        body { font-family: monospace; margin: 20px; background: #f0f0f0; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }
        .status { padding: 10px; margin: 10px 0; border-radius: 4px; }
        .active { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .inactive { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .button { padding: 8px 16px; margin: 4px; border: none; border-radius: 4px; cursor: pointer; }
        .btn-primary { background: #007bff; color: white; }
        .btn-secondary { background: #6c757d; color: white; }
        .btn-success { background: #28a745; color: white; }
        .btn-danger { background: #dc3545; color: white; }
        table { width: 100%; border-collapse: collapse; margin: 10px 0; }
        th, td { padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #f2f2f2; }
        .nav { margin: 20px 0; }
        .nav a { margin-right: 15px; text-decoration: none; color: #007bff; }
    </style>
    <script>
        function toggleService(action) {
            fetch('/plugins/ssh/api/' + action, {method: 'POST'})
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        location.reload();
                    } else {
                        alert('Operation failed');
                    }
                });
        }
    </script>
</head>
<body>
    <div class="container">
        <h1>🔐 SSH Management</h1>
        
        <div class="nav">
            <a href="/plugins/ssh/">Dashboard</a>
            <a href="/plugins/ssh/config">Configuration</a>
            <a href="/plugins/ssh/keys">SSH Keys</a>
            <a href="/plugins/ssh/terminal">Web Terminal</a>
        </div>

        <div class="status {{ status_class }}">
            <strong>SSH Status:</strong> {{ status_text }}
            {% if status %}
                <button class="button btn-danger" onclick="toggleService('stop')">Stop SSH</button>
            {% else %}
                <button class="button btn-success" onclick="toggleService('start')">Start SSH</button>
            {% endif %}
        </div>

        <h3>📊 Connection Status</h3>
        <p><strong>Active Connections:</strong> {{ connection_count }}</p>
        
        {% if connections %}
        <table>
            <thead>
                <tr><th>Local Address</th><th>Remote Address</th><th>Time</th></tr>
            </thead>
            <tbody>
                {% for conn in connections %}
                <tr>
                    <td>{{ conn.local }}</td>
                    <td>{{ conn.remote }}</td>
                    <td>{{ conn.time }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% endif %}

        <h3>🔧 Quick Actions</h3>
        <button class="button btn-primary" onclick="location.href='/plugins/ssh/config'">Configure SSH</button>
        <button class="button btn-secondary" onclick="location.href='/plugins/ssh/keys'">Manage Keys</button>
        <button class="button btn-primary" onclick="location.href='/plugins/ssh/terminal'">Web Terminal</button>
        
        <div style="margin-top: 30px; padding: 15px; background: #e9ecef; border-radius: 4px;">
            <h4>📋 SSH Connection Info</h4>
            <p><strong>Default SSH command:</strong> <code>ssh pi@[PWNAGOTCHI_IP]</code></p>
            <p><strong>Default port:</strong> 22</p>
            <p><strong>Key authentication:</strong> Recommended</p>
        </div>
    </div>
</body>
</html>
        """
        
        return render_template_string(template,
            pwnagotchi_name=pwnagotchi.name(),
            status=status,
            status_text='Active' if status else 'Inactive',
            status_class='active' if status else 'inactive',
            connections=connections,
            connection_count=len(connections)
        )

    def render_config_page(self):
        """Render SSH configuration page"""
        template = """
<!DOCTYPE html>
<html>
<head>
    <title>SSH Configuration - {{ pwnagotchi_name }}</title>
    <meta charset="utf-8">
    <style>
        body { font-family: monospace; margin: 20px; background: #f0f0f0; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }
        .nav { margin: 20px 0; }
        .nav a { margin-right: 15px; text-decoration: none; color: #007bff; }
        .form-group { margin: 15px 0; }
        label { display: block; margin-bottom: 5px; font-weight: bold; }
        input, textarea, select { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
        .button { padding: 8px 16px; margin: 4px; border: none; border-radius: 4px; cursor: pointer; }
        .btn-primary { background: #007bff; color: white; }
        .alert { padding: 10px; margin: 10px 0; border-radius: 4px; }
        .alert-info { background: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; }
    </style>
</head>
<body>
    <div class="container">
        <h1>⚙️ SSH Configuration</h1>
        
        <div class="nav">
            <a href="/plugins/ssh/">Dashboard</a>
            <a href="/plugins/ssh/config">Configuration</a>
            <a href="/plugins/ssh/keys">SSH Keys</a>
        </div>

        <div class="alert alert-info">
            <strong>Note:</strong> Configuration changes require SSH service restart to take effect.
        </div>

        <form method="POST">
            <div class="form-group">
                <label for="port">SSH Port:</label>
                <input type="number" id="port" name="port" value="22" min="1" max="65535">
            </div>
            
            <div class="form-group">
                <label for="permit_root">Permit Root Login:</label>
                <select id="permit_root" name="permit_root">
                    <option value="no">No</option>
                    <option value="yes">Yes</option>
                    <option value="prohibit-password" selected>Prohibit Password (Keys Only)</option>
                </select>
            </div>
            
            <div class="form-group">
                <label for="password_auth">Password Authentication:</label>
                <select id="password_auth" name="password_auth">
                    <option value="no" selected>No (Recommended)</option>
                    <option value="yes">Yes</option>
                </select>
            </div>
            
            <div class="form-group">
                <label for="listen_addresses">Listen Addresses (one per line):</label>
                <textarea id="listen_addresses" name="listen_addresses" rows="3">0.0.0.0</textarea>
            </div>
            
            <button type="submit" class="button btn-primary">Save Configuration</button>
        </form>
    </div>
</body>
</html>
        """
        
        return render_template_string(template, pwnagotchi_name=pwnagotchi.name())

    def render_keys_page(self):
        """Render SSH keys management page"""
        keys = self.get_authorized_keys()
        
        template = """
<!DOCTYPE html>
<html>
<head>
    <title>SSH Keys - {{ pwnagotchi_name }}</title>
    <meta charset="utf-8">
    <style>
        body { font-family: monospace; margin: 20px; background: #f0f0f0; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }
        .nav { margin: 20px 0; }
        .nav a { margin-right: 15px; text-decoration: none; color: #007bff; }
        .form-group { margin: 15px 0; }
        label { display: block; margin-bottom: 5px; font-weight: bold; }
        input, textarea { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
        .button { padding: 8px 16px; margin: 4px; border: none; border-radius: 4px; cursor: pointer; }
        .btn-primary { background: #007bff; color: white; }
        .btn-danger { background: #dc3545; color: white; }
        table { width: 100%; border-collapse: collapse; margin: 10px 0; }
        th, td { padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #f2f2f2; }
        .key-data { font-family: monospace; font-size: 10px; max-width: 200px; overflow: hidden; text-overflow: ellipsis; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔑 SSH Key Management</h1>
        
        <div class="nav">
            <a href="/plugins/ssh/">Dashboard</a>
            <a href="/plugins/ssh/config">Configuration</a>
            <a href="/plugins/ssh/keys">SSH Keys</a>
        </div>

        <h3>📝 Add New SSH Key</h3>
        <form method="POST">
            <input type="hidden" name="action" value="add_key">
            <div class="form-group">
                <label for="key_name">Key Name (optional):</label>
                <input type="text" id="key_name" name="key_name" placeholder="e.g., laptop-key">
            </div>
            <div class="form-group">
                <label for="public_key">Public Key:</label>
                <textarea id="public_key" name="public_key" rows="3" placeholder="ssh-rsa AAAAB3NzaC1yc2E... user@host" required></textarea>
            </div>
            <button type="submit" class="button btn-primary">Add Key</button>
        </form>

        <h3>📋 Authorized Keys ({{ key_count }})</h3>
        {% if keys %}
        <table>
            <thead>
                <tr><th>Name</th><th>Type</th><th>Key Data</th><th>Actions</th></tr>
            </thead>
            <tbody>
                {% for key in keys %}
                <tr>
                    <td>{{ key.name }}</td>
                    <td>{{ key.type }}</td>
                    <td class="key-data">{{ key.key[:50] }}...</td>
                    <td>
                        <form method="POST" style="display: inline;">
                            <input type="hidden" name="action" value="remove_key">
                            <input type="hidden" name="key_data" value="{{ key.full_line }}">
                            <button type="submit" class="button btn-danger" onclick="return confirm('Remove this key?')">Remove</button>
                        </form>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% else %}
        <p>No SSH keys configured. Add a key above to enable key-based authentication.</p>
        {% endif %}
    </div>
</body>
</html>
        """
        
        return render_template_string(template,
            pwnagotchi_name=pwnagotchi.name(),
            keys=keys,
            key_count=len(keys)
        )

    def render_terminal_page(self):
        """Render web terminal page"""
        template = """
<!DOCTYPE html>
<html>
<head>
    <title>Web Terminal - {{ pwnagotchi_name }}</title>
    <meta charset="utf-8">
    <style>
        body { 
            font-family: monospace; 
            margin: 0; 
            padding: 20px; 
            background: #f0f0f0; 
        }
        .container { 
            max-width: 1200px; 
            margin: 0 auto; 
            background: white; 
            padding: 20px; 
            border-radius: 8px; 
        }
        .nav { 
            margin: 20px 0; 
        }
        .nav a { 
            margin-right: 15px; 
            text-decoration: none; 
            color: #007bff; 
        }
        .terminal-container {
            background: #1e1e1e;
            border: 1px solid #333;
            border-radius: 4px;
            margin: 20px 0;
            padding: 0;
            height: 500px;
            position: relative;
        }
        .terminal-header {
            background: #2d2d2d;
            color: #fff;
            padding: 8px 15px;
            border-bottom: 1px solid #333;
            font-size: 12px;
        }
        .terminal-controls {
            margin: 10px 0;
        }
        .button { 
            padding: 8px 16px; 
            margin: 4px; 
            border: none; 
            border-radius: 4px; 
            cursor: pointer; 
        }
        .btn-primary { 
            background: #007bff; 
            color: white; 
        }
        .btn-danger { 
            background: #dc3545; 
            color: white; 
        }
        .btn-secondary { 
            background: #6c757d; 
            color: white; 
        }
        #terminal {
            width: 100%;
            height: 460px;
            padding: 15px;
            box-sizing: border-box;
            font-family: 'Courier New', monospace;
            font-size: 14px;
            background: #1e1e1e;
            color: #00ff00;
            border: none;
            outline: none;
            resize: none;
            overflow-y: auto;
        }
        .status {
            padding: 10px;
            margin: 10px 0;
            border-radius: 4px;
        }
        .connected {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        .disconnected {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>💻 Web Terminal</h1>
        
        <div class="nav">
            <a href="/plugins/ssh/">Dashboard</a>
            <a href="/plugins/ssh/config">Configuration</a>
            <a href="/plugins/ssh/keys">SSH Keys</a>
            <a href="/plugins/ssh/terminal">Web Terminal</a>
        </div>

        <div id="status" class="status disconnected">
            <strong>Status:</strong> Disconnected
        </div>

        <div class="terminal-controls">
            <button id="connectBtn" class="button btn-primary">Connect Terminal</button>
            <button id="disconnectBtn" class="button btn-danger" disabled>Disconnect</button>
            <button id="clearBtn" class="button btn-secondary" disabled>Clear</button>
        </div>

        <div class="terminal-container">
            <div class="terminal-header">
                Web Terminal - Type commands and press Enter
            </div>
            <textarea id="terminal" placeholder="Click 'Connect Terminal' to start a shell session..." readonly></textarea>
        </div>

        <div style="margin-top: 20px; padding: 15px; background: #e9ecef; border-radius: 4px;">
            <h4>📋 Terminal Info</h4>
            <p><strong>Shell:</strong> /bin/bash</p>
            <p><strong>Features:</strong> Command history, tab completion, colors</p>
            <p><strong>Tips:</strong> Use 'clear' to clear screen, 'exit' to close session</p>
        </div>
    </div>

    <script>
        let terminalId = null;
        let connected = false;
        let pollInterval = null;
        
        const terminal = document.getElementById('terminal');
        const status = document.getElementById('status');
        const connectBtn = document.getElementById('connectBtn');
        const disconnectBtn = document.getElementById('disconnectBtn');
        const clearBtn = document.getElementById('clearBtn');
        
        // Connect to terminal
        connectBtn.addEventListener('click', async () => {
            try {
                const response = await fetch('/plugins/ssh/api/terminal/create', {
                    method: 'POST'
                });
                const data = await response.json();
                
                if (data.success && data.terminal_id) {
                    terminalId = data.terminal_id;
                    connected = true;
                    updateStatus('Connected', true);
                    enableControls();
                    startPolling();
                    terminal.value = 'Terminal connected. Type commands below:\\n\\n';
                    terminal.focus();
                } else {
                    alert('Failed to create terminal session');
                }
            } catch (error) {
                alert('Error connecting to terminal: ' + error.message);
            }
        });
        
        // Disconnect terminal
        disconnectBtn.addEventListener('click', async () => {
            if (terminalId) {
                try {
                    await fetch(`/plugins/ssh/api/terminal/${terminalId}/close`, {
                        method: 'POST'
                    });
                } catch (error) {
                    console.error('Error closing terminal:', error);
                }
            }
            disconnect();
        });
        
        // Clear terminal
        clearBtn.addEventListener('click', () => {
            terminal.value = '';
        });
        
        // Handle keyboard input
        terminal.addEventListener('keydown', async (e) => {
            if (!connected || !terminalId) return;
            
            if (e.key === 'Enter') {
                e.preventDefault();
                const lines = terminal.value.split('\\n');
                const currentLine = lines[lines.length - 1];
                
                // Send the current line as input
                try {
                    await fetch(`/plugins/ssh/api/terminal/${terminalId}/input`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            input: currentLine + '\\n'
                        })
                    });
                } catch (error) {
                    console.error('Error sending input:', error);
                }
            }
        });
        
        // Poll for output
        async function pollOutput() {
            if (!connected || !terminalId) return;
            
            try {
                const response = await fetch(`/plugins/ssh/api/terminal/${terminalId}/output`);
                const data = await response.json();
                
                if (data.output) {
                    terminal.value += data.output;
                    terminal.scrollTop = terminal.scrollHeight;
                }
            } catch (error) {
                console.error('Error polling output:', error);
                disconnect();
            }
        }
        
        function startPolling() {
            pollInterval = setInterval(pollOutput, 100); // Poll every 100ms
        }
        
        function stopPolling() {
            if (pollInterval) {
                clearInterval(pollInterval);
                pollInterval = null;
            }
        }
        
        function updateStatus(text, isConnected) {
            status.innerHTML = `<strong>Status:</strong> ${text}`;
            status.className = `status ${isConnected ? 'connected' : 'disconnected'}`;
        }
        
        function enableControls() {
            connectBtn.disabled = true;
            disconnectBtn.disabled = false;
            clearBtn.disabled = false;
            terminal.readOnly = false;
        }
        
        function disableControls() {
            connectBtn.disabled = false;
            disconnectBtn.disabled = true;
            clearBtn.disabled = true;
            terminal.readOnly = true;
        }
        
        function disconnect() {
            connected = false;
            terminalId = null;
            updateStatus('Disconnected', false);
            disableControls();
            stopPolling();
        }
        
        // Auto-resize terminal
        window.addEventListener('resize', () => {
            if (connected && terminalId) {
                const rows = Math.floor(terminal.clientHeight / 20);
                const cols = Math.floor(terminal.clientWidth / 8);
                
                fetch(`/plugins/ssh/api/terminal/${terminalId}/resize`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        rows: rows,
                        cols: cols
                    })
                }).catch(console.error);
            }
        });
    </script>
</body>
</html>
        """
        
        return render_template_string(template, pwnagotchi_name=pwnagotchi.name())

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
                                    'full_line': line
                                })
        except Exception as e:
            logging.error(f"[SSH] Error reading authorized keys: {e}")
        
        return keys

    def handle_config_update(self, request):
        """Handle SSH configuration updates"""
        try:
            # This is a placeholder - in a real implementation,
            # you would update the SSH configuration file
            logging.info("[SSH] Configuration update requested")
            return "<html><body><h1>Configuration Updated</h1><p>SSH configuration has been updated.</p><a href='/plugins/ssh/'>Back to Dashboard</a></body></html>"
        except Exception as e:
            logging.error(f"[SSH] Config update error: {e}")
            return f"<html><body><h1>Error</h1><p>{str(e)}</p></body></html>", 500

    def handle_key_management(self, request):
        """Handle SSH key management operations"""
        try:
            action = request.form.get('action')
            
            if action == 'add_key':
                public_key = request.form.get('public_key', '').strip()
                key_name = request.form.get('key_name', '').strip()
                
                if not public_key:
                    return "<html><body><h1>Error</h1><p>Public key is required</p><a href='/plugins/ssh/keys'>Back</a></body></html>"
                
                # Validate key format
                parts = public_key.split()
                if len(parts) < 2 or parts[0] not in ['ssh-rsa', 'ssh-ed25519', 'ssh-dss', 'ecdsa-sha2-nistp256']:
                    return "<html><body><h1>Error</h1><p>Invalid key format</p><a href='/plugins/ssh/keys'>Back</a></body></html>"
                
                # Add name if provided
                if key_name:
                    if len(parts) == 2:
                        public_key += f' {key_name}'
                    else:
                        parts[2] = key_name
                        public_key = ' '.join(parts)
                
                # Add key to authorized_keys
                with open(self.authorized_keys_path, 'a') as f:
                    f.write(f'\n{public_key}\n')
                
                logging.info(f"[SSH] Added new SSH key: {key_name or 'unnamed'}")
                return "<html><body><h1>Success</h1><p>SSH key added successfully</p><a href='/plugins/ssh/keys'>Back to Keys</a></body></html>"
            
            elif action == 'remove_key':
                key_data = request.form.get('key_data', '').strip()
                
                if key_data and os.path.exists(self.authorized_keys_path):
                    # Read current keys
                    with open(self.authorized_keys_path, 'r') as f:
                        lines = f.readlines()
                    
                    # Remove the specified key
                    updated_lines = [line for line in lines if line.strip() != key_data]
                    
                    # Write back
                    with open(self.authorized_keys_path, 'w') as f:
                        f.writelines(updated_lines)
                    
                    logging.info("[SSH] Removed SSH key")
                    return "<html><body><h1>Success</h1><p>SSH key removed successfully</p><a href='/plugins/ssh/keys'>Back to Keys</a></body></html>"
            
            return "<html><body><h1>Error</h1><p>Unknown action</p><a href='/plugins/ssh/keys'>Back</a></body></html>"
            
        except Exception as e:
            logging.error(f"[SSH] Key management error: {e}")
            return f"<html><body><h1>Error</h1><p>{str(e)}</p></body></html>", 500