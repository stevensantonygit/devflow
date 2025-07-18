#!/bin/bash

# DevFlow CLI Demo Script
# Demonstrates key features of the application

echo "DevFlow CLI Demo - Development Workflow Manager"
echo "=================================================="
echo

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is required to run DevFlow CLI"
    exit 1
fi

echo "Python 3 found"
echo

# Make script executable
chmod +x devflow 2>/dev/null || echo "Running on Windows, skipping chmod"

echo "Starting demo..."
echo

# Show help
echo "Available commands:"
python3 devflow.py
echo

# Start a demo session
echo "Starting coding session for 'demo-project'..."
python3 devflow.py start demo-project
echo

# Show status
echo "Checking session status..."
python3 devflow.py status
echo

# Simulate some work
echo "Simulating 3 seconds of coding..."
sleep 3
echo

# Stop session
echo "Stopping session..."
python3 devflow.py stop
echo

# Show stats
echo "Showing productivity stats..."
python3 devflow.py stats
echo

# Set a goal
echo "Setting daily goal to 4 hours..."
python3 devflow.py goals set 4
echo

# Show heatmap
echo "Showing activity heatmap..."
python3 devflow.py heatmap --weeks 4
echo

# Create a template
echo "Creating a demo template..."
mkdir -p demo-template
cd demo-template
echo "# Demo Project" > README.md
echo "print('Hello, DevFlow!')" > main.py
echo '{"name": "demo", "version": "1.0.0"}' > package.json
python3 ../devflow.py template create demo-template --description "A demo project template"
cd ..
rm -rf demo-template
echo

# Export data
echo "Exporting session data..."
python3 devflow.py export json
echo

echo "Demo completed! DevFlow CLI is ready to boost your productivity."
echo
echo "Try these commands:"
echo "   ./devflow start                 # Start tracking your work"
echo "   ./devflow stats                 # View your coding patterns"
echo "   ./devflow template create name  # Save project as template"
echo "   ./devflow heatmap              # See your activity calendar"
echo
echo "Features:"
echo "   Self-contained (no external dependencies)"
echo "   Cross-platform (Linux, macOS, Windows)"
echo "   Intelligent project detection"
echo "   Git integration for code statistics"
echo "   Goal tracking and progress visualization"
echo "   Project template management"
echo "   Data export capabilities"
