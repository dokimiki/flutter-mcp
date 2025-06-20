# Contributing to Flutter MCP 🎉

First off, **thank you** for considering contributing to Flutter MCP! 🙏 This is an open-source community project, and it's people like you who make it possible to give AI assistants real-time Flutter superpowers. Whether you're fixing a typo, reporting a bug, or adding a major feature, every contribution matters!

## 🌟 Ways to Contribute

There are many ways to contribute to Flutter MCP, and we value them all:

### 🐛 Report Bugs
Found something broken? [Open an issue](https://github.com/yourusername/flutter-mcp/issues/new?template=bug_report.md) and help us squash it!

### 💡 Suggest Features
Have an idea to make Flutter MCP even better? [Start a discussion](https://github.com/yourusername/flutter-mcp/discussions/new?category=ideas) or [open a feature request](https://github.com/yourusername/flutter-mcp/issues/new?template=feature_request.md)!

### 📖 Improve Documentation
Even the smallest documentation fix helps! Whether it's fixing a typo, clarifying instructions, or adding examples - documentation is crucial.

### 🧪 Write Tests
Help us maintain quality by adding tests. We aim for high test coverage to ensure Flutter MCP stays reliable.

### 🌐 Add Translations
Make Flutter MCP accessible to developers worldwide by helping with translations.

### ⭐ Spread the Word
Star the repo, share it with your Flutter community, write a blog post, or tweet about your experience!

### 💻 Write Code
Fix bugs, implement features, optimize performance - dive into the code and make Flutter MCP better!

## 🚀 Getting Started

### Prerequisites

Before you begin, ensure you have:
- Python 3.10 or higher
- Redis installed and running
- Git for version control
- A GitHub account

### Development Setup

1. **Fork the repository**
   
   Click the "Fork" button at the top right of the [Flutter MCP repository](https://github.com/yourusername/flutter-mcp).

2. **Clone your fork**
   
   ```bash
   git clone https://github.com/YOUR-USERNAME/flutter-mcp.git
   cd flutter-mcp
   ```

3. **Set up the development environment**
   
   ```bash
   # Create a virtual environment
   python -m venv venv
   
   # Activate it
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install dependencies in development mode
   pip install -e ".[dev]"
   ```

4. **Start Redis**
   
   ```bash
   # macOS
   brew services start redis
   
   # Linux
   sudo systemctl start redis
   
   # Docker
   docker run -d -p 6379:6379 --name flutter-mcp-redis redis:alpine
   ```

5. **Run the development server**
   
   ```bash
   # Run with MCP Inspector for debugging
   mcp dev src/flutter_mcp/server.py
   
   # Or run directly
   python -m flutter_mcp.server
   ```

For more detailed setup instructions, check out our [Development Guide](DEVELOPMENT.md).

## 📋 Before You Submit

### 🎨 Code Style Guidelines

We use Python's standard style guidelines with a few preferences:

- **Black** for code formatting (line length: 88)
- **isort** for import sorting
- **Type hints** for all public functions
- **Docstrings** for all classes and public methods

Run the formatters before committing:

```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Check types
mypy src/

# Run linter
ruff check src/ tests/
```

### 🧪 Testing Guidelines

All code changes should include tests:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=flutter_mcp

# Run specific test file
pytest tests/test_server.py

# Run tests in watch mode
pytest-watch
```

We aim for at least 80% test coverage. Write tests that:
- Cover both happy paths and edge cases
- Are isolated and don't depend on external services
- Use mocks for Redis and external API calls
- Have descriptive names that explain what they test

### 📝 Commit Messages

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
feat: add support for package version constraints
fix: handle rate limiting from pub.dev API
docs: update Redis installation instructions
test: add tests for cache expiration
refactor: extract documentation parser into separate module
```

## 🔄 Pull Request Process

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-description
```

### 2. Make Your Changes

- Write clean, readable code
- Add tests for new functionality
- Update documentation if needed
- Ensure all tests pass

### 3. Commit Your Changes

```bash
git add .
git commit -m "feat: add amazing new feature"
```

### 4. Push to Your Fork

```bash
git push origin feature/your-feature-name
```

### 5. Open a Pull Request

1. Go to the [Flutter MCP repository](https://github.com/yourusername/flutter-mcp)
2. Click "Compare & pull request"
3. Fill out the PR template:
   - Describe what changes you made
   - Link any related issues
   - Include screenshots if relevant
   - Check all the boxes in the checklist

### 6. Code Review

- Be patient and respectful during review
- Respond to feedback constructively
- Make requested changes promptly
- Ask questions if something isn't clear

## 🐛 Reporting Bugs

Found a bug? Help us fix it by providing detailed information:

1. **Search existing issues** first to avoid duplicates
2. **Use the bug report template** when creating an issue
3. **Include**:
   - Flutter MCP version (`flutter-mcp --version`)
   - Python version (`python --version`)
   - OS and version
   - Steps to reproduce
   - Expected behavior
   - Actual behavior
   - Error messages/logs
   - Screenshots if applicable

## 💡 Requesting Features

Have an idea? We'd love to hear it!

1. **Check existing issues and discussions** first
2. **Use the feature request template**
3. **Explain**:
   - The problem you're trying to solve
   - Your proposed solution
   - Alternative solutions you've considered
   - How it benefits other users

## 🤝 Community Guidelines

### Our Code of Conduct

We're committed to providing a welcoming and inclusive environment. By participating, you agree to:

- **Be respectful** - Treat everyone with respect
- **Be constructive** - Provide helpful feedback
- **Be inclusive** - Welcome newcomers and help them get started
- **Be patient** - Remember that everyone is volunteering their time
- **Be professional** - Keep discussions focused and productive

### Getting Help

- 💬 **Discord**: Join our [Flutter MCP Discord](https://discord.gg/flutter-mcp)
- 🤔 **Discussions**: Ask questions in [GitHub Discussions](https://github.com/yourusername/flutter-mcp/discussions)
- 📧 **Email**: Reach out to maintainers@flutter-mcp.dev

## 🏆 Recognition

We believe in recognizing our contributors! 

### All Contributors

We use the [All Contributors](https://allcontributors.org/) specification to recognize everyone who helps make Flutter MCP better. Contributors are automatically added to our README.

### Types of Contributions We Recognize

- 💻 Code
- 📖 Documentation
- 🎨 Design
- 💡 Ideas & Planning
- 🧪 Testing
- 🐛 Bug Reports
- 👀 Code Reviews
- 📢 Evangelism
- 🌍 Translation
- 💬 Answering Questions
- 🚧 Maintenance
- 🔧 Tools
- 📦 Packaging

## 📚 Additional Resources

- [Development Guide](DEVELOPMENT.md) - Detailed development setup
- [Architecture Overview](docs/ARCHITECTURE.md) - How Flutter MCP works
- [API Reference](docs/API.md) - Server API documentation
- [Testing Guide](docs/TESTING.md) - How to write effective tests

## 🎯 Current Priorities

Check our [Project Board](https://github.com/yourusername/flutter-mcp/projects) for current priorities. Good first issues are labeled with [`good first issue`](https://github.com/yourusername/flutter-mcp/labels/good%20first%20issue).

### Quick Wins for New Contributors

- Fix typos or improve documentation clarity
- Add missing tests for existing functionality
- Improve error messages
- Add code examples to documentation
- Help triage issues

## 🚢 Release Process

We use semantic versioning and release regularly:

- **Patch releases** (x.x.1) - Bug fixes, documentation updates
- **Minor releases** (x.1.0) - New features, non-breaking changes
- **Major releases** (1.0.0) - Breaking changes (rare)

Releases are automated through GitHub Actions when maintainers tag a new version.

---

<p align="center">
  <strong>Ready to contribute?</strong>
  <br><br>
  Remember: no contribution is too small! Whether you're fixing a typo or adding a major feature, you're helping make AI + Flutter development better for everyone.
  <br><br>
  <strong>Thank you for being awesome! 🎉</strong>
  <br><br>
  Made with ❤️ by the Flutter MCP community
</p>