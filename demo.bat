@echo off
REM DevFlow CLI Demo Script for Windows
REM Demonstrates key features of the application

echo DevFlow CLI Demo - Development Workflow Manager
echo ==================================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python 3 is required to run DevFlow CLI
    pause
    exit /b 1
)

echo Python found
echo.

echo Starting demo...
echo.

REM Show help
echo Available commands:
python devflow.py
echo.

REM Start a demo session
echo Starting coding session for 'demo-project'...
python devflow.py start demo-project
echo.

REM Show status
echo Checking session status...
python devflow.py status
echo.

REM Simulate some work
echo Simulating 3 seconds of coding...
timeout /t 3 /nobreak >nul
echo.

REM Stop session
echo Stopping session...
python devflow.py stop
echo.

REM Show stats
echo Showing productivity stats...
python devflow.py stats
echo.

REM Set a goal
echo Setting daily goal to 4 hours...
python devflow.py goals set 4
echo.

REM Show heatmap
echo Showing activity heatmap...
python devflow.py heatmap --weeks 4
echo.

REM Export data
echo Exporting session data...
python devflow.py export json
echo.

echo Demo completed! DevFlow CLI is ready to boost your productivity.
echo.
echo Try these commands:
echo    python devflow.py start         # Start tracking your work
echo    python devflow.py stats         # View your coding patterns
echo    python devflow.py template create name  # Save project as template
echo    python devflow.py heatmap       # See your activity calendar
echo.
echo Features:
echo    Self-contained (no external dependencies)
echo    Cross-platform (Linux, macOS, Windows)
echo    Intelligent project detection
echo    Git integration for code statistics
echo    Goal tracking and progress visualization
echo    Project template management
echo    Data export capabilities

pause
