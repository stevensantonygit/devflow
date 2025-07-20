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
- **Habit Tracking**: Build and maintain coding habits with weekly targets
- **Milestone System**: Set and track project completion milestones
- **Time Block Scheduling**: Plan focused work sessions in advance
- **Focus Analytics**: Deep analysis of concentration patterns and consistency
- **Daily Review**: Comprehensive end-of-day productivity summary
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
- `devflow focus` - Focus and consistency analytics
- `devflow review` - Daily productivity review

### Habit & Goal Tracking
- `devflow habits create NAME` - Create a new coding habit
- `devflow habits complete NAME` - Mark habit as completed for today
- `devflow habits status` - Show habit completion progress
- `devflow milestones create NAME HOURS` - Create project milestone
- `devflow milestones show` - Show milestone progress

### Time Management
- `devflow schedule plan TYPE DATETIME DURATION` - Schedule focused time blocks
- `devflow schedule show` - Show upcoming scheduled blocks

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

## New Advanced Features

### Habit Tracking System
Build sustainable coding practices with our habit tracking system:

```bash
# Create coding habits with weekly targets
devflow habits create "Daily Commit" --description "Make at least one commit per day" --frequency 7
devflow habits create "Code Review" --frequency 3

# Mark habits as completed
devflow habits complete "Daily Commit" --notes "Fixed bug in authentication"

# Check habit progress
devflow habits status
```

### Project Milestones
Set and track significant project goals:

```bash
# Create milestones with hour targets
devflow milestones create "MVP Release" 100 --description "Complete minimum viable product"
devflow milestones create "Beta Testing" 50

# View milestone progress (auto-updates based on coding time)
devflow milestones show
```

### Time Block Scheduling
Plan focused work sessions in advance:

```bash
# Schedule focused coding blocks
devflow schedule plan "Deep Focus" "2024-12-20 09:00" 120 --notes "Work on authentication system"
devflow schedule plan "Code Review" "2024-12-20 14:00" 60

# View upcoming schedule
devflow schedule show
```

### Focus Analytics
Get deep insights into your concentration patterns:

```bash
# Analyze focus quality and consistency
devflow focus

# Daily productivity summary
devflow review
```

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