# Contributing to SSH Web Terminal Plugin

Thank you for your interest in contributing to the SSH Web Terminal plugin for Pwnagotchi Torch! 🎉

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- Git
- A Pwnagotchi device or development environment
- Basic knowledge of Python, Flask, and JavaScript

### Development Setup

1. **Fork the repository**
   ```bash
   # Visit https://github.com/Pureach22/pwnagotchi-ssh-plugin and click Fork
   ```

2. **Clone your fork**
   ```bash
   git clone https://github.com/YOUR_USERNAME/pwnagotchi-ssh-plugin.git
   cd pwnagotchi-ssh-plugin
   ```

3. **Create a virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install pytest black flake8  # Development tools
   ```

## 🛠️ Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Your Changes

- **Python Code**: Follow PEP 8 style guidelines
- **JavaScript**: Use modern ES6+ features
- **CSS**: Maintain consistent styling
- **Documentation**: Update README.md if needed

### 3. Test Your Changes

```bash
# Run linting
flake8 ssh.py

# Format code
black ssh.py

# Run tests (when available)
pytest tests/
```

### 4. Commit Your Changes

```bash
git add .
git commit -m "feat: add your feature description"
```

**Commit Message Format:**
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes
- `refactor:` Code refactoring
- `test:` Adding tests
- `chore:` Maintenance tasks

### 5. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

## 📝 Code Guidelines

### Python Style

- Follow [PEP 8](https://pep8.org/)
- Use type hints where possible
- Add docstrings to functions and classes
- Keep functions small and focused

**Example:**
```python
def create_terminal_session(self, session_type: str = "bash") -> Optional[str]:
    """
    Create a new terminal session.
    
    Args:
        session_type: Type of terminal session to create
        
    Returns:
        Session ID if successful, None otherwise
    """
    # Implementation here
    pass
```

### JavaScript Style

- Use `const` and `let` instead of `var`
- Use arrow functions for callbacks
- Add JSDoc comments for functions
- Use async/await for promises

**Example:**
```javascript
/**
 * Send input to terminal session
 * @param {string} sessionId - The terminal session ID
 * @param {string} input - Input to send
 * @returns {Promise<boolean>} Success status
 */
async function sendInput(sessionId, input) {
    // Implementation here
}
```

### CSS Style

- Use consistent naming (kebab-case)
- Group related properties
- Use CSS custom properties for colors
- Mobile-first responsive design

## 🧪 Testing

### Manual Testing

1. **Plugin Installation**
   ```bash
   # Test plugin installation on a Pwnagotchi device
   sudo cp ssh.py /usr/local/share/pwnagotchi/custom-plugins/
   sudo systemctl restart pwnagotchi
   ```

2. **Web Interface**
   - Test dashboard functionality
   - Test terminal connectivity
   - Test on different devices (mobile, desktop)
   - Test different browsers

3. **API Testing**
   ```bash
   # Test API endpoints
   curl -X POST http://localhost:8080/plugins/ssh/api/terminal/create
   curl http://localhost:8080/plugins/ssh/api/ssh/status
   ```

### Automated Testing (Future)

We're working on adding automated tests. When available:

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_terminal.py

# Run with coverage
pytest --cov=ssh
```

## 🐛 Bug Reports

When reporting bugs, please include:

1. **Environment Information**
   - Pwnagotchi version
   - Plugin version
   - Python version
   - Operating system

2. **Steps to Reproduce**
   - Clear, numbered steps
   - Expected behavior
   - Actual behavior

3. **Logs and Screenshots**
   - Relevant log excerpts
   - Screenshots if applicable
   - Error messages

**Bug Report Template:**
```markdown
## Bug Description
Brief description of the bug

## Environment
- Pwnagotchi Version: 
- Plugin Version: 
- Python Version: 
- OS: 

## Steps to Reproduce
1. 
2. 
3. 

## Expected Behavior
What should happen

## Actual Behavior
What actually happens

## Logs
```
Relevant log output
```

## Screenshots
If applicable
```

## 💡 Feature Requests

We welcome feature requests! Please:

1. **Check existing issues** to avoid duplicates
2. **Describe the use case** - why is this needed?
3. **Propose a solution** - how should it work?
4. **Consider alternatives** - are there other ways to solve this?

**Feature Request Template:**
```markdown
## Feature Description
Clear description of the feature

## Use Case
Why is this feature needed?

## Proposed Solution
How should this feature work?

## Alternatives Considered
Other ways to solve this problem

## Additional Context
Any other relevant information
```

## 📚 Documentation

### Documentation Changes

- Update README.md for new features
- Add code comments for complex logic
- Update API documentation
- Include examples for new features

### Documentation Style

- Use clear, concise language
- Include code examples
- Add screenshots for UI changes
- Use proper Markdown formatting

## 🏆 Recognition

Contributors will be:

- Added to the README contributors section
- Mentioned in release notes
- Credited in commit messages

## 📞 Getting Help

Need help contributing?

- 💬 **Discussions**: [GitHub Discussions](https://github.com/Pureach22/pwnagotchi-ssh-plugin/discussions)
- 🐛 **Issues**: [GitHub Issues](https://github.com/Pureach22/pwnagotchi-ssh-plugin/issues)
- 🌐 **Community**: [Pwnagotchi Discord](https://discord.gg/pwnagotchi)

## 📄 License

By contributing to this project, you agree that your contributions will be licensed under the same GPL-3.0 License that covers the project.

---

**Thank you for contributing to the SSH Web Terminal plugin! 🙏**