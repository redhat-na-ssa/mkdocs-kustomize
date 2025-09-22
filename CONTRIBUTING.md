# Contributing to MkDocs Kustomize Plugin

Thank you for considering contributing to the MkDocs Kustomize plugin! This document provides guidelines and instructions to help you contribute effectively.

## Development Setup

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/your-username/mkdocs-kustomize.git
   cd mkdocs-kustomize
   ```
3. Set up a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
4. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

## Running Tests

We use pytest for testing:

```bash
pytest tests/
```

For code coverage:

```bash
pytest --cov=mkdocs_kustomize tests/
```

## Code Style

We follow PEP 8 guidelines for Python code. Please ensure your code is formatted properly:

```bash
# Install tools
pip install black flake8 isort

# Format code
black mkdocs_kustomize tests
isort mkdocs_kustomize tests

# Check for issues
flake8 mkdocs_kustomize tests
```

## Making Changes

1. Create a new branch for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. Make your changes, adding tests as necessary
3. Ensure all tests pass
4. Update documentation if needed
5. Commit your changes with clear, descriptive commit messages

## Submitting a Pull Request

1. Push your changes to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```
2. Submit a pull request through the GitHub interface
3. In your pull request description, explain the changes and how they benefit the project

## Feature Requests and Bug Reports

Please use GitHub Issues to report bugs or request features. When reporting a bug, please include:

- A clear title and description
- Steps to reproduce the issue
- Expected and actual behavior
- Version information (Python, MkDocs, this plugin)
- Example code or files if possible

## Documentation

If you're changing functionality, please update the documentation to reflect your changes. Documentation lives in:

- README.md - For general usage and installation
- docs/ - For detailed documentation
- docstrings - For API documentation

## License

By contributing, you agree that your contributions will be licensed under the project's MIT License.