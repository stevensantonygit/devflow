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
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS habits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                habit_name TEXT NOT NULL,
                description TEXT,
                target_frequency INTEGER DEFAULT 1,
                created_date TEXT NOT NULL,
                active BOOLEAN DEFAULT 1
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS habit_completions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                habit_id INTEGER,
                completion_date TEXT NOT NULL,
                notes TEXT,
                FOREIGN KEY(habit_id) REFERENCES habits(id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS milestones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_name TEXT NOT NULL,
                milestone_name TEXT NOT NULL,
                description TEXT,
                target_hours INTEGER,
                completed BOOLEAN DEFAULT 0,
                completed_date TEXT,
                created_date TEXT NOT NULL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS time_blocks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_name TEXT NOT NULL,
                block_type TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                planned_duration INTEGER,
                actual_duration INTEGER,
                completed BOOLEAN DEFAULT 0,
                notes TEXT
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

    def create_habit(self, habit_name, description, target_frequency):
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO habits (habit_name, description, target_frequency, created_date) VALUES (?, ?, ?, ?)',
            (habit_name, description, target_frequency, today)
        )
        conn.commit()
        conn.close()

    def complete_habit(self, habit_name, notes=''):
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT id FROM habits WHERE habit_name = ? AND active = 1', (habit_name,))
        habit = cursor.fetchone()
        
        if habit:
            cursor.execute(
                'INSERT OR IGNORE INTO habit_completions (habit_id, completion_date, notes) VALUES (?, ?, ?)',
                (habit[0], today, notes)
            )
            conn.commit()
        
        conn.close()
        return habit is not None

    def get_habit_status(self, days=7):
        end_date = datetime.datetime.now()
        start_date = end_date - datetime.timedelta(days=days)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT h.habit_name, h.target_frequency, h.description,
                   COUNT(hc.completion_date) as completions
            FROM habits h
            LEFT JOIN habit_completions hc ON h.id = hc.habit_id 
                AND hc.completion_date >= ?
            WHERE h.active = 1
            GROUP BY h.id, h.habit_name, h.target_frequency, h.description
        ''', (start_date.strftime('%Y-%m-%d'),))
        
        results = cursor.fetchall()
        conn.close()
        return results

    def create_milestone(self, project_name, milestone_name, description, target_hours):
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO milestones (project_name, milestone_name, description, target_hours, created_date) VALUES (?, ?, ?, ?, ?)',
            (project_name, milestone_name, description, target_hours, today)
        )
        conn.commit()
        conn.close()

    def check_milestone_progress(self, project_name):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT m.id, m.milestone_name, m.description, m.target_hours, m.completed,
                   COALESCE(SUM(s.duration), 0) / 60.0 as hours_completed
            FROM milestones m
            LEFT JOIN sessions s ON m.project_name = s.project_name AND m.created_date <= DATE(s.start_time)
            WHERE m.project_name = ? AND m.completed = 0
            GROUP BY m.id, m.milestone_name, m.description, m.target_hours, m.completed
        ''', (project_name,))
        
        milestones = cursor.fetchall()
        
        # Auto-complete milestones that have reached their target
        for milestone in milestones:
            if milestone[5] >= milestone[3]:  # hours_completed >= target_hours
                today = datetime.datetime.now().strftime('%Y-%m-%d')
                cursor.execute(
                    'UPDATE milestones SET completed = 1, completed_date = ? WHERE id = ?',
                    (today, milestone[0])
                )
                print(f"🎯 Milestone completed: {milestone[1]}")
        
        conn.commit()
        conn.close()
        return milestones

    def schedule_time_block(self, project_name, block_type, start_time, duration_minutes, notes=''):
        start_dt = datetime.datetime.strptime(start_time, '%Y-%m-%d %H:%M')
        end_dt = start_dt + datetime.timedelta(minutes=duration_minutes)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            '''INSERT INTO time_blocks (project_name, block_type, start_time, end_time, 
               planned_duration, notes) VALUES (?, ?, ?, ?, ?, ?)''',
            (project_name, block_type, start_time, end_dt.strftime('%Y-%m-%d %H:%M'), 
             duration_minutes, notes)
        )
        conn.commit()
        conn.close()

    def get_upcoming_blocks(self, days=3):
        end_date = datetime.datetime.now() + datetime.timedelta(days=days)
        now = datetime.datetime.now()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            '''SELECT * FROM time_blocks 
               WHERE start_time >= ? AND start_time <= ? AND completed = 0
               ORDER BY start_time''',
            (now.strftime('%Y-%m-%d %H:%M'), end_date.strftime('%Y-%m-%d %H:%M'))
        )
        
        blocks = cursor.fetchall()
        conn.close()
        return blocks

    def get_focus_analytics(self, project_name, days=7):
        end_date = datetime.datetime.now()
        start_date = end_date - datetime.timedelta(days=days)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Session length analysis
        cursor.execute(
            '''SELECT duration FROM sessions 
               WHERE project_name = ? AND start_time >= ? AND end_time IS NOT NULL
               ORDER BY duration''',
            (project_name, start_date.strftime('%Y-%m-%d %H:%M:%S'))
        )
        durations = [row[0] for row in cursor.fetchall()]
        
        # Interruption analysis (sessions < 15 minutes)
        interruptions = len([d for d in durations if d < 900])
        
        # Flow state sessions (sessions > 90 minutes)
        flow_sessions = len([d for d in durations if d > 5400])
        
        conn.close()
        
        analytics = {
            'total_sessions': len(durations),
            'avg_session_length': sum(durations) / len(durations) if durations else 0,
            'interruption_rate': (interruptions / len(durations)) * 100 if durations else 0,
            'flow_sessions': flow_sessions,
            'consistency_score': self.calculate_consistency_score(durations)
        }
        
        return analytics

    def calculate_consistency_score(self, durations):
        if len(durations) < 2:
            return 0
        
        # Calculate coefficient of variation (lower is more consistent)
        mean_duration = sum(durations) / len(durations)
        variance = sum((d - mean_duration) ** 2 for d in durations) / len(durations)
        std_dev = variance ** 0.5
        cv = (std_dev / mean_duration) * 100 if mean_duration > 0 else 100
        
        # Convert to consistency score (0-100, higher is better)
        consistency = max(0, 100 - cv)
        return round(consistency, 1)

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

    def create_habit(self, habit_name, description='', target_frequency=1):
        self.db.create_habit(habit_name, description, target_frequency)
        print(f"Habit '{habit_name}' created successfully!")
        print(f"Target: {target_frequency} times per week")

    def complete_habit(self, habit_name, notes=''):
        if self.db.complete_habit(habit_name, notes):
            print(f"✅ Habit '{habit_name}' completed for today!")
        else:
            print(f"Habit '{habit_name}' not found or already completed today")

    def show_habits(self):
        habits = self.db.get_habit_status(7)
        
        print("\nHabit Tracker (Last 7 days):")
        print("=" * 40)
        
        if not habits:
            print("No habits created. Use 'devflow habits create' to start!")
            return
        
        for habit_name, target, description, completions in habits:
            completion_rate = (completions / target) * 100 if target > 0 else 0
            status = "✅" if completions >= target else "⏳"
            
            print(f"{status} {habit_name}")
            print(f"   {description}")
            print(f"   Progress: {completions}/{target} ({completion_rate:.1f}%)")
            
            # Visual progress bar
            progress_bars = int((completions / target) * 10) if target > 0 else 0
            progress_bar = "█" * progress_bars + "░" * (10 - progress_bars)
            print(f"   [{progress_bar}]")
            print()

    def create_milestone(self, project_name, milestone_name, description, target_hours):
        self.db.create_milestone(project_name, milestone_name, description, target_hours)
        print(f"Milestone '{milestone_name}' created for '{project_name}'")
        print(f"Target: {target_hours} hours")

    def show_milestones(self, project_name=None):
        if not project_name:
            project_name = self.get_current_project_name()
        
        milestones = self.db.check_milestone_progress(project_name)
        
        print(f"\nMilestones for '{project_name}':")
        print("=" * 40)
        
        if not milestones:
            print("No milestones set. Use 'devflow milestones create' to add one!")
            return
        
        for milestone in milestones:
            milestone_id, name, desc, target, completed, hours_done = milestone
            progress = (hours_done / target) * 100 if target > 0 else 0
            
            status = "✅" if completed else "🎯"
            print(f"{status} {name}")
            print(f"   {desc}")
            print(f"   Progress: {hours_done:.1f}h / {target}h ({progress:.1f}%)")
            
            # Progress visualization
            progress_bars = int(progress / 10)
            bar = "█" * progress_bars + "░" * (10 - progress_bars)
            print(f"   [{bar}] {progress:.1f}%")
            print()

    def schedule_block(self, project_name, block_type, start_time, duration, notes=''):
        if not project_name:
            project_name = self.get_current_project_name()
        
        self.db.schedule_time_block(project_name, block_type, start_time, duration, notes)
        print(f"Time block scheduled:")
        print(f"   Project: {project_name}")
        print(f"   Type: {block_type}")
        print(f"   Time: {start_time}")
        print(f"   Duration: {duration} minutes")

    def show_schedule(self):
        blocks = self.db.get_upcoming_blocks(3)
        
        print("\nUpcoming Time Blocks (Next 3 days):")
        print("=" * 45)
        
        if not blocks:
            print("No scheduled time blocks. Use 'devflow schedule' to plan your time!")
            return
        
        current_day = None
        for block in blocks:
            block_id, project, block_type, start_time, end_time, planned, actual, completed, notes = block
            
            start_dt = datetime.datetime.strptime(start_time, '%Y-%m-%d %H:%M')
            day = start_dt.strftime('%A, %B %d')
            
            if day != current_day:
                print(f"\n📅 {day}")
                print("-" * 30)
                current_day = day
            
            time_range = f"{start_dt.strftime('%H:%M')} - {datetime.datetime.strptime(end_time, '%Y-%m-%d %H:%M').strftime('%H:%M')}"
            print(f"   {time_range} | {project} ({block_type})")
            if notes:
                print(f"     📝 {notes}")

    def show_focus_report(self, project_name=None):
        if not project_name:
            project_name = self.get_current_project_name()
        
        analytics = self.db.get_focus_analytics(project_name, 7)
        
        print(f"\nFocus Analytics for '{project_name}' (Last 7 days):")
        print("=" * 50)
        
        if analytics['total_sessions'] == 0:
            print("No sessions found. Start coding to see your focus analytics!")
            return
        
        print(f"Total Sessions: {analytics['total_sessions']}")
        print(f"Average Session: {self.format_duration(analytics['avg_session_length'])}")
        print(f"Flow Sessions (90+ min): {analytics['flow_sessions']}")
        print(f"Interruption Rate: {analytics['interruption_rate']:.1f}%")
        print(f"Consistency Score: {analytics['consistency_score']}%")
        
        # Focus rating
        if analytics['consistency_score'] >= 80 and analytics['interruption_rate'] < 20:
            print("\n🔥 EXCELLENT FOCUS - You're in the zone!")
        elif analytics['consistency_score'] >= 60 and analytics['interruption_rate'] < 40:
            print("\n👍 GOOD FOCUS - Keep up the great work!")
        elif analytics['consistency_score'] >= 40:
            print("\n📈 IMPROVING FOCUS - Getting better!")
        else:
            print("\n💪 DEVELOPING FOCUS - Room for improvement!")

    def show_daily_review(self):
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        project_name = self.get_current_project_name()
        
        print(f"\nDaily Review - {today}")
        print("=" * 40)
        
        # Today's coding time
        today_sessions = self.db.execute_query(
            "SELECT SUM(duration), COUNT(*) FROM sessions WHERE DATE(start_time) = ? AND project_name = ? AND end_time IS NOT NULL",
            (today, project_name), fetch=True
        )[0]
        
        total_time = today_sessions[0] or 0
        session_count = today_sessions[1] or 0
        
        print(f"📊 Coding Time: {self.format_duration(total_time)}")
        print(f"📈 Sessions: {session_count}")
        
        # Habit completions
        habits = self.db.get_habit_status(1)
        completed_habits = sum(1 for h in habits if h[3] > 0)
        total_habits = len(habits)
        
        print(f"✅ Habits: {completed_habits}/{total_habits} completed")
        
        # Current streak
        streak = self.db.get_current_streak()
        print(f"🔥 Streak: {streak} days")
        
        # Productivity score
        score = self.db.get_productivity_score(project_name, 1)
        print(f"⭐ Today's Score: {score}%")
        
        # Weekly goals progress
        weekly_summary = self.db.get_weekly_summary(project_name)
        weekly_hours = weekly_summary['total_time'] / 60 if weekly_summary['total_time'] else 0
        print(f"\n📅 This Week: {weekly_hours:.1f}h total")

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
    
    # New powerful features
    habits_parser = subparsers.add_parser('habits', help='Habit tracking system')
    habits_subparsers = habits_parser.add_subparsers(dest='habits_action')
    
    create_habit_parser = habits_subparsers.add_parser('create', help='Create new habit')
    create_habit_parser.add_argument('name', help='Habit name')
    create_habit_parser.add_argument('--description', default='', help='Habit description')
    create_habit_parser.add_argument('--frequency', type=int, default=1, help='Target frequency per week')
    
    complete_habit_parser = habits_subparsers.add_parser('complete', help='Mark habit as completed today')
    complete_habit_parser.add_argument('name', help='Habit name')
    complete_habit_parser.add_argument('--notes', default='', help='Optional notes')
    
    habits_subparsers.add_parser('status', help='Show habit completion status')
    
    milestones_parser = subparsers.add_parser('milestones', help='Project milestone tracking')
    milestones_subparsers = milestones_parser.add_subparsers(dest='milestones_action')
    
    create_milestone_parser = milestones_subparsers.add_parser('create', help='Create project milestone')
    create_milestone_parser.add_argument('name', help='Milestone name')
    create_milestone_parser.add_argument('hours', type=int, help='Target hours to complete')
    create_milestone_parser.add_argument('--description', default='', help='Milestone description')
    create_milestone_parser.add_argument('--project', help='Project name (default: current)')
    
    milestones_subparsers.add_parser('show', help='Show milestone progress')
    
    schedule_parser = subparsers.add_parser('schedule', help='Time block scheduling')
    schedule_subparsers = schedule_parser.add_subparsers(dest='schedule_action')
    
    plan_parser = schedule_subparsers.add_parser('plan', help='Schedule a time block')
    plan_parser.add_argument('type', help='Block type (focus, review, break, etc.)')
    plan_parser.add_argument('datetime', help='Start time (YYYY-MM-DD HH:MM)')
    plan_parser.add_argument('duration', type=int, help='Duration in minutes')
    plan_parser.add_argument('--project', help='Project name (default: current)')
    plan_parser.add_argument('--notes', default='', help='Optional notes')
    
    schedule_subparsers.add_parser('show', help='Show upcoming time blocks')
    
    subparsers.add_parser('focus', help='Show focus and consistency analytics')
    subparsers.add_parser('review', help='Show daily review summary')
    
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
        print("  habits create      - Create new coding habit")
        print("  habits complete    - Mark habit as completed")
        print("  habits status      - Show habit progress")
        print("  milestones create  - Create project milestone")
        print("  milestones show    - Show milestone progress")
        print("  schedule plan      - Schedule focused time blocks")
        print("  schedule show      - Show upcoming schedule")
        print("  focus              - Show focus analytics")
        print("  review             - Show daily review")
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
    elif args.command == 'habits':
        if args.habits_action == 'create':
            cli.create_habit(args.name, args.description, args.frequency)
        elif args.habits_action == 'complete':
            cli.complete_habit(args.name, args.notes)
        elif args.habits_action == 'status':
            cli.show_habits()
    elif args.command == 'milestones':
        if args.milestones_action == 'create':
            project = args.project or cli.get_current_project_name()
            cli.create_milestone(project, args.name, args.description, args.hours)
        elif args.milestones_action == 'show':
            cli.show_milestones()
    elif args.command == 'schedule':
        if args.schedule_action == 'plan':
            project = args.project or cli.get_current_project_name()
            cli.schedule_block(project, args.type, args.datetime, args.duration, args.notes)
        elif args.schedule_action == 'show':
            cli.show_schedule()
    elif args.command == 'focus':
        cli.show_focus_report()
    elif args.command == 'review':
        cli.show_daily_review()

if __name__ == '__main__':
    main()