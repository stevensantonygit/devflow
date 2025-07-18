# DevFlow CLI

A comprehensive development workflow manager that helps developers track coding sessions, manage project templates, and analyze productivity patterns - all from the terminal.

## Features

- **Time Tracking**: Intelligent session tracking with automatic project detection
- **Project Templates**: Create and manage reusable project scaffolds
- **Productivity Analytics**: Visualize your coding patterns and habits
- **Goal Setting**: Set and track daily/weekly coding goals
- **Activity Heatmap**: GitHub-style contribution calendar in your terminal
- **Cross-Platform**: Works on Linux, macOS, and Windows
- **Self-Contained**: No external dependencies required

## Quick Start

```bash
# Clone the repository
git clone https://github.com/stevensantonygit/devflow-cli
cd devflow-cli

# Run the application
./devflow

# Or with Python
py devflow.py
```

## Commands

- `devflow start [project]` - Start a coding session
- `devflow stop` - Stop current session
- `devflow status` - Show current session info
- `devflow stats` - View productivity analytics
- `devflow template create <name>` - Create a new project template
- `devflow template use <name> <path>` - Use a template for new project
- `devflow goals set <hours>` - Set daily coding goal
- `devflow heatmap` - Show activity heatmap
- `devflow export` - Export data to various formats

## Setup Instructions

1. Ensure Python 3.6+ is installed
2. No additional dependencies required - uses only Python standard library
3. Make the script executable: `chmod +x devflow`
4. Optionally add to PATH for global access

## Browser Gallery

This project includes a `palms.json` configuration for running in the browser gallery. The web interface provides a demo of the key features.

## License

MIT License - see LICENSE file for details
