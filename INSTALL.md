# DevFlow CLI - Installation and Setup Guide

## Quick Installation

### Option 1: Direct Download
```bash
# Clone the repository
git clone https://github.com/stevensantonygit/devflow-cli
cd devflow-cli

# Make executable (Unix systems)
chmod +x devflow

# Test installation
./devflow
```

### Option 2: Manual Setup
```bash
# Download the main script
wget https://raw.githubusercontent.com/stevensantonygit/devflow-cli/main/devflow.py

# Run directly
python3 devflow.py
```

## System Requirements

- **Python**: 3.6 or higher
- **Operating System**: Linux, macOS, or Windows
- **Storage**: ~50KB for application, ~1MB for data storage
- **Dependencies**: None (uses Python standard library only)

## Platform-Specific Setup

### Linux/macOS
```bash
# Make script executable
chmod +x devflow

# Optional: Add to PATH for global access
sudo cp devflow /usr/local/bin/
sudo cp devflow.py /usr/local/bin/

# Verify installation
devflow --help
```

### Windows
```cmd
# Run with Python
python devflow.py

# Or create a batch file for easier access
echo @echo off > devflow.bat
echo python "%~dp0devflow.py" %* >> devflow.bat
```

## First Run

1. **Start your first session**:
   ```bash
   ./devflow start "My Project"
   ```

2. **Check session status**:
   ```bash
   ./devflow status
   ```

3. **Stop and view stats**:
   ```bash
   ./devflow stop
   ./devflow stats
   ```

## Configuration

DevFlow CLI stores all data in `~/.devflow/` directory:
- `devflow.db` - SQLite database with all session data
- Configuration is automatic, no setup required

## Troubleshooting

### Common Issues

**"Permission denied" error**:
```bash
chmod +x devflow
```

**"Python not found"**:
- Ensure Python 3.6+ is installed
- Try `python3` instead of `python`

**Database errors**:
- Check write permissions in home directory
- Remove `~/.devflow/devflow.db` to reset

### Uninstallation

To completely remove DevFlow CLI:
```bash
# Remove application files
rm -rf devflow-cli/

# Remove user data (optional)
rm -rf ~/.devflow/
```

## Advanced Usage

### Git Integration
DevFlow automatically detects Git repositories and tracks:
- Files changed during sessions
- Lines added/removed
- Commit statistics

### Template System
Create reusable project templates:
```bash
# In your project directory
./devflow template create my-template

# Use template elsewhere
./devflow template use my-template /path/to/new-project
```

### Data Export
Export your productivity data:
```bash
# Export to JSON
./devflow export json

# Export to CSV
./devflow export csv
```

### Goal Tracking
Set and track daily coding goals:
```bash
# Set 4-hour daily goal
./devflow goals set 4

# View progress in stats
./devflow stats
```

## Browser Gallery Integration

This project includes `palms.json` for the TerminalCraft browser gallery. The configuration allows the project to run in a web environment, demonstrating key features without requiring local installation.

## Development

### Running Tests
```bash
python -m unittest tests/test_devflow.py
```

### Code Structure
- `devflow.py` - Main application
- `devflow` - Unix executable wrapper
- `palms.json` - Browser gallery configuration
- `tests/` - Unit tests
- `demo.sh` / `demo.bat` - Demo scripts

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

MIT License - see LICENSE file for details
