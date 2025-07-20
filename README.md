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
- **Music Integration**: Track music preferences and correlate with productivity patterns
- **Music Analytics**: Recommendations based on coding performance
- **Voice Commands**: Hands-free session management and voice-to-text transcription
- **Voice Analytics**: Track and analyze voice command usage patterns
- **Session Snapshots**: Visual project progress tracking with automatic milestones
- **Progress Charts**: See your project growth over time with file/line counts
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

### Music Integration & Analytics
- `devflow music log "TYPE" [--artist NAME] [--track NAME] [--genre GENRE] [--mood MOOD] [--energy N]` - Log currently playing music
- `devflow music stop` - Stop current music tracking
- `devflow music status` - Show currently tracked music
- `devflow music rate "TYPE" PRODUCTIVITY FOCUS` - Rate music's effect on productivity (1-10 scale)
- `devflow music analytics` - View music productivity correlations
- `devflow music recommend` - Get music recommendations

### Voice Commands & Transcription
- `devflow voice enable [--sensitivity N] [--language LANG] [--wake-word WORD]` - Enable voice commands
- `devflow voice disable` - Disable voice commands
- `devflow voice status` - Show voice command settings and usage history
- `devflow voice interactive` - Start interactive voice command mode
- `devflow voice transcribe --to-notes [--text TEXT]` - Convert speech to session notes

### Session Snapshots & Progress Tracking
- `devflow snapshot [--milestone] [--notes TEXT]` - Capture current project state
- `devflow snapshots` - View all snapshots for current session
- `devflow progress [--days N]` - Show visual progress chart with file/line growth

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

### Music Integration System
Track and optimize your music choices for maximum productivity:

```bash
# Log music while coding (track what enhances your focus)
devflow music log "Lo-fi Hip Hop" --artist "ChilledCow" --genre "Electronic" --mood "calm" --energy 6
devflow music log "Classical Piano" --artist "Ludovico Einaudi" --mood "focused" --energy 8

# Rate music's impact on your productivity
devflow music rate "Lo-fi Hip Hop" 9 8  # productivity=9, focus=8 (out of 10)
devflow music rate "Classical Piano" 8 9

# Get recommendations based on your productivity data
devflow music recommend

# Analyze which music types boost your coding performance
devflow music analytics

# Check what's currently playing
devflow music status

# Stop tracking current music
devflow music stop
```

**Music Analytics Features:**
- **Productivity Correlation**: See which music types lead to longer, more productive sessions
- **Mood & Energy Tracking**: Correlate music energy levels with coding performance
- **Personalized Recommendations**: Suggests music based on your historical productivity data
- **Session Integration**: Music data automatically tied to coding sessions for comprehensive analytics
- **Genre Analysis**: Discover which musical genres enhance your focus and creativity

### Voice Command System
Experience hands-free productivity management with advanced voice integration:

```bash
# Enable voice commands with custom settings
devflow voice enable --sensitivity 0.8 --language en-US --wake-word "devflow"

# Start interactive voice command mode
devflow voice interactive

# Then use natural voice commands:
# "DevFlow start session my new project"
# "DevFlow log music jazz"
# "DevFlow status"
# "DevFlow note completed authentication module"
# "DevFlow stop session"

# Convert speech to session notes
devflow voice transcribe --to-notes

# Check voice command settings and history
devflow voice status

# Disable voice commands
devflow voice disable
```

**Voice Command Features:**
- **Natural Language Processing**: Understand conversational commands like "Hey DevFlow, start a session"
- **Hands-Free Operation**: Manage sessions without touching the keyboard
- **Voice-to-Text Transcription**: Convert speech directly to session notes
- **Customizable Wake Words**: Set personalized activation phrases
- **Multi-Language Support**: Configure for different languages and accents
- **Command History**: Track and analyze voice command usage patterns
- **Interactive Mode**: Real-time voice command processing and feedback

### Session Snapshots & Visual Progress
Experience visual project evolution with automated progress tracking:

```bash
# Capture project state at any moment
devflow snapshot --notes "Completed authentication module"

# Mark important milestones in your development
devflow snapshot --milestone --notes "MVP Release Ready!"

# View all snapshots for current session
devflow snapshots

# See visual progress chart with file/line growth over time
devflow progress --days 7
```

**Session Snapshot Features:**
- **Automatic Snapshots**: Captures project state when sessions end
- **Milestone Tracking**: Mark significant development achievements
- **File & Directory Analysis**: Track project growth over time
- **Visual Progress Charts**: See coding activity with file/line count evolution
- **Project Structure Insights**: Monitor how your codebase evolves
- **Historical Comparison**: Compare project state across different time periods
- **Smart File Detection**: Automatically identifies and counts code files vs other files

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
- **Music-Productivity Correlation Analysis**: Discover which music enhances your coding flow
- **Music Recommendations**: Get personalized suggestions based on your productivity patterns
- **Mood & Energy Correlation**: Track how music energy levels affect your coding performance
- **Voice Command Analytics**: Analyze voice command usage patterns and effectiveness
- **Speech-to-Text Integration**: Convert natural speech to actionable session data
- **Hands-Free Productivity**: Manage entire coding sessions without keyboard interaction
- **Visual Progress Tracking**: See project evolution with file/line count growth over time
- **Automated Project Snapshots**: Capture development milestones and compare project states
- **Smart Project Analysis**: Automatic detection of code files, directories, and project structure changes

---

*DevFlow CLI: Because every commit counts!*