# DevFlow CLI

A comprehensive development workflow manager that helps developers track coding sessions, manage project templates, and analyze productivity patterns - all from the terminal.

## Features

- **Time Tracking**: Intelligent session tracking with automatic project detection
- **Project Templates**: Create and manage reusable project scaffolds
- **Productivity Analytics**: Visualize your coding patterns and habits
- **Goal Setting**: Set and track daily/weekly coding goals
- **Activity Heatmap**: GitHub-style contribution calendar in your terminal
- **Achievement System**: Gamified coding with unlockable achievements
- **Streak Tracking**: Daily coding streak monitoring and motivation
- **Session Notes**: Add contextual notes to track accomplishments
- **Session Tagging**: Organize sessions with custom tags
- **Advanced Insights**: Hourly productivity distribution analysis
- **Project Leaderboard**: Compare productivity across different projects
- **Productivity Scoring**: Intelligent scoring based on coding frequency
- **Weekly Summaries**: Comprehensive project performance reports
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

### Session Management
- `devflow start [project]` - Start a coding session
- `devflow stop` - Stop current session and trigger achievements
- `devflow status` - Show current session info

### Analytics & Insights
- `devflow stats` - View productivity analytics
- `devflow summary [--project NAME]` - Show weekly project summary
- `devflow insights` - Advanced analytics with hourly distribution
- `devflow score [--days N]` - Show productivity score
- `devflow heatmap` - Show activity heatmap
- `devflow leaderboard` - Project productivity rankings

### Productivity Tools
- `devflow achievements` - View unlocked achievements
- `devflow streak` - Show current coding streak
- `devflow notes add <text>` - Add note to current session
- `devflow notes list` - View recent session notes
- `devflow tags add <tag>` - Tag current session

### Project Management
- `devflow template create <name>` - Create a new project template
- `devflow template use <name> <path>` - Use a template for new project
- `devflow goals set <hours>` - Set daily coding goal
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

## Achievement System

Unlock achievements for coding milestones:
- **First Steps**: Complete your first coding session
- **Marathon Coder**: Code for 4+ hours in a single session
- **Week Warrior**: Maintain a 7-day coding streak
- **Early Bird**: Start coding before 8 AM
- **Night Owl**: Code past 10 PM

## Advanced Analytics

- Hourly productivity distribution charts
- Project leaderboards with time comparisons
- Productivity scoring based on consistency
- Weekly summaries with comprehensive metrics
- Streak tracking for motivation

---

*DevFlow CLI: Because every commit counts!*