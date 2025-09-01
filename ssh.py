#!/usr/bin/env python3
"""
SSH Web Terminal Plugin for Pwnagotchi Torch
Provides a modern web-based terminal interface for SSH access
Compatible with pwnagotchi-torch-plugins architecture
"""

import logging
import subprocess
import json
import os
import time
import threading
import queue
import signal
import pty
import select
import termios
import struct
import fcntl
from datetime import datetime

import pwnagotchi
import pwnagotchi.plugins as plugins
import pwnagotchi.ui.fonts as fonts
from pwnagotchi.ui.components import LabeledValue
from pwnagotchi.ui.view import BLACK

from flask import render_template_string, request, jsonify, abort


class WebTerminalSession:
    """Enhanced web terminal session with better error handling and features"""
    
    def __init__(self, session_id):
        self.session_id = session_id
        self.active = True
        self.created_at = time.time()
        self.last_activity = time.time()
        self.output_buffer = queue.Queue(maxsize=1000)
        self.command_history = []
        
        # Platform-specific initialization
        import platform
        self.platform = platform.system().lower()
        
        if self.platform == "windows":
            self._init_windows_terminal()
        else:
            self._init_unix_terminal()
    
    def _init_windows_terminal(self):
        """Initialize Windows terminal using PowerShell"""
        try:
            # Try PowerShell Core first, then Windows PowerShell
            for ps_cmd in ['pwsh.exe', 'powershell.exe']:
                try:
                    self.process = subprocess.Popen(
                        [ps_cmd, '-NoLogo', '-NoProfile', '-Command', '-'],
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        bufsize=0,
                        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
                    )
                    break
                except FileNotFoundError:
                    continue
            else:
                # Fallback to cmd.exe
                self.process = subprocess.Popen(
                    ['cmd.exe'],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=0,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
                )
            
            # Start output reader
            self.output_thread = threading.Thread(
                target=self._read_windows_output, 
                daemon=True
            )
            self.output_thread.start()
            
            logging.info(f"[SSH-WebTerm] Windows terminal session {self.session_id} initialized")
            
        except Exception as e:
            logging.error(f"[SSH-WebTerm] Failed to initialize Windows terminal: {e}")
            self.active = False
    
    def _init_unix_terminal(self):
        """Initialize Unix/Linux terminal using pty"""
        try:
            # Create pseudo-terminal
            self.master_fd, slave_fd = pty.openpty()
            
            # Fork process
            self.pid = os.fork()
            if self.pid == 0:
                # Child process - become shell
                os.setsid()
                os.dup2(slave_fd, 0)  # stdin
                os.dup2(slave_fd, 1)  # stdout
                os.dup2(slave_fd, 2)  # stderr
                os.close(self.master_fd)
                os.close(slave_fd)
                
                # Set environment variables
                os.environ['TERM'] = 'xterm-256color'
                os.environ['SHELL'] = '/bin/bash'
                os.environ['PS1'] = r'\u@\h:\w$ '
                
                # Execute shell
                os.execv('/bin/bash', ['/bin/bash', '-l'])
            else:
                # Parent process
                os.close(slave_fd)
                
                # Make master non-blocking
                fcntl.fcntl(self.master_fd, fcntl.F_SETFL, os.O_NONBLOCK)
                
                # Start output reader
                self.output_thread = threading.Thread(
                    target=self._read_unix_output, 
                    daemon=True
                )
                self.output_thread.start()
                
                logging.info(f"[SSH-WebTerm] Unix terminal session {self.session_id} initialized")
                
        except Exception as e:
            logging.error(f"[SSH-WebTerm] Failed to initialize Unix terminal: {e}")
            self.active = False
    
    def _read_windows_output(self):
        """Read output from Windows subprocess"""
        while self.active and self.process.poll() is None:
            try:
                line = self.process.stdout.readline()
                if line:
                    self.output_buffer.put(line.rstrip('\r\n'))
                    self.last_activity = time.time()
                else:
                    time.sleep(0.05)  # Prevent busy waiting
            except Exception as e:
                logging.error(f"[SSH-WebTerm] Windows output read error: {e}")
                break
        
        self.active = False
    
    def _read_unix_output(self):
        """Read output from Unix pty"""
        while self.active:
            try:
                ready, _, _ = select.select([self.master_fd], [], [], 0.1)
                if ready:
                    data = os.read(self.master_fd, 4096)
                    if data:
                        output = data.decode('utf-8', errors='ignore')
                        self.output_buffer.put(output)
                        self.last_activity = time.time()
                    else:
                        break
            except (OSError, IOError) as e:
                logging.error(f"[SSH-WebTerm] Unix output read error: {e}")
                break
        
        self.active = False
    
    def write_input(self, data):
        """Send input to terminal"""
        if not self.active:
            return False
        
        try:
            # Add to command history if it's a complete command
            if data.endswith('\n') and data.strip():
                cmd = data.strip()
                if cmd not in self.command_history:
                    self.command_history.append(cmd)
                    # Keep only last 50 commands
                    if len(self.command_history) > 50:
                        self.command_history.pop(0)
            
            if self.platform == "windows":
                self.process.stdin.write(data)
                self.process.stdin.flush()
            else:
                os.write(self.master_fd, data.encode('utf-8'))
            
            self.last_activity = time.time()
            return True
            
        except (OSError, IOError, BrokenPipeError) as e:
            logging.error(f"[SSH-WebTerm] Input write error: {e}")
            self.active = False
            return False
    
    def read_output(self):
        """Get accumulated output"""
        output = ""
        try:
            while not self.output_buffer.empty():
                output += self.output_buffer.get_nowait()
        except queue.Empty:
            pass
        
        return output
    
    def resize(self, rows, cols):
        """Resize terminal window"""
        if not self.active or self.platform == "windows":
            return False
        
        try:
            winsize = struct.pack('HHHH', rows, cols, 0, 0)
            fcntl.ioctl(self.master_fd, termios.TIOCSWINSZ, winsize)
            return True
        except (OSError, IOError):
            return False
    
    def close(self):
        """Close terminal session"""
        self.active = False
        
        try:
            if self.platform == "windows":
                self.process.terminate()
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.process.kill()
            else:
                os.close(self.master_fd)
                try:
                    os.kill(self.pid, signal.SIGTERM)
                    os.waitpid(self.pid, 0)
                except (OSError, ProcessLookupError):
                    pass
        except Exception as e:
            logging.error(f"[SSH-WebTerm] Error closing session: {e}")
    
    def is_alive(self):
        """Check if session is still active"""
        if not self.active:
            return False
        
        # Check for timeout (30 minutes)
        if time.time() - self.last_activity > 1800:
            self.close()
            return False
        
        if self.platform == "windows":
            return self.process.poll() is None
        else:
            try:
                os.kill(self.pid, 0)
                return True
            except ProcessLookupError:
                return False


class WebTerminalManager:
    """Manages multiple web terminal sessions"""
    
    def __init__(self):
        self.sessions = {}
        self.session_counter = 0
        self.cleanup_thread = threading.Thread(target=self._cleanup_sessions, daemon=True)
        self.cleanup_thread.start()
    
    def create_session(self):
        """Create new terminal session"""
        session_id = f"term_{int(time.time())}_{self.session_counter}"
        self.session_counter += 1
        
        session = WebTerminalSession(session_id)
        if session.active:
            self.sessions[session_id] = session
            logging.info(f"[SSH-WebTerm] Created session: {session_id}")
            return session_id
        else:
            logging.error(f"[SSH-WebTerm] Failed to create session: {session_id}")
            return None
    
    def get_session(self, session_id):
        """Get existing session"""
        return self.sessions.get(session_id)
    
    def close_session(self, session_id):
        """Close and remove session"""
        session = self.sessions.get(session_id)
        if session:
            session.close()
            del self.sessions[session_id]
            logging.info(f"[SSH-WebTerm] Closed session: {session_id}")
    
    def _cleanup_sessions(self):
        """Background cleanup of dead sessions"""
        while True:
            try:
                time.sleep(60)  # Check every minute
                dead_sessions = []
                
                for session_id, session in self.sessions.items():
                    if not session.is_alive():
                        dead_sessions.append(session_id)
                
                for session_id in dead_sessions:
                    self.close_session(session_id)
                    
            except Exception as e:
                logging.error(f"[SSH-WebTerm] Session cleanup error: {e}")


class SSH(plugins.Plugin):
    __author__ = 'Pwnagotchi Community'
    __version__ = '2.0.0'
    __license__ = 'GPL3'
    __description__ = 'Advanced SSH Web Terminal for Pwnagotchi Torch'

    def __init__(self):
        self.options = {
            'enabled': True,
            'display_on_screen': True,
            'ssh_x_coord': 160,
            'ssh_y_coord': 66,
            'auto_start_ssh': True,
            'enable_web_terminal': True,
            'terminal_theme': 'dark',
            'max_sessions': 5
        }
        
        self.ssh_status = False
        self.active_connections = 0
        self.ready = False
        self.terminal_manager = WebTerminalManager()

    def on_loaded(self):
        """Plugin initialization"""
        logging.info("[SSH-WebTerm] SSH Web Terminal plugin loaded")
        
        # Check SSH service status
        self.ssh_status = self._check_ssh_status()
        logging.info(f"[SSH-WebTerm] SSH service status: {'active' if self.ssh_status else 'inactive'}")
        
        # Auto-start SSH if configured
        if self.options.get('auto_start_ssh', True) and not self.ssh_status:
            logging.info("[SSH-WebTerm] Auto-starting SSH service...")
            self._start_ssh_service()
        
        self.ready = True

    def on_ui_setup(self, ui):
        """Setup UI display elements"""
        if not self.options.get('display_on_screen', True):
            return
            
        with ui._lock:
            ui.add_element(
                'ssh_status',
                LabeledValue(
                    color=BLACK,
                    label='SSH',
                    value='Starting...',
                    position=(
                        int(self.options.get('ssh_x_coord', 160)),
                        int(self.options.get('ssh_y_coord', 66))
                    ),
                    label_font=fonts.Small,
                    text_font=fonts.Small
                )
            )

    def on_ui_update(self, ui):
        """Update UI display"""
        if not self.options.get('display_on_screen', True):
            return
            
        current_status = self._check_ssh_status()
        self.active_connections = len(self._get_ssh_connections())
        
        if current_status:
            if self.active_connections > 0:
                status_text = f"ON[{self.active_connections}]"
            else:
                status_text = "ON"
        else:
            status_text = "OFF"
        
        ui.set('ssh_status', status_text)

    def on_unload(self, ui):
        """Plugin cleanup"""
        if self.options.get('display_on_screen', True):
            with ui._lock:
                ui.remove_element('ssh_status')
        
        # Close all terminal sessions
        for session_id in list(self.terminal_manager.sessions.keys()):
            self.terminal_manager.close_session(session_id)
        
        logging.info("[SSH-WebTerm] SSH Web Terminal plugin unloaded")

    def on_webhook(self, path, request):
        """Handle web requests"""
        if not self.ready:
            abort(503)  # Service Unavailable

        logging.info(f"[SSH-WebTerm] Webhook: {request.method} {path}")
        
        try:
            # Main dashboard
            if path == "/" or path == "" or path is None:
                return self._render_dashboard()
            
            # Web terminal page
            elif path == "terminal":
                return self._render_terminal()
            
            # API endpoints
            elif path == "api/ssh/status":
                return jsonify({
                    'ssh_active': self._check_ssh_status(),
                    'connections': len(self._get_ssh_connections()),
                    'uptime': self._get_ssh_uptime()
                })
            
            elif path == "api/ssh/start":
                success = self._start_ssh_service()
                return jsonify({'success': success})
            
            elif path == "api/ssh/stop":
                success = self._stop_ssh_service()
                return jsonify({'success': success})
            
            # Terminal API
            elif path == "api/terminal/create":
                session_id = self.terminal_manager.create_session()
                return jsonify({
                    'success': session_id is not None,
                    'session_id': session_id,
                    'message': 'Terminal session created' if session_id else 'Failed to create session'
                })
            
            elif path.startswith("api/terminal/") and "/input" in path:
                session_id = path.split("/")[2]
                data = request.get_json() or {}
                input_data = data.get('input', '')
                
                session = self.terminal_manager.get_session(session_id)
                if session:
                    success = session.write_input(input_data)
                    return jsonify({'success': success})
                else:
                    return jsonify({'success': False, 'error': 'Session not found'})
            
            elif path.startswith("api/terminal/") and "/output" in path:
                session_id = path.split("/")[2]
                session = self.terminal_manager.get_session(session_id)
                
                if session:
                    output = session.read_output()
                    return jsonify({'output': output, 'active': session.is_alive()})
                else:
                    return jsonify({'output': '', 'active': False, 'error': 'Session not found'})
            
            elif path.startswith("api/terminal/") and "/resize" in path:
                session_id = path.split("/")[2]
                data = request.get_json() or {}
                rows = data.get('rows', 24)
                cols = data.get('cols', 80)
                
                session = self.terminal_manager.get_session(session_id)
                if session:
                    success = session.resize(rows, cols)
                    return jsonify({'success': success})
                else:
                    return jsonify({'success': False, 'error': 'Session not found'})
            
            elif path.startswith("api/terminal/") and "/close" in path:
                session_id = path.split("/")[2]
                self.terminal_manager.close_session(session_id)
                return jsonify({'success': True})
            
            elif path.startswith("api/terminal/") and "/history" in path:
                session_id = path.split("/")[2]
                session = self.terminal_manager.get_session(session_id)
                
                if session:
                    return jsonify({
                        'history': session.command_history,
                        'success': True
                    })
                else:
                    return jsonify({'history': [], 'success': False})

        except Exception as e:
            logging.error(f"[SSH-WebTerm] Webhook error: {e}")
            return jsonify({'error': str(e)}), 500
        
        # 404 for unhandled paths
        abort(404)

    def _check_ssh_status(self):
        """Check SSH service status"""
        try:
            result = subprocess.run(
                ['systemctl', 'is-active', 'ssh'], 
                capture_output=True, 
                text=True,
                timeout=5
            )
            return result.returncode == 0 and result.stdout.strip() == 'active'
        except Exception:
            return False

    def _start_ssh_service(self):
        """Start SSH service"""
        try:
            result = subprocess.run(
                ['sudo', 'systemctl', 'start', 'ssh'], 
                capture_output=True, 
                text=True,
                timeout=10
            )
            success = result.returncode == 0
            if success:
                logging.info("[SSH-WebTerm] SSH service started")
                self.ssh_status = True
            return success
        except Exception as e:
            logging.error(f"[SSH-WebTerm] Failed to start SSH: {e}")
            return False

    def _stop_ssh_service(self):
        """Stop SSH service"""
        try:
            result = subprocess.run(
                ['sudo', 'systemctl', 'stop', 'ssh'], 
                capture_output=True, 
                text=True,
                timeout=10
            )
            success = result.returncode == 0
            if success:
                logging.info("[SSH-WebTerm] SSH service stopped")
                self.ssh_status = False
            return success
        except Exception as e:
            logging.error(f"[SSH-WebTerm] Failed to stop SSH: {e}")
            return False

    def _get_ssh_connections(self):
        """Get active SSH connections"""
        connections = []
        try:
            result = subprocess.run(
                ['ss', '-tuln'], 
                capture_output=True, 
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if ':22' in line and 'LISTEN' not in line and 'ESTAB' in line:
                        parts = line.split()
                        if len(parts) >= 5:
                            connections.append({
                                'local': parts[3],
                                'remote': parts[4],
                                'time': datetime.now().strftime('%H:%M:%S')
                            })
        except Exception:
            pass
        
        return connections

    def _get_ssh_uptime(self):
        """Get SSH service uptime"""
        try:
            result = subprocess.run(
                ['systemctl', 'show', 'ssh', '--property=ActiveEnterTimestamp'], 
                capture_output=True, 
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip().split('=')[1]
        except Exception:
            pass
        return "Unknown"

    def _render_dashboard(self):
        """Render main dashboard"""
        ssh_active = self._check_ssh_status()
        connections = self._get_ssh_connections()
        active_terminals = len(self.terminal_manager.sessions)
        
        template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SSH Web Terminal - {{ pwnagotchi_name }}</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            min-height: 100vh;
        }
        .container { 
            max-width: 1200px; 
            margin: 0 auto; 
            padding: 20px;
        }
        .header {
            background: rgba(255,255,255,0.95);
            padding: 20px;
            border-radius: 15px;
            margin-bottom: 20px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            backdrop-filter: blur(10px);
        }
        .header h1 {
            font-size: 2.5em;
            color: #2c3e50;
            margin-bottom: 10px;
        }
        .header p {
            color: #7f8c8d;
            font-size: 1.1em;
        }
        .card {
            background: rgba(255,255,255,0.95);
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 20px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            backdrop-filter: blur(10px);
        }
        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .status-card {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            padding: 20px;
            border-radius: 12px;
            text-align: center;
        }
        .status-card.active {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        }
        .status-card.warning {
            background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
        }
        .status-value {
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 5px;
        }
        .status-label {
            font-size: 1.1em;
            opacity: 0.9;
        }
        .btn {
            display: inline-block;
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            font-size: 1em;
            font-weight: bold;
            text-decoration: none;
            cursor: pointer;
            transition: all 0.3s ease;
            margin: 5px;
        }
        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .btn-success {
            background: linear-gradient(135deg, #56ab2f 0%, #a8e6cf 100%);
            color: white;
        }
        .btn-danger {
            background: linear-gradient(135deg, #ff416c 0%, #ff4b2b 100%);
            color: white;
        }
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }
        .terminal-preview {
            background: #1e1e1e;
            color: #00ff00;
            padding: 20px;
            border-radius: 10px;
            font-family: 'Courier New', monospace;
            margin: 20px 0;
        }
        .feature-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }
        .feature-card {
            background: rgba(255,255,255,0.8);
            padding: 20px;
            border-radius: 10px;
            border-left: 4px solid #667eea;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .nav {
            margin: 20px 0;
        }
        .nav a {
            color: #667eea;
            text-decoration: none;
            margin-right: 20px;
            font-weight: bold;
        }
        .footer {
            text-align: center;
            margin-top: 40px;
            opacity: 0.7;
        }
    </style>
    <script>
        function toggleSSH(action) {
            fetch(`/plugins/ssh/api/ssh/${action}`, {method: 'POST'})
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        location.reload();
                    } else {
                        alert(`Failed to ${action} SSH service`);
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('Operation failed');
                });
        }
        
        // Auto-refresh status every 30 seconds
        setInterval(() => {
            fetch('/plugins/ssh/api/ssh/status')
                .then(response => response.json())
                .then(data => {
                    // Update status indicators without full page reload
                    console.log('Status updated:', data);
                })
                .catch(error => console.error('Status update failed:', error));
        }, 30000);
    </script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 SSH Web Terminal</h1>
            <p>Advanced terminal interface for {{ pwnagotchi_name }}</p>
            <div class="nav">
                <a href="/plugins/ssh/">🏠 Dashboard</a>
                <a href="/plugins/ssh/terminal">💻 Web Terminal</a>
            </div>
        </div>

        <div class="status-grid">
            <div class="status-card {{ 'active' if ssh_active else 'warning' }}">
                <div class="status-value">{{ 'ON' if ssh_active else 'OFF' }}</div>
                <div class="status-label">SSH Service</div>
            </div>
            <div class="status-card active">
                <div class="status-value">{{ connection_count }}</div>
                <div class="status-label">SSH Connections</div>
            </div>
            <div class="status-card">
                <div class="status-value">{{ terminal_count }}</div>
                <div class="status-label">Active Terminals</div>
            </div>
        </div>

        <div class="card">
            <h2>🔧 Service Control</h2>
            <div style="margin: 20px 0;">
                {% if ssh_active %}
                    <button class="btn btn-danger" onclick="toggleSSH('stop')">🛑 Stop SSH</button>
                {% else %}
                    <button class="btn btn-success" onclick="toggleSSH('start')">▶️ Start SSH</button>
                {% endif %}
                <a href="/plugins/ssh/terminal" class="btn btn-primary">💻 Open Web Terminal</a>
            </div>
        </div>

        {% if connections %}
        <div class="card">
            <h2>🌐 Active SSH Connections</h2>
            <table>
                <thead>
                    <tr>
                        <th>Local Address</th>
                        <th>Remote Address</th>
                        <th>Connection Time</th>
                    </tr>
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
        </div>
        {% endif %}

        <div class="card">
            <h2>🖥️ Web Terminal Preview</h2>
            <div class="terminal-preview">
                pi@pwnagotchi:~$ ssh-keygen -t ed25519<br>
                Generating public/private ed25519 key pair...<br>
                pi@pwnagotchi:~$ systemctl status ssh<br>
                <span style="color: #00ff00;">● ssh.service - OpenBSD Secure Shell server</span><br>
                &nbsp;&nbsp;&nbsp;Active: <span style="color: #00ff00;">active (running)</span><br>
                pi@pwnagotchi:~$ █
            </div>
            <a href="/plugins/ssh/terminal" class="btn btn-primary">🚀 Launch Full Terminal</a>
        </div>

        <div class="feature-grid">
            <div class="feature-card">
                <h3>⚡ Real-time Terminal</h3>
                <p>Full bash shell with real-time input/output, command history, and tab completion support.</p>
            </div>
            <div class="feature-card">
                <h3>🔒 Secure Access</h3>
                <p>Direct access to your Pwnagotchi through secure web interface without external SSH clients.</p>
            </div>
            <div class="feature-card">
                <h3>📱 Cross-platform</h3>
                <p>Works on any device with a web browser - desktop, tablet, or mobile.</p>
            </div>
            <div class="feature-card">
                <h3>🎨 Modern Interface</h3>
                <p>Beautiful, responsive design with dark theme and terminal emulation.</p>
            </div>
        </div>

        <div class="footer">
            <p>SSH Web Terminal v2.0.0 - Built for Pwnagotchi Torch 🔥</p>
        </div>
    </div>
</body>
</html>
        """
        
        return render_template_string(
            template,
            pwnagotchi_name=pwnagotchi.name(),
            ssh_active=ssh_active,
            connections=connections,
            connection_count=len(connections),
            terminal_count=active_terminals
        )

    def _render_terminal(self):
        """Render terminal interface"""
        template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Web Terminal - {{ pwnagotchi_name }}</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace; 
            background: #1a1a1a;
            color: #fff;
            height: 100vh;
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 10px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.3);
        }
        .header h1 {
            font-size: 1.5em;
            margin: 0;
        }
        .controls {
            display: flex;
            gap: 10px;
        }
        .btn {
            padding: 8px 16px;
            border: none;
            border-radius: 6px;
            font-size: 0.9em;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        .btn-primary { background: #007bff; color: white; }
        .btn-success { background: #28a745; color: white; }
        .btn-danger { background: #dc3545; color: white; }
        .btn-secondary { background: #6c757d; color: white; }
        .btn:hover { opacity: 0.8; transform: translateY(-1px); }
        .btn:disabled { opacity: 0.5; cursor: not-allowed; }
        
        .status-bar {
            background: #2a2a2a;
            padding: 8px 20px;
            font-size: 0.9em;
            border-bottom: 1px solid #444;
        }
        .status-connected { color: #28a745; }
        .status-disconnected { color: #dc3545; }
        .status-connecting { color: #ffc107; }
        
        .terminal-container {
            height: calc(100vh - 120px);
            background: #0d1117;
            position: relative;
        }
        .terminal {
            width: 100%;
            height: 100%;
            background: #0d1117;
            color: #58a6ff;
            font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Roboto Mono', monospace;
            font-size: 14px;
            line-height: 1.4;
            padding: 20px;
            border: none;
            outline: none;
            resize: none;
            overflow-y: auto;
            white-space: pre-wrap;
            word-wrap: break-word;
        }
        .terminal:focus {
            background: #0d1117;
        }
        .terminal::placeholder {
            color: #6e7681;
        }
        
        .input-line {
            background: #161b22;
            border-top: 1px solid #30363d;
            padding: 10px 20px;
            display: flex;
            align-items: center;
        }
        .prompt {
            color: #7c3aed;
            margin-right: 8px;
            font-weight: bold;
        }
        .command-input {
            flex: 1;
            background: transparent;
            border: none;
            color: #f0f6fc;
            font-family: inherit;
            font-size: 14px;
            outline: none;
        }
        
        .nav {
            margin-right: 20px;
        }
        .nav a {
            color: rgba(255,255,255,0.8);
            text-decoration: none;
            margin-left: 15px;
            font-size: 0.9em;
        }
        .nav a:hover {
            color: white;
        }
        
        /* Terminal animations */
        .cursor {
            animation: blink 1s infinite;
        }
        @keyframes blink {
            0%, 50% { opacity: 1; }
            51%, 100% { opacity: 0; }
        }
        
        /* Responsive design */
        @media (max-width: 768px) {
            .header h1 { font-size: 1.2em; }
            .controls { gap: 5px; }
            .btn { padding: 6px 12px; font-size: 0.8em; }
            .terminal { font-size: 12px; padding: 15px; }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>💻 Web Terminal</h1>
        <div style="display: flex; align-items: center;">
            <div class="nav">
                <a href="/plugins/ssh/">🏠 Dashboard</a>
            </div>
            <div class="controls">
                <button id="connectBtn" class="btn btn-success">🔌 Connect</button>
                <button id="disconnectBtn" class="btn btn-danger" disabled>🔌 Disconnect</button>
                <button id="clearBtn" class="btn btn-secondary" disabled>🗑️ Clear</button>
                <button id="fullscreenBtn" class="btn btn-primary">🔍 Fullscreen</button>
            </div>
        </div>
    </div>
    
    <div class="status-bar">
        <span id="status" class="status-disconnected">● Disconnected</span>
        <span id="sessionInfo" style="margin-left: 20px;"></span>
    </div>
    
    <div class="terminal-container">
        <textarea id="terminal" class="terminal" placeholder="Click Connect to start terminal session..." readonly></textarea>
    </div>
    
    <div class="input-line">
        <span class="prompt" id="prompt">$</span>
        <input type="text" id="commandInput" class="command-input" placeholder="Type commands here..." disabled>
    </div>

    <script>
        class WebTerminal {
            constructor() {
                this.sessionId = null;
                this.connected = false;
                this.pollInterval = null;
                this.commandHistory = [];
                this.historyIndex = -1;
                
                this.terminal = document.getElementById('terminal');
                this.commandInput = document.getElementById('commandInput');
                this.status = document.getElementById('status');
                this.sessionInfo = document.getElementById('sessionInfo');
                
                this.connectBtn = document.getElementById('connectBtn');
                this.disconnectBtn = document.getElementById('disconnectBtn');
                this.clearBtn = document.getElementById('clearBtn');
                this.fullscreenBtn = document.getElementById('fullscreenBtn');
                
                this.initializeEventListeners();
            }
            
            initializeEventListeners() {
                this.connectBtn.addEventListener('click', () => this.connect());
                this.disconnectBtn.addEventListener('click', () => this.disconnect());
                this.clearBtn.addEventListener('click', () => this.clearTerminal());
                this.fullscreenBtn.addEventListener('click', () => this.toggleFullscreen());
                
                this.commandInput.addEventListener('keydown', (e) => this.handleKeyDown(e));
                this.commandInput.addEventListener('keyup', (e) => this.handleKeyUp(e));
                
                // Auto-resize handling
                window.addEventListener('resize', () => this.handleResize());
                
                // Focus management
                this.terminal.addEventListener('click', () => this.commandInput.focus());
                
                // Auto-connect on load
                setTimeout(() => this.connect(), 1000);
            }
            
            async connect() {
                try {
                    this.updateStatus('Connecting...', 'connecting');
                    this.connectBtn.disabled = true;
                    
                    const response = await fetch('/plugins/ssh/api/terminal/create', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' }
                    });
                    
                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                    }
                    
                    const data = await response.json();
                    
                    if (data.success && data.session_id) {
                        this.sessionId = data.session_id;
                        this.connected = true;
                        this.updateStatus('Connected', 'connected');
                        this.sessionInfo.textContent = `Session: ${this.sessionId}`;
                        this.enableControls();
                        this.startPolling();
                        this.terminal.value = `Welcome to Pwnagotchi Web Terminal\\n`;
                        this.terminal.value += `Session ID: ${this.sessionId}\\n`;
                        this.terminal.value += `Type 'help' for available commands\\n\\n`;
                        this.commandInput.focus();
                        
                        // Load command history
                        this.loadCommandHistory();
                    } else {
                        throw new Error(data.message || 'Failed to create terminal session');
                    }
                } catch (error) {
                    console.error('Connection error:', error);
                    this.updateStatus(`Error: ${error.message}`, 'disconnected');
                    this.connectBtn.disabled = false;
                }
            }
            
            async disconnect() {
                if (this.sessionId) {
                    try {
                        await fetch(`/plugins/ssh/api/terminal/${this.sessionId}/close`, {
                            method: 'POST'
                        });
                    } catch (error) {
                        console.error('Error closing session:', error);
                    }
                }
                
                this.connected = false;
                this.sessionId = null;
                this.updateStatus('Disconnected', 'disconnected');
                this.sessionInfo.textContent = '';
                this.disableControls();
                this.stopPolling();
            }
            
            clearTerminal() {
                this.terminal.value = '';
                this.commandInput.focus();
            }
            
            toggleFullscreen() {
                if (!document.fullscreenElement) {
                    document.documentElement.requestFullscreen();
                    this.fullscreenBtn.textContent = '🔍 Exit Fullscreen';
                } else {
                    document.exitFullscreen();
                    this.fullscreenBtn.textContent = '🔍 Fullscreen';
                }
            }
            
            async handleKeyDown(e) {
                if (!this.connected || !this.sessionId) return;
                
                switch (e.key) {
                    case 'Enter':
                        e.preventDefault();
                        await this.executeCommand();
                        break;
                    case 'ArrowUp':
                        e.preventDefault();
                        this.navigateHistory(-1);
                        break;
                    case 'ArrowDown':
                        e.preventDefault();
                        this.navigateHistory(1);
                        break;
                    case 'Tab':
                        e.preventDefault();
                        // TODO: Implement tab completion
                        break;
                    case 'c':
                        if (e.ctrlKey) {
                            e.preventDefault();
                            await this.sendInput('\\x03'); // Ctrl+C
                        }
                        break;
                }
            }
            
            handleKeyUp(e) {
                // Update prompt based on input
                const input = this.commandInput.value;
                if (input.length > 0) {
                    document.getElementById('prompt').textContent = '>';
                } else {
                    document.getElementById('prompt').textContent = '$';
                }
            }
            
            async executeCommand() {
                const command = this.commandInput.value.trim();
                if (!command) return;
                
                // Add to history
                if (command !== this.commandHistory[this.commandHistory.length - 1]) {
                    this.commandHistory.push(command);
                    if (this.commandHistory.length > 100) {
                        this.commandHistory.shift();
                    }
                }
                this.historyIndex = this.commandHistory.length;
                
                // Display command in terminal
                this.terminal.value += `$ ${command}\\n`;
                
                // Send to backend
                await this.sendInput(command + '\\n');
                
                // Clear input
                this.commandInput.value = '';
                document.getElementById('prompt').textContent = '$';
            }
            
            async sendInput(input) {
                if (!this.connected || !this.sessionId) return;
                
                try {
                    await fetch(`/plugins/ssh/api/terminal/${this.sessionId}/input`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ input: input })
                    });
                } catch (error) {
                    console.error('Error sending input:', error);
                }
            }
            
            async pollOutput() {
                if (!this.connected || !this.sessionId) return;
                
                try {
                    const response = await fetch(`/plugins/ssh/api/terminal/${this.sessionId}/output`);
                    const data = await response.json();
                    
                    if (data.output) {
                        this.terminal.value += data.output;
                        this.terminal.scrollTop = this.terminal.scrollHeight;
                    }
                    
                    if (!data.active) {
                        this.disconnect();
                    }
                } catch (error) {
                    console.error('Polling error:', error);
                    this.disconnect();
                }
            }
            
            async loadCommandHistory() {
                if (!this.sessionId) return;
                
                try {
                    const response = await fetch(`/plugins/ssh/api/terminal/${this.sessionId}/history`);
                    const data = await response.json();
                    
                    if (data.success) {
                        this.commandHistory = data.history || [];
                        this.historyIndex = this.commandHistory.length;
                    }
                } catch (error) {
                    console.error('Error loading history:', error);
                }
            }
            
            navigateHistory(direction) {
                if (this.commandHistory.length === 0) return;
                
                this.historyIndex += direction;
                
                if (this.historyIndex < 0) {
                    this.historyIndex = 0;
                } else if (this.historyIndex >= this.commandHistory.length) {
                    this.historyIndex = this.commandHistory.length;
                    this.commandInput.value = '';
                    return;
                }
                
                this.commandInput.value = this.commandHistory[this.historyIndex] || '';
            }
            
            startPolling() {
                this.pollInterval = setInterval(() => this.pollOutput(), 200);
            }
            
            stopPolling() {
                if (this.pollInterval) {
                    clearInterval(this.pollInterval);
                    this.pollInterval = null;
                }
            }
            
            updateStatus(text, type) {
                this.status.textContent = `● ${text}`;
                this.status.className = `status-${type}`;
            }
            
            enableControls() {
                this.connectBtn.disabled = true;
                this.disconnectBtn.disabled = false;
                this.clearBtn.disabled = false;
                this.commandInput.disabled = false;
            }
            
            disableControls() {
                this.connectBtn.disabled = false;
                this.disconnectBtn.disabled = true;
                this.clearBtn.disabled = true;
                this.commandInput.disabled = true;
            }
            
            async handleResize() {
                if (!this.connected || !this.sessionId) return;
                
                const rows = Math.floor(this.terminal.clientHeight / 20);
                const cols = Math.floor(this.terminal.clientWidth / 8);
                
                try {
                    await fetch(`/plugins/ssh/api/terminal/${this.sessionId}/resize`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ rows, cols })
                    });
                } catch (error) {
                    console.error('Resize error:', error);
                }
            }
        }
        
        // Initialize terminal when page loads
        window.addEventListener('load', () => {
            window.webTerminal = new WebTerminal();
        });
        
        // Handle fullscreen changes
        document.addEventListener('fullscreenchange', () => {
            const btn = document.getElementById('fullscreenBtn');
            if (document.fullscreenElement) {
                btn.textContent = '🔍 Exit Fullscreen';
            } else {
                btn.textContent = '🔍 Fullscreen';
            }
        });
    </script>
</body>
</html>
        """
        
        return render_template_string(template, pwnagotchi_name=pwnagotchi.name())