import os
import sys
import json
import time
import datetime
import argparse
import sqlite3
import hashlib
import subprocess
from pathlib import Path
from collections import defaultdict, Counter

class DevFlowDB:
    
    def __init__(self, db_path=None):
        if db_path is None:
            db_path = Path.home() / '.devflow' / 'devflow.db'
        
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        self.init_database()
    
    def init_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_name TEXT NOT NULL,
                project_path TEXT,
                start_time TIMESTAMP NOT NULL,
                end_time TIMESTAMP,
                duration INTEGER,
                files_changed INTEGER DEFAULT 0,
                lines_added INTEGER DEFAULT 0,
                lines_removed INTEGER DEFAULT 0,
                active BOOLEAN DEFAULT 1
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                files TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                goal_type TEXT NOT NULL,
                target_value INTEGER NOT NULL,
                current_value INTEGER DEFAULT 0,
                date TEXT NOT NULL,
                completed BOOLEAN DEFAULT 0
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS activity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                project_name TEXT NOT NULL,
                minutes_coded INTEGER NOT NULL,
                UNIQUE(date, project_name)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS streaks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                start_date TEXT NOT NULL,
                end_date TEXT,
                length INTEGER DEFAULT 1,
                active BOOLEAN DEFAULT 1
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                earned_date TEXT,
                project_name TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(session_id) REFERENCES sessions(id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                tag_name TEXT NOT NULL,
                FOREIGN KEY(session_id) REFERENCES sessions(id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def execute_query(self, query, params=None, fetch=False, fetch_one=False):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        result = None
        if fetch_one:
            result = cursor.fetchone()
        elif fetch:
            result = cursor.fetchall()
        else:
            result = cursor.lastrowid
        
        conn.commit()
        conn.close()
        return result

    def update_streak(self, project_name):
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM streaks WHERE active = 1 ORDER BY id DESC LIMIT 1')
        current_streak = cursor.fetchone()
        
        if current_streak:
            start_date, end_date, length = current_streak[1], current_streak[2], current_streak[3]
            
            cursor.execute('SELECT * FROM activity WHERE date = ? AND project_name = ?', (yesterday, project_name))
            if cursor.fetchone() or end_date == yesterday:
                cursor.execute('UPDATE streaks SET end_date = ?, length = ? WHERE id = ?', (today, length + 1, current_streak[0]))
            else:
                cursor.execute('UPDATE streaks SET active = 0 WHERE id = ?', (current_streak[0],))
                cursor.execute('INSERT INTO streaks (start_date, end_date, length) VALUES (?, ?, ?)', (today, today, 1))
        else:
            cursor.execute('INSERT INTO streaks (start_date, end_date, length) VALUES (?, ?, ?)', (today, today, 1))
        
        conn.commit()
        conn.close()

    def check_achievements(self, project_name, session_duration):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        achievements_to_award = []
        
        cursor.execute('SELECT COUNT(*) FROM sessions WHERE project_name = ?', (project_name,))
        session_count = cursor.fetchone()[0]
        if session_count == 1:
            achievements_to_award.append(("First Steps", "Completed your first coding session"))
        
        if session_duration >= 240:
            achievements_to_award.append(("Marathon Coder", "Coded for 4+ hours in a single session"))
        
        cursor.execute('SELECT MAX(length) FROM streaks')
        max_streak = cursor.fetchone()[0] or 0
        if max_streak >= 7:
            achievements_to_award.append(("Week Warrior", "Maintained a 7-day coding streak"))
        
        current_hour = datetime.datetime.now().hour
        if current_hour < 8:
            achievements_to_award.append(("Early Bird", "Started coding before 8 AM"))
        elif current_hour >= 22:
            achievements_to_award.append(("Night Owl", "Coded past 10 PM"))
        
        for name, description in achievements_to_award:
            cursor.execute('SELECT * FROM achievements WHERE name = ? AND project_name = ?', (name, project_name))
            if not cursor.fetchone():
                cursor.execute('INSERT INTO achievements (name, description, earned_date, project_name) VALUES (?, ?, ?, ?)',
                             (name, description, datetime.datetime.now().strftime('%Y-%m-%d'), project_name))
                print(f"Achievement unlocked: {name} - {description}")
        
        conn.commit()
        conn.close()

    def add_note(self, session_id, content):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO notes (session_id, content) VALUES (?, ?)', (session_id, content))
        conn.commit()
        conn.close()

    def get_notes(self, session_id=None):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if session_id:
            cursor.execute('SELECT * FROM notes WHERE session_id = ? ORDER BY created_at', (session_id,))
        else:
            cursor.execute('SELECT * FROM notes ORDER BY created_at DESC LIMIT 20')
        
        notes = cursor.fetchall()
        conn.close()
        return notes

    def get_achievements(self, project_name=None):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if project_name:
            cursor.execute('SELECT * FROM achievements WHERE project_name = ? ORDER BY earned_date DESC', (project_name,))
        else:
            cursor.execute('SELECT * FROM achievements ORDER BY earned_date DESC')
        
        achievements = cursor.fetchall()
        conn.close()
        return achievements

    def get_current_streak(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT length FROM streaks WHERE active = 1 ORDER BY id DESC LIMIT 1')
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else 0

    def get_productivity_score(self, project_name, days=7):
        end_date = datetime.datetime.now()
        start_date = end_date - datetime.timedelta(days=days)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            'SELECT duration FROM sessions WHERE project_name = ? AND start_time >= ? AND end_time IS NOT NULL',
            (project_name, start_date.strftime('%Y-%m-%d %H:%M:%S'))
        )
        sessions = cursor.fetchall()
        conn.close()
        
        total_minutes = sum(session[0] for session in sessions) if sessions else 0
        target_minutes = days * 60
        score = min(100, (total_minutes / target_minutes) * 100) if target_minutes > 0 else 0
        
        return round(score, 1)

    def get_weekly_summary(self, project_name):
        end_date = datetime.datetime.now()
        start_date = end_date - datetime.timedelta(days=7)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            'SELECT COUNT(*), SUM(duration), AVG(duration), SUM(files_changed), SUM(lines_added), SUM(lines_removed) FROM sessions WHERE project_name = ? AND start_time >= ? AND end_time IS NOT NULL',
            (project_name, start_date.strftime('%Y-%m-%d %H:%M:%S'))
        )
        result = cursor.fetchone()
        conn.close()
        
        return {
            'session_count': result[0] or 0,
            'total_time': result[1] or 0,
            'avg_session': result[2] or 0,
            'files_changed': result[3] or 0,
            'lines_added': result[4] or 0,
            'lines_removed': result[5] or 0,
            'productivity_score': self.get_productivity_score(project_name, 7),
            'current_streak': self.get_current_streak()
        }

    def add_session_tag(self, session_id, tag_name):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO tags (session_id, tag_name) VALUES (?, ?)', (session_id, tag_name))
        conn.commit()
        conn.close()

    def get_session_tags(self, session_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT tag_name FROM tags WHERE session_id = ?', (session_id,))
        tags = [row[0] for row in cursor.fetchall()]
        conn.close()
        return tags

    def get_project_leaderboard(self, days=30):
        end_date = datetime.datetime.now()
        start_date = end_date - datetime.timedelta(days=days)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            '''SELECT project_name, 
                      COUNT(*) as session_count,
                      SUM(duration) as total_minutes,
                      AVG(duration) as avg_session,
                      SUM(files_changed) as total_files,
                      SUM(lines_added) as total_lines_added
               FROM sessions 
               WHERE start_time >= ? AND end_time IS NOT NULL
               GROUP BY project_name 
               ORDER BY total_minutes DESC
               LIMIT 10''',
            (start_date.strftime('%Y-%m-%d %H:%M:%S'),)
        )
        results = cursor.fetchall()
        conn.close()
        return results

    def get_time_distribution(self, project_name, days=7):
        end_date = datetime.datetime.now()
        start_date = end_date - datetime.timedelta(days=days)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            '''SELECT strftime('%H', start_time) as hour, SUM(duration)
               FROM sessions 
               WHERE project_name = ? AND start_time >= ? AND end_time IS NOT NULL
               GROUP BY hour
               ORDER BY hour''',
            (project_name, start_date.strftime('%Y-%m-%d %H:%M:%S'))
        )
        results = cursor.fetchall()
        conn.close()
        
        hour_data = {}
        for hour, minutes in results:
            hour_data[int(hour)] = minutes
        
        return hour_data

class DevFlowCLI:
    
    def __init__(self):
        self.db = DevFlowDB()
        self.current_session = None
        self.load_current_session()
    
    def load_current_session(self):
        sessions = self.db.execute_query(
            "SELECT * FROM sessions WHERE active = 1 ORDER BY start_time DESC LIMIT 1",
            fetch=True
        )
        
        if sessions:
            session = sessions[0]
            self.current_session = {
                'id': session[0],
                'project_name': session[1],
                'project_path': session[2],
                'start_time': session[3]
            }
    
    def start_session(self, project_name=None, project_path=None):
        if self.current_session:
            print(f"WARNING: Session already active for '{self.current_session['project_name']}'")
            print(f"   Started: {self.current_session['start_time']}")
            return
        
        if not project_name:
            current_dir = os.getcwd()
            project_name = os.path.basename(current_dir)
            project_path = current_dir
        
        start_time = datetime.datetime.now().isoformat()
        
        session_id = self.db.execute_query(
            "INSERT INTO sessions (project_name, project_path, start_time) VALUES (?, ?, ?)",
            (project_name, project_path, start_time)
        )
        
        self.current_session = {
            'id': session_id,
            'project_name': project_name,
            'project_path': project_path,
            'start_time': start_time
        }
        
        print(f"Started session for '{project_name}'")
        print(f"   Time: {datetime.datetime.now().strftime('%H:%M:%S')}")
        if project_path:
            print(f"   Path: {project_path}")
    
    def stop_session(self):
        if not self.current_session:
            print("No active session found")
            return
        
        end_time = datetime.datetime.now().isoformat()
        start_dt = datetime.datetime.fromisoformat(self.current_session['start_time'])
        end_dt = datetime.datetime.fromisoformat(end_time)
        duration = int((end_dt - start_dt).total_seconds())
        
        files_changed, lines_added, lines_removed = self.get_git_stats()
        
        self.db.execute_query(
            """UPDATE sessions 
               SET end_time = ?, duration = ?, active = 0, 
                   files_changed = ?, lines_added = ?, lines_removed = ?
               WHERE id = ?""",
            (end_time, duration, files_changed, lines_added, lines_removed, self.current_session['id'])
        )
        
        date_str = start_dt.strftime('%Y-%m-%d')
        minutes = duration // 60
        
        self.db.execute_query(
            """INSERT OR REPLACE INTO activity (date, project_name, minutes_coded)
               VALUES (?, ?, COALESCE((SELECT minutes_coded FROM activity WHERE date = ? AND project_name = ?), 0) + ?)""",
            (date_str, self.current_session['project_name'], date_str, self.current_session['project_name'], minutes)
        )
        
        # Update streak and check achievements
        self.db.update_streak(self.current_session['project_name'])
        self.db.check_achievements(self.current_session['project_name'], minutes)
        
        print(f"Stopped session for '{self.current_session['project_name']}'")
        print(f"   Duration: {self.format_duration(duration)}")
        print(f"   Current streak: {self.db.get_current_streak()} days")
        if files_changed > 0:
            print(f"   Files changed: {files_changed}")
            print(f"   Lines: +{lines_added} -{lines_removed}")
        
        self.current_session = None
    
    def get_git_stats(self):
        if not self.current_session or not self.current_session.get('project_path'):
            return 0, 0, 0
        
        try:
            os.chdir(self.current_session['project_path'])
            
            start_time = self.current_session['start_time']
            result = subprocess.run(
                ['git', 'diff', '--stat', f'--since={start_time}'],
                capture_output=True, text=True
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if len(lines) > 1:
                    stats_line = lines[-1]
                    parts = stats_line.split(',')
                    files_changed = int(parts[0].strip().split()[0]) if parts else 0
                    
                    lines_added = 0
                    lines_removed = 0
                    for part in parts[1:]:
                        if 'insertion' in part:
                            lines_added = int(part.strip().split()[0])
                        elif 'deletion' in part:
                            lines_removed = int(part.strip().split()[0])
                    
                    return files_changed, lines_added, lines_removed
        except:
            pass
        
        return 0, 0, 0
    
    def show_status(self):
        if not self.current_session:
            print("No active session")
            return
        
        start_dt = datetime.datetime.fromisoformat(self.current_session['start_time'])
        current_duration = int((datetime.datetime.now() - start_dt).total_seconds())
        
        print(f"Active Session: {self.current_session['project_name']}")
        print(f"   Started: {start_dt.strftime('%H:%M:%S')}")
        print(f"   Duration: {self.format_duration(current_duration)}")
        if self.current_session.get('project_path'):
            print(f"   Path: {self.current_session['project_path']}")
    
    def show_stats(self, days=7):
        print(f"Productivity Stats (Last {days} days)")
        print("=" * 50)
        
        cutoff_date = (datetime.datetime.now() - datetime.timedelta(days=days)).strftime('%Y-%m-%d')
        
        sessions = self.db.execute_query(
            """SELECT project_name, SUM(duration), COUNT(*), SUM(files_changed), 
                      SUM(lines_added), SUM(lines_removed)
               FROM sessions 
               WHERE end_time IS NOT NULL AND DATE(start_time) >= ?
               GROUP BY project_name
               ORDER BY SUM(duration) DESC""",
            (cutoff_date,), fetch=True
        )
        
        total_time = 0
        total_sessions = 0
        
        print("\nTop Projects:")
        for i, (project, duration, count, files, added, removed) in enumerate(sessions[:5], 1):
            total_time += duration or 0
            total_sessions += count or 0
            print(f"  {i}. {project}")
            print(f"     Time: {self.format_duration(duration or 0)} ({count} sessions)")
            if files:
                print(f"     Changes: {files} files, +{added or 0}/-{removed or 0} lines")
        
        print(f"\nTotal Coding Time: {self.format_duration(total_time)}")
        print(f"Total Sessions: {total_sessions}")
        
        if total_sessions > 0:
            avg_session = total_time // total_sessions
            print(f"Average Session: {self.format_duration(avg_session)}")
        
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        today_minutes = self.db.execute_query(
            "SELECT SUM(minutes_coded) FROM activity WHERE date = ?",
            (today,), fetch=True
        )[0][0] or 0
        
        goals = self.db.execute_query(
            "SELECT target_value FROM goals WHERE goal_type = 'daily' AND date = ?",
            (today,), fetch=True
        )
        
        if goals:
            target_minutes = goals[0][0]
            progress = min(100, (today_minutes / target_minutes) * 100)
            print(f"\nToday's Goal: {today_minutes//60}h {today_minutes%60}m / {target_minutes//60}h {target_minutes%60}m ({progress:.1f}%)")
            print(f"   {'█' * int(progress//5)}{'░' * (20-int(progress//5))} {progress:.1f}%")
    
    def create_template(self, name, description=""):
        current_dir = Path.cwd()
        
        template_files = {}
        
        for file_path in current_dir.rglob('*'):
            if file_path.is_file() and not self.should_ignore_file(file_path):
                relative_path = file_path.relative_to(current_dir)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    template_files[str(relative_path)] = content
                except:
                    template_files[str(relative_path)] = f"BINARY_FILE:{file_path.suffix}"
        
        files_json = json.dumps(template_files)
        
        try:
            self.db.execute_query(
                "INSERT INTO templates (name, description, files) VALUES (?, ?, ?)",
                (name, description, files_json)
            )
            print(f"Template '{name}' created successfully!")
            print(f"   Files included: {len(template_files)}")
        except sqlite3.IntegrityError:
            print(f"Template '{name}' already exists")
    
    def use_template(self, name, target_path):
        templates = self.db.execute_query(
            "SELECT files FROM templates WHERE name = ?",
            (name,), fetch=True
        )
        
        if not templates:
            print(f"Template '{name}' not found")
            return
        
        target_dir = Path(target_path)
        target_dir.mkdir(parents=True, exist_ok=True)
        
        template_files = json.loads(templates[0][0])
        
        created_count = 0
        for file_path, content in template_files.items():
            full_path = target_dir / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            if content.startswith("BINARY_FILE:"):
                print(f"Skipping binary file: {file_path}")
                continue
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            created_count += 1
        
        print(f"Template '{name}' applied to {target_path}")
        print(f"   Created {created_count} files")
    
    def set_goal(self, goal_type, target_value):
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        
        if goal_type == 'daily':
            target_minutes = int(float(target_value) * 60)
        else:
            target_minutes = target_value
        
        self.db.execute_query(
            "INSERT OR REPLACE INTO goals (goal_type, target_value, date) VALUES (?, ?, ?)",
            (goal_type, target_minutes, today)
        )
        
        print(f"{goal_type.title()} goal set: {target_value}{'h' if goal_type == 'daily' else ''}")
    
    def show_heatmap(self, weeks=12):
        end_date = datetime.datetime.now()
        start_date = end_date - datetime.timedelta(weeks=weeks)
        
        activity = self.db.execute_query(
            "SELECT date, SUM(minutes_coded) FROM activity WHERE date >= ? GROUP BY date",
            (start_date.strftime('%Y-%m-%d'),), fetch=True
        )
        
        activity_dict = {date: minutes for date, minutes in activity}
        
        print(f"Activity Heatmap (Last {weeks} weeks)")
        print("=" * 60)
        
        current_date = start_date
        week_days = []
        
        print("    ", end="")
        month_positions = []
        for i in range(weeks):
            week_start = start_date + datetime.timedelta(weeks=i)
            if i == 0 or week_start.month != (week_start - datetime.timedelta(days=7)).month:
                month_positions.append((i * 3, week_start.strftime('%b')))
        
        for pos, month in month_positions:
            print(f"{month:>3}", end="   " if pos < weeks * 3 - 6 else "")
        print()
        
        day_labels = ['   ', 'Mon', '   ', 'Wed', '   ', 'Fri', '   ']
        for label in day_labels:
            print(f"{label:>3}", end="")
            for week in range(weeks):
                current_date = start_date + datetime.timedelta(weeks=week, days=['   ', 'Mon', '   ', 'Wed', '   ', 'Fri', '   '].index(label))
                if current_date <= end_date:
                    date_str = current_date.strftime('%Y-%m-%d')
                    minutes = activity_dict.get(date_str, 0)
                    intensity = self.get_intensity_char(minutes)
                    print(f" {intensity} ", end="")
                else:
                    print("   ", end="")
            print()
        
        print("\nLegend: ░ No activity  ▒ Low  ▓ Medium  █ High")
    
    def get_intensity_char(self, minutes):
        if minutes == 0:
            return '░'
        elif minutes < 60:
            return '▒'
        elif minutes < 180:
            return '▓'
        else:
            return '█'
    
    def should_ignore_file(self, file_path):
        ignore_patterns = [
            '.git', '__pycache__', '.vscode', '.idea', 'node_modules',
            '.env', '.DS_Store', '*.pyc', '*.log', '*.tmp'
        ]
        
        path_str = str(file_path)
        for pattern in ignore_patterns:
            if pattern in path_str or path_str.endswith(pattern.replace('*', '')):
                return True
        return False
    
    def format_duration(self, seconds):
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            return f"{seconds//60}m {seconds%60}s"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}h {minutes}m"
    
    def export_data(self, format_type='json'):
        export_data = {
            'sessions': [],
            'templates': [],
            'goals': [],
            'activity': []
        }
        
        sessions = self.db.execute_query(
            "SELECT * FROM sessions WHERE end_time IS NOT NULL ORDER BY start_time DESC",
            fetch=True
        )
        
        for session in sessions:
            export_data['sessions'].append({
                'project_name': session[1],
                'project_path': session[2],
                'start_time': session[3],
                'end_time': session[4],
                'duration': session[5],
                'files_changed': session[6],
                'lines_added': session[7],
                'lines_removed': session[8]
            })
        
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"devflow_export_{timestamp}.{format_type}"
        
        with open(filename, 'w') as f:
            if format_type == 'json':
                json.dump(export_data, f, indent=2)
            elif format_type == 'csv':
                f.write("project_name,start_time,end_time,duration,files_changed,lines_added,lines_removed\n")
                for session in export_data['sessions']:
                    f.write(f"{session['project_name']},{session['start_time']},{session['end_time']},{session['duration']},{session['files_changed']},{session['lines_added']},{session['lines_removed']}\n")
        
        print(f"Data exported to {filename}")

    def get_current_project_name(self):
        if self.current_session:
            return self.current_session['project_name']
        else:
            current_dir = os.getcwd()
            return os.path.basename(current_dir)

    def show_achievements(self):
        achievements = self.db.get_achievements()
        
        print(f"\nAll Achievements:")
        print("=" * 40)
        
        if not achievements:
            print("No achievements earned yet. Keep coding!")
            return
        
        current_project = None
        for achievement in achievements:
            if achievement[4] != current_project:
                current_project = achievement[4]
                print(f"\n{current_project}:")
                print("-" * len(current_project))
            
            print(f"🏆 {achievement[1]} - {achievement[2]}")
            print(f"   Earned: {achievement[3]}")
            print()

    def add_session_note(self, content):
        if not self.current_session:
            print("No active session. Start a session first with 'devflow start'")
            return
        
        self.db.add_note(self.current_session['id'], content)
        print(f"Note added to current session: {content}")

    def list_notes(self):
        notes = self.db.get_notes()
        
        print("\nRecent Session Notes:")
        print("=" * 30)
        
        if not notes:
            print("No notes found.")
            return
        
        for note in notes:
            print(f"Session {note[1]}: {note[2]}")
            print(f"  Created: {note[3]}")
            print()

    def show_weekly_summary(self, project_name=None):
        if not project_name:
            project_name = self.get_current_project_name()
        
        summary = self.db.get_weekly_summary(project_name)
        
        print(f"\nWeekly Summary for '{project_name}':")
        print("=" * 40)
        print(f"Sessions completed: {summary['session_count']}")
        print(f"Total time coded: {self.format_duration(summary['total_time'] * 60) if summary['total_time'] else '0m'}")
        if summary['avg_session']:
            print(f"Average session: {self.format_duration(summary['avg_session'] * 60)}")
        print(f"Files changed: {summary['files_changed']}")
        print(f"Lines added: {summary['lines_added']}")
        print(f"Lines removed: {summary['lines_removed']}")
        print(f"Productivity score: {summary['productivity_score']}%")
        print(f"Current streak: {summary['current_streak']} days")

    def show_streak(self):
        streak = self.db.get_current_streak()
        project_name = self.get_current_project_name()
        
        print(f"\nCoding Streak for '{project_name}':")
        print("=" * 30)
        if streak > 0:
            print(f"🔥 Current streak: {streak} days")
            if streak >= 7:
                print("Amazing! You're on a roll!")
            elif streak >= 3:
                print("Great job! Keep it up!")
        else:
            print("No active streak. Start coding to begin a new streak!")

    def show_productivity_score(self, days=7):
        project_name = self.get_current_project_name()
        score = self.db.get_productivity_score(project_name, days)
        
        print(f"\nProductivity Score ({days} days):")
        print("=" * 30)
        print(f"Project: {project_name}")
        print(f"Score: {score}%")
        
        if score >= 80:
            print("🌟 Excellent productivity!")
        elif score >= 60:
            print("👍 Good productivity!")
        elif score >= 40:
            print("📈 Room for improvement!")
        else:
            print("💪 Let's get coding!")

    def show_leaderboard(self):
        leaderboard = self.db.get_project_leaderboard(30)
        
        print("\nProject Leaderboard (Last 30 days):")
        print("=" * 45)
        
        if not leaderboard:
            print("No projects found. Start coding to see your projects here!")
            return
        
        for i, (project, sessions, total_min, avg_min, files, lines) in enumerate(leaderboard, 1):
            print(f"{i}. {project}")
            print(f"   Time: {self.format_duration(total_min * 60)} ({sessions} sessions)")
            print(f"   Avg: {self.format_duration(avg_min * 60)} | Files: {files} | Lines: +{lines}")
            print()

    def add_tag(self, tag_name):
        if not self.current_session:
            print("No active session. Start a session first with 'devflow start'")
            return
        
        self.db.add_session_tag(self.current_session['id'], tag_name)
        print(f"Added tag '{tag_name}' to current session")

    def show_insights(self):
        project_name = self.get_current_project_name()
        time_dist = self.db.get_time_distribution(project_name, 7)
        
        print(f"\nAdvanced Insights for '{project_name}':")
        print("=" * 50)
        
        # Time distribution analysis
        if time_dist:
            print("\nHourly Coding Distribution (Last 7 days):")
            print("-" * 40)
            
            # Find peak hours
            peak_hour = max(time_dist.items(), key=lambda x: x[1])
            total_minutes = sum(time_dist.values())
            
            for hour in range(24):
                minutes = time_dist.get(hour, 0)
                if minutes > 0:
                    percentage = (minutes / total_minutes) * 100
                    bar_length = int(percentage / 5)
                    bar = "█" * bar_length
                    print(f"{hour:2d}:00 │{bar:<20} {self.format_duration(minutes * 60)} ({percentage:.1f}%)")
            
            print(f"\n🔥 Peak productivity: {peak_hour[0]}:00 with {self.format_duration(peak_hour[1] * 60)}")
            
            # Productivity insights
            morning_time = sum(time_dist.get(h, 0) for h in range(6, 12))
            afternoon_time = sum(time_dist.get(h, 0) for h in range(12, 18))
            evening_time = sum(time_dist.get(h, 0) for h in range(18, 24))
            
            best_period = max([
                ("Morning", morning_time),
                ("Afternoon", afternoon_time), 
                ("Evening", evening_time)
            ], key=lambda x: x[1])
            
            print(f"🌟 Best period: {best_period[0]} ({self.format_duration(best_period[1] * 60)})")
        else:
            print("No coding activity in the last 7 days. Start a session to see insights!")

def main():
    parser = argparse.ArgumentParser(
        description='DevFlow CLI - Comprehensive development workflow manager',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  devflow start                    # Start session for current directory
  devflow start "My Project"       # Start named session
  devflow stop                     # Stop current session
  devflow status                   # Show session status
  devflow stats                    # Show productivity stats
  devflow template create webapp   # Create template from current dir
  devflow template use webapp ./new-project  # Use template
  devflow goals set 4              # Set 4-hour daily goal
  devflow heatmap                  # Show activity heatmap
  devflow export json              # Export data to JSON
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    start_parser = subparsers.add_parser('start', help='Start coding session')
    start_parser.add_argument('project', nargs='?', help='Project name')
    start_parser.add_argument('--path', help='Project path')
    
    subparsers.add_parser('stop', help='Stop coding session')
    
    subparsers.add_parser('status', help='Show session status')
    
    stats_parser = subparsers.add_parser('stats', help='Show productivity statistics')
    stats_parser.add_argument('--days', type=int, default=7, help='Number of days to include')
    
    template_parser = subparsers.add_parser('template', help='Template management')
    template_subparsers = template_parser.add_subparsers(dest='template_action')
    
    create_template_parser = template_subparsers.add_parser('create', help='Create template')
    create_template_parser.add_argument('name', help='Template name')
    create_template_parser.add_argument('--description', help='Template description')
    
    use_template_parser = template_subparsers.add_parser('use', help='Use template')
    use_template_parser.add_argument('name', help='Template name')
    use_template_parser.add_argument('path', help='Target path')
    
    goals_parser = subparsers.add_parser('goals', help='Goal management')
    goals_subparsers = goals_parser.add_subparsers(dest='goals_action')
    
    set_goal_parser = goals_subparsers.add_parser('set', help='Set goal')
    set_goal_parser.add_argument('hours', type=float, help='Daily goal in hours')
    
    heatmap_parser = subparsers.add_parser('heatmap', help='Show activity heatmap')
    heatmap_parser.add_argument('--weeks', type=int, default=12, help='Number of weeks to show')
    
    export_parser = subparsers.add_parser('export', help='Export data')
    export_parser.add_argument('format', choices=['json', 'csv'], default='json', nargs='?')
    
    # New commands for enhanced features
    subparsers.add_parser('achievements', help='Show earned achievements')
    
    notes_parser = subparsers.add_parser('notes', help='Session notes management')
    notes_subparsers = notes_parser.add_subparsers(dest='notes_action')
    add_note_parser = notes_subparsers.add_parser('add', help='Add note to current session')
    add_note_parser.add_argument('content', help='Note content')
    notes_subparsers.add_parser('list', help='List recent notes')
    
    summary_parser = subparsers.add_parser('summary', help='Show weekly summary')
    summary_parser.add_argument('--project', help='Project name (default: current project)')
    
    subparsers.add_parser('streak', help='Show current coding streak')
    
    score_parser = subparsers.add_parser('score', help='Show productivity score')
    score_parser.add_argument('--days', type=int, default=7, help='Number of days to calculate score for')
    
    # Advanced features
    subparsers.add_parser('leaderboard', help='Show project leaderboard')
    
    tags_parser = subparsers.add_parser('tags', help='Session tagging')
    tags_subparsers = tags_parser.add_subparsers(dest='tags_action')
    add_tag_parser = tags_subparsers.add_parser('add', help='Add tag to current session')
    add_tag_parser.add_argument('tag', help='Tag name')
    
    subparsers.add_parser('insights', help='Show advanced analytics and insights')
    
    if len(sys.argv) == 1:
        print("DevFlow CLI - Development Workflow Manager")
        print("=" * 50)
        print("Available commands:")
        print("  start [project]     - Start coding session")
        print("  stop               - Stop current session")
        print("  status             - Show session status")
        print("  stats              - Show productivity stats")
        print("  template create    - Create project template")
        print("  template use       - Use project template")
        print("  goals set <hours>  - Set daily goal")
        print("  heatmap            - Show activity heatmap")
        print("  export [format]    - Export data")
        print("  achievements       - Show earned achievements")
        print("  notes add <text>   - Add note to session")
        print("  notes list         - List recent notes")
        print("  summary [project]  - Show weekly summary")
        print("  streak             - Show coding streak")
        print("  score [days]       - Show productivity score")
        print("  leaderboard        - Show project leaderboard")
        print("  tags add <tag>     - Add tag to current session")
        print("  insights           - Show advanced analytics")
        print("\nUse 'devflow <command> --help' for detailed help")
        return
    
    args = parser.parse_args()
    cli = DevFlowCLI()
    
    if args.command == 'start':
        cli.start_session(args.project, getattr(args, 'path', None))
    elif args.command == 'stop':
        cli.stop_session()
    elif args.command == 'status':
        cli.show_status()
    elif args.command == 'stats':
        cli.show_stats(args.days)
    elif args.command == 'template':
        if args.template_action == 'create':
            cli.create_template(args.name, getattr(args, 'description', ''))
        elif args.template_action == 'use':
            cli.use_template(args.name, args.path)
    elif args.command == 'goals':
        if args.goals_action == 'set':
            cli.set_goal('daily', args.hours)
    elif args.command == 'heatmap':
        cli.show_heatmap(args.weeks)
    elif args.command == 'export':
        cli.export_data(args.format)
    elif args.command == 'achievements':
        cli.show_achievements()
    elif args.command == 'notes':
        if args.notes_action == 'add':
            cli.add_session_note(args.content)
        elif args.notes_action == 'list':
            cli.list_notes()
    elif args.command == 'summary':
        cli.show_weekly_summary(args.project)
    elif args.command == 'streak':
        cli.show_streak()
    elif args.command == 'score':
        cli.show_productivity_score(args.days)
    elif args.command == 'leaderboard':
        cli.show_leaderboard()
    elif args.command == 'tags':
        if args.tags_action == 'add':
            cli.add_tag(args.tag)
    elif args.command == 'insights':
        cli.show_insights()

if __name__ == '__main__':
    main()