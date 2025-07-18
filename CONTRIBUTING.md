# Contributing to DevFlow CLI

Thank you for your interest in contributing to DevFlow CLI! This document provides guidelines for contributing to the project.

## Getting Started

1. Fork the repository
2. Clone your fork locally
3. Create a new branch for your feature or bugfix
4. Make your changes
5. Test your changes thoroughly
6. Submit a pull request

## Development Setup

```bash
# Clone the repository
git clone https://github.com/stevensantonygit/devflow-cli
cd devflow-cli

# No additional setup needed - uses Python standard library only
# Run tests
python -m unittest tests/test_devflow.py

# Test the application
py devflow.py --help
```

## Code Style

- Follow PEP 8 Python style guidelines
- Use meaningful variable and function names
- Add docstrings to functions and classes
- Keep functions focused and small
- Add comments for complex logic

## Testing

- Add unit tests for new functionality
- Ensure all existing tests pass
- Test on both Windows and Unix systems
- Manual testing of CLI commands

## Submitting Changes

1. Ensure your code follows the style guidelines
2. Add tests for new features
3. Update documentation if needed
4. Make sure all tests pass
5. Create a clear pull request description

## Bug Reports

When reporting bugs, please include:
- Your operating system and Python version
- Steps to reproduce the issue
- Expected vs actual behavior
- Any error messages

## Feature Requests

For new features:
- Describe the use case clearly
- Explain how it fits with existing functionality
- Consider backward compatibility

## Questions

For questions about usage or development, please:
- Check the README and documentation first
- Search existing issues
- Create a new issue with the "question" label

Thank you for contributing!
