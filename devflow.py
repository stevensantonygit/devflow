import os
import sys
import json
import time
import datetime
import argparse
import sqlite3
import hashlib
import subprocess
import threading
import re
import random
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
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS music_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                music_type TEXT NOT NULL,
                artist TEXT,
                track_name TEXT,
                genre TEXT,
                mood TEXT,
                energy_level INTEGER DEFAULT 5,
                start_time TIMESTAMP NOT NULL,
                end_time TIMESTAMP,
                FOREIGN KEY(session_id) REFERENCES sessions(id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS music_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                music_type TEXT NOT NULL,
                productivity_rating INTEGER DEFAULT 5,
                focus_rating INTEGER DEFAULT 5,
                usage_count INTEGER DEFAULT 1,
                last_used TEXT,
                notes TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS voice_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                enabled BOOLEAN DEFAULT 0,
                sensitivity REAL DEFAULT 0.7,
                language TEXT DEFAULT 'en-US',
                wake_word TEXT DEFAULT 'devflow',
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS voice_commands (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                command_text TEXT NOT NULL,
                interpreted_command TEXT NOT NULL,
                session_id INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                confidence REAL DEFAULT 0.0,
                FOREIGN KEY(session_id) REFERENCES sessions(id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS session_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                snapshot_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_files INTEGER DEFAULT 0,
                code_files INTEGER DEFAULT 0,
                total_lines INTEGER DEFAULT 0,
                directories INTEGER DEFAULT 0,
                file_types TEXT,
                project_structure TEXT,
                milestone_reached BOOLEAN DEFAULT 0,
                notes TEXT,
                FOREIGN KEY(session_id) REFERENCES sessions(id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS quick_ideas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_name TEXT NOT NULL,
                idea_text TEXT NOT NULL,
                category TEXT DEFAULT 'general',
                priority INTEGER DEFAULT 3,
                status TEXT DEFAULT 'open',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                session_id INTEGER,
                tags TEXT,
                FOREIGN KEY(session_id) REFERENCES sessions(id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS idea_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_name TEXT UNIQUE NOT NULL,
                description TEXT,
                color_code TEXT DEFAULT '#3498db',
                usage_count INTEGER DEFAULT 0
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS mood_tracking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                project_name TEXT NOT NULL,
                mood_score INTEGER NOT NULL CHECK(mood_score >= 1 AND mood_score <= 10),
                energy_level INTEGER NOT NULL CHECK(energy_level >= 1 AND energy_level <= 10),
                stress_level INTEGER NOT NULL CHECK(stress_level >= 1 AND stress_level <= 10),
                motivation_level INTEGER NOT NULL CHECK(motivation_level >= 1 AND motivation_level <= 10),
                focus_difficulty TEXT DEFAULT 'normal',
                notes TEXT DEFAULT '',
                logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions (id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS code_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                project_name TEXT NOT NULL,
                file_path TEXT NOT NULL,
                pattern_type TEXT NOT NULL,
                pattern_count INTEGER DEFAULT 1,
                severity TEXT DEFAULT 'info',
                description TEXT,
                detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions (id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pomodoro_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                project_name TEXT NOT NULL,
                pomodoro_type TEXT DEFAULT 'work',
                duration_minutes INTEGER DEFAULT 25,
                completed BOOLEAN DEFAULT FALSE,
                interruptions INTEGER DEFAULT 0,
                productivity_rating INTEGER CHECK(productivity_rating >= 1 AND productivity_rating <= 10),
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions (id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_quotes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quote_text TEXT NOT NULL,
                author TEXT DEFAULT 'Unknown',
                category TEXT DEFAULT 'motivation',
                shown_date DATE,
                user_rating INTEGER CHECK(user_rating >= 1 AND user_rating <= 5)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS break_suggestions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                project_name TEXT NOT NULL,
                break_type TEXT NOT NULL,
                reason TEXT NOT NULL,
                suggested_duration INTEGER DEFAULT 5,
                suggested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                taken BOOLEAN DEFAULT FALSE,
                effectiveness_rating INTEGER CHECK(effectiveness_rating >= 1 AND effectiveness_rating <= 5),
                FOREIGN KEY (session_id) REFERENCES sessions (id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS coding_style (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                project_name TEXT NOT NULL,
                file_extension TEXT,
                avg_line_length REAL DEFAULT 0.0,
                avg_function_length REAL DEFAULT 0.0,
                comment_ratio REAL DEFAULT 0.0,
                variable_naming_style TEXT DEFAULT 'mixed',
                indentation_style TEXT DEFAULT 'spaces',
                complexity_preference TEXT DEFAULT 'moderate',
                analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions (id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS project_comparisons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_a TEXT NOT NULL,
                project_b TEXT NOT NULL,
                comparison_type TEXT NOT NULL,
                metric_name TEXT NOT NULL,
                value_a REAL NOT NULL,
                value_b REAL NOT NULL,
                difference_percentage REAL DEFAULT 0.0,
                compared_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(project_a, project_b, comparison_type, metric_name)
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
        
        for milestone in milestones:
            if milestone[5] >= milestone[3]:
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
        
        cursor.execute(
            '''SELECT duration FROM sessions 
               WHERE project_name = ? AND start_time >= ? AND end_time IS NOT NULL
               ORDER BY duration''',
            (project_name, start_date.strftime('%Y-%m-%d %H:%M:%S'))
        )
        durations = [row[0] for row in cursor.fetchall()]
        
        interruptions = len([d for d in durations if d < 900])
        
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
        
        mean_duration = sum(durations) / len(durations)
        variance = sum((d - mean_duration) ** 2 for d in durations) / len(durations)
        std_dev = variance ** 0.5
        cv = (std_dev / mean_duration) * 100 if mean_duration > 0 else 100
        
        consistency = max(0, 100 - cv)
        return round(consistency, 1)

    def log_music(self, session_id, music_type, artist='', track_name='', genre='', mood='neutral', energy_level=5):
        start_time = datetime.datetime.now().isoformat()
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            '''INSERT INTO music_sessions (session_id, music_type, artist, track_name, genre, mood, energy_level, start_time)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
            (session_id, music_type, artist, track_name, genre, mood, energy_level, start_time)
        )
        
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        cursor.execute(
            '''INSERT OR REPLACE INTO music_preferences (music_type, usage_count, last_used)
               VALUES (?, COALESCE((SELECT usage_count FROM music_preferences WHERE music_type = ?), 0) + 1, ?)''',
            (music_type, music_type, today)
        )
        
        conn.commit()
        conn.close()
        return cursor.lastrowid

    def stop_music(self, music_session_id):
        end_time = datetime.datetime.now().isoformat()
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('UPDATE music_sessions SET end_time = ? WHERE id = ?', (end_time, music_session_id))
        conn.commit()
        conn.close()

    def rate_music_productivity(self, music_type, productivity_rating, focus_rating):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            '''UPDATE music_preferences 
               SET productivity_rating = ?, focus_rating = ?
               WHERE music_type = ?''',
            (productivity_rating, focus_rating, music_type)
        )
        conn.commit()
        conn.close()

    def get_music_analytics(self, days=30):
        end_date = datetime.datetime.now()
        start_date = end_date - datetime.timedelta(days=days)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT m.music_type, m.artist, m.genre, m.mood,
                   AVG(s.duration) as avg_session_duration,
                   COUNT(*) as session_count,
                   mp.productivity_rating, mp.focus_rating
            FROM music_sessions m
            JOIN sessions s ON m.session_id = s.id
            LEFT JOIN music_preferences mp ON m.music_type = mp.music_type
            WHERE m.start_time >= ?
            GROUP BY m.music_type, m.artist, m.genre, m.mood
            ORDER BY avg_session_duration DESC
        ''', (start_date.strftime('%Y-%m-%d %H:%M:%S'),))
        
        results = cursor.fetchall()
        conn.close()
        return results

    def get_music_recommendations(self, current_task_type='general'):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT music_type, productivity_rating, focus_rating, usage_count, last_used
            FROM music_preferences
            WHERE productivity_rating >= 7 OR focus_rating >= 7
            ORDER BY (productivity_rating + focus_rating) DESC, usage_count DESC
            LIMIT 5
        ''')
        
        recommendations = cursor.fetchall()
        conn.close()
        return recommendations

    def get_current_music_session(self, session_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            'SELECT * FROM music_sessions WHERE session_id = ? AND end_time IS NULL ORDER BY start_time DESC LIMIT 1',
            (session_id,)
        )
        result = cursor.fetchone()
        conn.close()
        return result

    def enable_voice_commands(self, enabled=True, sensitivity=0.7, language='en-US', wake_word='devflow'):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO voice_settings (id, enabled, sensitivity, language, wake_word, last_updated)
            VALUES (1, ?, ?, ?, ?, ?)
        ''', (enabled, sensitivity, language, wake_word, datetime.datetime.now().isoformat()))
        
        conn.commit()
        conn.close()

    def get_voice_settings(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM voice_settings WHERE id = 1')
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'enabled': bool(result[1]),
                'sensitivity': result[2],
                'language': result[3],
                'wake_word': result[4],
                'last_updated': result[5]
            }
        return None

    def log_voice_command(self, command_text, interpreted_command, session_id=None, confidence=0.0):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO voice_commands (command_text, interpreted_command, session_id, confidence) VALUES (?, ?, ?, ?)',
            (command_text, interpreted_command, session_id, confidence)
        )
        conn.commit()
        conn.close()

    def get_voice_command_history(self, limit=20):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            'SELECT * FROM voice_commands ORDER BY timestamp DESC LIMIT ?',
            (limit,)
        )
        results = cursor.fetchall()
        conn.close()
        return results

    def create_session_snapshot(self, session_id, project_path, milestone_reached=False, notes=''):
        """Create a snapshot of current project state"""
        import json
        
        if not project_path or not os.path.exists(project_path):
            return
        
        total_files = 0
        code_files = 0
        total_lines = 0
        directories = 0
        file_types = {}
        structure = {}
        
        code_extensions = {'.py', '.js', '.ts', '.java', '.cpp', '.c', '.cs', '.php', '.rb', '.go', '.rs', '.swift', '.kt'}
        
        try:
            for root, dirs, files in os.walk(project_path):
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'venv', 'env']]
                directories += len(dirs)
                
                for file in files:
                    if file.startswith('.'):
                        continue
                        
                    total_files += 1
                    file_path = os.path.join(root, file)
                    
                    ext = os.path.splitext(file)[1].lower()
                    file_types[ext] = file_types.get(ext, 0) + 1
                    
                    if ext in code_extensions:
                        code_files += 1
                        
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                total_lines += sum(1 for line in f if line.strip())
                        except:
                            pass
                    
                    rel_path = os.path.relpath(root, project_path)
                    if rel_path != '.':
                        top_dir = rel_path.split(os.sep)[0]
                        if top_dir not in structure:
                            structure[top_dir] = 0
                        structure[top_dir] += 1
        
        except Exception:
            pass
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            '''INSERT INTO session_snapshots 
               (session_id, total_files, code_files, total_lines, directories, file_types, project_structure, milestone_reached, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (session_id, total_files, code_files, total_lines, directories, 
             json.dumps(file_types), json.dumps(structure), milestone_reached, notes)
        )
        conn.commit()
        conn.close()
        return cursor.lastrowid

    def get_session_snapshots(self, session_id):
        """Get all snapshots for a session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            'SELECT * FROM session_snapshots WHERE session_id = ? ORDER BY snapshot_time',
            (session_id,)
        )
        results = cursor.fetchall()
        conn.close()
        return results

    def get_project_progress(self, project_name, days=30):
        """Get project progress over time"""
        end_date = datetime.datetime.now()
        start_date = end_date - datetime.timedelta(days=days)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            '''SELECT s.start_time, s.end_time, s.duration, 
                      ss.total_files, ss.code_files, ss.total_lines, ss.milestone_reached
               FROM sessions s
               LEFT JOIN session_snapshots ss ON s.id = ss.session_id
               WHERE s.project_name = ? AND s.start_time >= ? AND s.end_time IS NOT NULL
               ORDER BY s.start_time''',
            (project_name, start_date.strftime('%Y-%m-%d %H:%M:%S'))
        )
        results = cursor.fetchall()
        conn.close()
        return results

class VoiceManager:
    """Simple voice command manager using basic text patterns"""
    
    def __init__(self, db):
        self.db = db
        self.listening = False
        self.voice_thread = None
        
        self.command_patterns = {
            r'(?:hey\s+)?devflow\s+start(?:\s+session)?(?:\s+(.+))?': 'start_session',
            r'(?:hey\s+)?devflow\s+stop(?:\s+session)?': 'stop_session',
            r'(?:hey\s+)?devflow\s+status': 'show_status',
            r'(?:hey\s+)?devflow\s+log\s+music\s+(.+)': 'log_music',
            r'(?:hey\s+)?devflow\s+stop\s+music': 'stop_music',
            r'(?:hey\s+)?devflow\s+note\s+(.+)': 'add_note',
            r'(?:hey\s+)?devflow\s+stats': 'show_stats',
            r'(?:hey\s+)?devflow\s+achievements': 'show_achievements',
            r'(?:hey\s+)?devflow\s+help': 'show_help',
        }
    
    def enable_voice_listening(self):
        """Enable voice command listening (simulation)"""
        settings = self.db.get_voice_settings()
        if not settings:
            self.db.enable_voice_commands(True)
            settings = self.db.get_voice_settings()
        
        if settings['enabled']:
            print("🎤 Voice commands enabled!")
            print("Available voice commands:")
            print("  'DevFlow start session [project name]'")
            print("  'DevFlow stop session'")
            print("  'DevFlow status'")
            print("  'DevFlow log music [type]'")
            print("  'DevFlow stop music'")
            print("  'DevFlow note [your note]'")
            print("  'DevFlow stats'")
            print("  'DevFlow achievements'")
            print("\nSimulation mode: Type voice commands to test them!")
            return True
        return False
    
    def disable_voice_listening(self):
        """Disable voice command listening"""
        self.db.enable_voice_commands(False)
        self.listening = False
        print("🔇 Voice commands disabled")
    
    def parse_voice_command(self, text):
        """Parse voice command text and return action"""
        text = text.lower().strip()
        
        for pattern, action in self.command_patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                params = match.groups() if match.groups() else []
                return action, params, 0.8
        
        return None, [], 0.0
    
    def process_voice_input(self, text, cli_instance):
        """Process voice input and execute command"""
        action, params, confidence = self.parse_voice_command(text)
        
        if action:
            session_id = cli_instance.current_session['id'] if cli_instance.current_session else None
            self.db.log_voice_command(text, f"{action}:{params}", session_id, confidence)
            
            print(f"🎤 Voice command recognized: '{text}' (confidence: {confidence:.1f})")
            
            try:
                if action == 'start_session':
                    project_name = params[0] if params and params[0] else None
                    cli_instance.start_session(project_name)
                elif action == 'stop_session':
                    cli_instance.stop_session()
                elif action == 'show_status':
                    cli_instance.show_status()
                elif action == 'log_music':
                    music_type = params[0] if params else "Unknown"
                    cli_instance.log_music(music_type)
                elif action == 'stop_music':
                    cli_instance.stop_music()
                elif action == 'add_note':
                    note_content = params[0] if params else "Voice note"
                    cli_instance.add_session_note(note_content)
                elif action == 'show_stats':
                    cli_instance.show_stats()
                elif action == 'show_achievements':
                    cli_instance.show_achievements()
                elif action == 'show_help':
                    self.show_voice_help()
                else:
                    print(f"❓ Command '{action}' not implemented yet")
                    
            except Exception as e:
                print(f"❌ Error executing voice command: {e}")
        else:
            print(f"❓ Voice command not recognized: '{text}'")
            print("Try saying: 'DevFlow start session' or 'DevFlow status'")
    
    def show_voice_help(self):
        """Show voice commands help"""
        print("🎤 Voice Commands Help:")
        print("=" * 30)
        print("Session Management:")
        print("  'DevFlow start session [project name]'")
        print("  'DevFlow stop session'")
        print("  'DevFlow status'")
        print("\nMusic Integration:")
        print("  'DevFlow log music [type]'")
        print("  'DevFlow stop music'")
        print("\nProductivity:")
        print("  'DevFlow note [your note text]'")
        print("  'DevFlow stats'")
        print("  'DevFlow achievements'")
        print("\nTip: You can also say 'Hey DevFlow' before any command!")
    
    def voice_to_text_simulation(self, text):
        """Simulate voice-to-text conversion"""
        print(f"🎤 Converting speech to text: '{text}'")
        return text
    
    def start_interactive_mode(self, cli_instance):
        """Start interactive voice command mode"""
        print("🎤 Interactive Voice Mode Started!")
        print("Type voice commands (or 'quit' to exit):")
        print("Example: 'DevFlow start session my project'")
        
        while True:
            try:
                voice_input = input("\n🎤 Voice Input: ").strip()
                if voice_input.lower() in ['quit', 'exit', 'stop']:
                    print("👋 Exiting voice mode")
                    break
                elif voice_input:
                    self.process_voice_input(voice_input, cli_instance)
            except KeyboardInterrupt:
                print("\n👋 Exiting voice mode")
                break

class DevFlowCLI:
    
    def __init__(self):
        self.db = DevFlowDB()
        self.current_session = None
        self.voice_manager = VoiceManager(self.db)
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
        
        self.db.update_streak(self.current_session['project_name'])
        self.db.check_achievements(self.current_session['project_name'], minutes)
        
        project_path = self.current_session.get('project_path', os.getcwd())
        self.db.create_session_snapshot(
            self.current_session['id'], 
            project_path, 
            milestone_reached=False, 
            notes=f"Session ended - {self.format_duration(duration)}"
        )
        
        print(f"Stopped session for '{self.current_session['project_name']}'")
        print(f"   Duration: {self.format_duration(duration)}")
        print(f"   Current streak: {self.db.get_current_streak()} days")
        if files_changed > 0:
            print(f"   Files changed: {files_changed}")
            print(f"   Lines: +{lines_added} -{lines_removed}")
        print("📸 Session snapshot saved automatically")
        
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
        
        if time_dist:
            print("\nHourly Coding Distribution (Last 7 days):")
            print("-" * 40)
            
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
        
        today_sessions = self.db.execute_query(
            "SELECT SUM(duration), COUNT(*) FROM sessions WHERE DATE(start_time) = ? AND project_name = ? AND end_time IS NOT NULL",
            (today, project_name), fetch=True
        )[0]
        
        total_time = today_sessions[0] or 0
        session_count = today_sessions[1] or 0
        
        print(f"📊 Coding Time: {self.format_duration(total_time)}")
        print(f"📈 Sessions: {session_count}")
        
        habits = self.db.get_habit_status(1)
        completed_habits = sum(1 for h in habits if h[3] > 0)
        total_habits = len(habits)
        
        print(f"✅ Habits: {completed_habits}/{total_habits} completed")
        
        streak = self.db.get_current_streak()
        print(f"🔥 Streak: {streak} days")
        
        score = self.db.get_productivity_score(project_name, 1)
        print(f"⭐ Today's Score: {score}%")
        
        weekly_summary = self.db.get_weekly_summary(project_name)
        weekly_hours = weekly_summary['total_time'] / 60 if weekly_summary['total_time'] else 0
        print(f"\n📅 This Week: {weekly_hours:.1f}h total")

    def log_music(self, music_type, artist='', track_name='', genre='', mood='neutral', energy_level=5):
        if not self.current_session:
            print("No active session. Start a session first with 'devflow start'")
            return
        
        current_music = self.db.get_current_music_session(self.current_session['id'])
        if current_music:
            self.db.stop_music(current_music[0])
        
        music_id = self.db.log_music(
            self.current_session['id'], music_type, artist, track_name, genre, mood, energy_level
        )
        
        print(f"🎵 Music logged: {music_type}")
        if artist:
            print(f"   Artist: {artist}")
        if track_name:
            print(f"   Track: {track_name}")
        if genre:
            print(f"   Genre: {genre}")
        print(f"   Mood: {mood} | Energy: {energy_level}/10")
        
        return music_id

    def stop_music(self):
        if not self.current_session:
            print("No active session found")
            return
        
        current_music = self.db.get_current_music_session(self.current_session['id'])
        if not current_music:
            print("No active music session found")
            return
        
        self.db.stop_music(current_music[0])
        print(f"🎵 Stopped music: {current_music[2]}")

    def rate_music(self, music_type, productivity_rating, focus_rating):
        self.db.rate_music_productivity(music_type, productivity_rating, focus_rating)
        print(f"🎵 Rated '{music_type}':")
        print(f"   Productivity: {productivity_rating}/10")
        print(f"   Focus: {focus_rating}/10")

    def show_music_analytics(self):
        analytics = self.db.get_music_analytics(30)
        
        print("\n🎵 Music Productivity Analytics (Last 30 days):")
        print("=" * 55)
        
        if not analytics:
            print("No music data found. Use 'devflow music log' to start tracking!")
            return
        
        print("\nTop Music Types by Session Length:")
        print("-" * 40)
        
        for i, (music_type, artist, genre, mood, avg_duration, count, prod_rating, focus_rating) in enumerate(analytics[:10], 1):
            avg_duration = avg_duration or 0
            print(f"{i}. {music_type}")
            if artist:
                print(f"   Artist: {artist}")
            if genre:
                print(f"   Genre: {genre}")
            print(f"   Avg Session: {self.format_duration(avg_duration)} ({count} sessions)")
            if prod_rating and focus_rating:
                print(f"   Ratings: Productivity {prod_rating}/10, Focus {focus_rating}/10")
            print()

    def show_music_recommendations(self):
        recommendations = self.db.get_music_recommendations()
        
        print("\n🎵 Music Recommendations:")
        print("=" * 30)
        
        if not recommendations:
            print("No music data available yet. Start logging music to get recommendations!")
            return
        
        print("Based on your productivity patterns:")
        print("-" * 35)
        
        for i, (music_type, prod_rating, focus_rating, usage_count, last_used) in enumerate(recommendations, 1):
            overall_score = (prod_rating + focus_rating) / 2
            print(f"{i}. {music_type}")
            print(f"   Overall Score: {overall_score:.1f}/10")
            print(f"   Productivity: {prod_rating}/10 | Focus: {focus_rating}/10")
            print(f"   Used {usage_count} times | Last: {last_used}")
            print()

    def show_current_music(self):
        if not self.current_session:
            print("No active session")
            return
        
        current_music = self.db.get_current_music_session(self.current_session['id'])
        if not current_music:
            print("🎵 No music currently playing")
            return
        
        music_id, session_id, music_type, artist, track, genre, mood, energy, start_time, end_time = current_music
        
        print(f"🎵 Currently Playing: {music_type}")
        if artist:
            print(f"   Artist: {artist}")
        if track:
            print(f"   Track: {track}")
        if genre:
            print(f"   Genre: {genre}")
        print(f"   Mood: {mood} | Energy: {energy}/10")
        
        start_dt = datetime.datetime.fromisoformat(start_time)
        duration = int((datetime.datetime.now() - start_dt).total_seconds())
        print(f"   Playing for: {self.format_duration(duration)}")

    def take_snapshot(self, milestone=False, notes=''):
        """Take a snapshot of current project state"""
        if not self.current_session:
            print("No active session. Start a session first with 'devflow start'")
            return
        
        project_path = self.current_session.get('project_path')
        if not project_path:
            project_path = os.getcwd()
        
        snapshot_id = self.db.create_session_snapshot(
            self.current_session['id'], 
            project_path, 
            milestone, 
            notes
        )
        
        print("📸 Project snapshot captured!")
        if milestone:
            print("🎯 Milestone snapshot created")
        if notes:
            print(f"📝 Note: {notes}")
        
        return snapshot_id

    def show_snapshots(self):
        """Show snapshots for current session"""
        if not self.current_session:
            print("No active session")
            return
        
        snapshots = self.db.get_session_snapshots(self.current_session['id'])
        
        print(f"\n📸 Session Snapshots for '{self.current_session['project_name']}':")
        print("=" * 50)
        
        if not snapshots:
            print("No snapshots taken yet. Use 'devflow snapshot' to capture project state!")
            return
        
        import json
        
        for i, snapshot in enumerate(snapshots, 1):
            snap_id, session_id, snap_time, total_files, code_files, total_lines, directories, file_types_json, structure_json, milestone, notes = snapshot
            
            file_types = json.loads(file_types_json) if file_types_json else {}
            structure = json.loads(structure_json) if structure_json else {}
            
            print(f"\n{i}. Snapshot taken at {snap_time}")
            if milestone:
                print("   🎯 MILESTONE SNAPSHOT")
            if notes:
                print(f"   📝 {notes}")
            
            print(f"   📁 Files: {total_files} total, {code_files} code files")
            print(f"   📊 Lines of code: {total_lines:,}")
            print(f"   📂 Directories: {directories}")
            
            if file_types:
                top_types = sorted(file_types.items(), key=lambda x: x[1], reverse=True)[:3]
                types_str = ", ".join([f"{ext}({count})" for ext, count in top_types])
                print(f"   🔧 Top file types: {types_str}")

    def show_progress_chart(self, days=7):
        """Show visual progress chart for current project"""
        project_name = self.get_current_project_name()
        progress_data = self.db.get_project_progress(project_name, days)
        
        print(f"\n📈 Project Progress Chart: '{project_name}' (Last {days} days)")
        print("=" * 60)
        
        if not progress_data:
            print("No progress data available. Start coding to see your progress!")
            return
        
        daily_stats = {}
        for session_data in progress_data:
            start_time, end_time, duration, total_files, code_files, total_lines, milestone = session_data
            
            if not start_time:
                continue
                
            day = datetime.datetime.fromisoformat(start_time).strftime('%Y-%m-%d')
            
            if day not in daily_stats:
                daily_stats[day] = {
                    'coding_time': 0,
                    'max_files': 0,
                    'max_lines': 0,
                    'milestones': 0
                }
            
            daily_stats[day]['coding_time'] += (duration or 0)
            if total_files:
                daily_stats[day]['max_files'] = max(daily_stats[day]['max_files'], total_files)
            if total_lines:
                daily_stats[day]['max_lines'] = max(daily_stats[day]['max_lines'], total_lines)
            if milestone:
                daily_stats[day]['milestones'] += 1
        
        print("\nDaily Coding Activity:")
        print("-" * 30)
        
        sorted_days = sorted(daily_stats.keys())
        
        for day in sorted_days:
            stats = daily_stats[day]
            day_name = datetime.datetime.strptime(day, '%Y-%m-%d').strftime('%a %m/%d')
            
            hours = stats['coding_time'] / 3600
            bar_length = min(20, int(hours * 2))
            bar = "█" * bar_length + "░" * (20 - bar_length)
            
            milestone_indicator = " 🎯" if stats['milestones'] > 0 else ""
            
            print(f"{day_name} │{bar}│ {hours:.1f}h{milestone_indicator}")
            if stats['max_files'] > 0:
                print(f"        📁 {stats['max_files']} files, {stats['max_lines']:,} lines")
        
        total_hours = sum(stats['coding_time'] for stats in daily_stats.values()) / 3600
        total_milestones = sum(stats['milestones'] for stats in daily_stats.values())
        print(f"\n📊 Summary: {total_hours:.1f}h total, {total_milestones} milestones")

    def enable_voice_commands(self, sensitivity=0.7, language='en-US', wake_word='devflow'):
        """Enable voice commands with specified settings"""
        self.db.enable_voice_commands(True, sensitivity, language, wake_word)
        success = self.voice_manager.enable_voice_listening()
        
        if success:
            print(f"🎤 Voice commands enabled!")
            print(f"   Wake word: '{wake_word}'")
            print(f"   Language: {language}")
            print(f"   Sensitivity: {sensitivity}")
            print("\nYou can now use voice commands like:")
            print("  'DevFlow start session'")
            print("  'DevFlow log music jazz'")
            print("  'DevFlow status'")
        else:
            print("❌ Failed to enable voice commands")

    def disable_voice_commands(self):
        """Disable voice commands"""
        self.voice_manager.disable_voice_listening()

    def voice_interactive_mode(self):
        """Start interactive voice command mode"""
        settings = self.db.get_voice_settings()
        if not settings or not settings['enabled']:
            print("❌ Voice commands are not enabled.")
            print("Run 'devflow voice enable' first.")
            return
        
        self.voice_manager.start_interactive_mode(self)

    def voice_transcribe_to_notes(self, text=None):
        """Convert voice input to session notes"""
        if not self.current_session:
            print("No active session. Start a session first with 'devflow start'")
            return
        
        if not text:
            print("🎤 Voice Transcription Mode")
            print("Speak your note (or type it for simulation):")
            try:
                text = input("📝 Note: ").strip()
            except KeyboardInterrupt:
                print("\n❌ Transcription cancelled")
                return
        
        if text:
            processed_text = self.voice_manager.voice_to_text_simulation(text)
            
            self.add_session_note(processed_text)
            
            self.db.log_voice_command(
                f"Transcribe: {text}", 
                f"add_note:{processed_text}", 
                self.current_session['id'], 
                0.9
            )
            
            print("✅ Voice note added successfully!")
        else:
            print("❌ No text provided for transcription")

    def show_voice_status(self):
        """Show voice command settings and statistics"""
        settings = self.db.get_voice_settings()
        
        print("🎤 Voice Command Status:")
        print("=" * 30)
        
        if settings:
            status = "Enabled" if settings['enabled'] else "Disabled"
            print(f"Status: {status}")
            print(f"Wake word: '{settings['wake_word']}'")
            print(f"Language: {settings['language']}")
            print(f"Sensitivity: {settings['sensitivity']}")
            print(f"Last updated: {settings['last_updated']}")
        else:
            print("Status: Not configured")
            print("Run 'devflow voice enable' to set up voice commands")
        
        history = self.db.get_voice_command_history(5)
        if history:
            print("\nRecent Voice Commands:")
            print("-" * 20)
            for cmd in history:
                timestamp = cmd[4]
                command_text = cmd[1]
                confidence = cmd[5]
                print(f"  {timestamp}: '{command_text}' (confidence: {confidence:.1f})")
        else:
            print("\nNo voice commands used yet")

    def add_idea(self, idea_text, category='general', priority=3, tags=''):
        """Add a quick idea or TODO item"""
        project_name = self.get_current_project_name()
        session_id = None
        if self.current_session:
            session_id = self.current_session['id']
        
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO quick_ideas 
            (project_name, idea_text, category, priority, session_id, tags)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (project_name, idea_text, category, priority, session_id, tags))
        
        cursor.execute('''
            INSERT OR IGNORE INTO idea_categories (category_name) VALUES (?)
        ''', (category,))
        
        cursor.execute('''
            UPDATE idea_categories SET usage_count = usage_count + 1 
            WHERE category_name = ?
        ''', (category,))
        
        conn.commit()
        idea_id = cursor.lastrowid
        conn.close()
        
        print(f"💡 Idea added: {idea_text}")
        print(f"   Category: {category} | Priority: {priority}/5")
        if tags:
            print(f"   Tags: {tags}")
        
        return idea_id

    def list_ideas(self, category=None, status='open', limit=20):
        """List ideas with optional filtering"""
        project_name = self.get_current_project_name()
        
        query = '''
            SELECT id, idea_text, category, priority, status, 
                   created_at, tags, completed_at
            FROM quick_ideas 
            WHERE project_name = ? AND status = ?
        '''
        params = [project_name, status]
        
        if category:
            query += ' AND category = ?'
            params.append(category)
        
        query += ' ORDER BY priority DESC, created_at DESC LIMIT ?'
        params.append(limit)
        
        ideas = self.db.execute_query(query, params, fetch=True)
        
        if not ideas:
            print(f"💡 No {status} ideas found for '{project_name}'")
            if category:
                print(f"   Category filter: {category}")
            return
        
        print(f"\n💡 {status.title()} Ideas for '{project_name}':")
        print("=" * 50)
        
        for idea in ideas:
            idea_id, text, cat, priority, stat, created, tags, completed = idea
            
            priority_stars = "⭐" * priority
            
            print(f"\n#{idea_id} {priority_stars} [{cat}]")
            print(f"   {text}")
            if tags:
                print(f"   🏷️  {tags}")
            print(f"   📅 {created}")
            if completed:
                print(f"   ✅ Completed: {completed}")

    def complete_idea(self, idea_id):
        """Mark an idea as completed"""
        idea = self.db.execute_query('''
            SELECT idea_text, category FROM quick_ideas WHERE id = ?
        ''', (idea_id,), fetch_one=True)
        
        if not idea:
            print(f"❌ Idea #{idea_id} not found")
            return
        
        self.db.execute_query('''
            UPDATE quick_ideas 
            SET status = 'completed', completed_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (idea_id,))
        
        print(f"✅ Completed idea: {idea[0]}")
        print(f"   Category: {idea[1]}")

    def delete_idea(self, idea_id):
        """Delete an idea"""
        idea = self.db.execute_query('''
            SELECT idea_text FROM quick_ideas WHERE id = ?
        ''', (idea_id,), fetch_one=True)
        
        if not idea:
            print(f"❌ Idea #{idea_id} not found")
            return
        
        self.db.execute_query('DELETE FROM quick_ideas WHERE id = ?', (idea_id,))
        print(f"🗑️  Deleted idea: {idea[0]}")

    def show_idea_stats(self):
        """Show idea statistics and insights"""
        project_name = self.get_current_project_name()
        
        stats = self.db.execute_query('''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'open' THEN 1 ELSE 0 END) as open,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                AVG(priority) as avg_priority
            FROM quick_ideas 
            WHERE project_name = ?
        ''', (project_name,), fetch_one=True)
        
        categories = self.db.execute_query('''
            SELECT category, COUNT(*), AVG(priority)
            FROM quick_ideas 
            WHERE project_name = ?
            GROUP BY category
            ORDER BY COUNT(*) DESC
        ''', (project_name,), fetch=True)
        
        recent_count = self.db.execute_query('''
            SELECT COUNT(*) 
            FROM quick_ideas 
            WHERE project_name = ? AND DATE(created_at) >= DATE('now', '-7 days')
        ''', (project_name,), fetch_one=True)[0]
        
        print(f"\n💡 Ideas Dashboard for '{project_name}':")
        print("=" * 45)
        
        if stats[0] == 0:
            print("No ideas yet! Use 'devflow idea add' to capture your thoughts.")
            return
        
        total, open_count, completed, avg_priority = stats
        completion_rate = (completed / total * 100) if total > 0 else 0
        
        print(f"📊 Total Ideas: {total}")
        print(f"🔓 Open: {open_count}")
        print(f"✅ Completed: {completed} ({completion_rate:.1f}%)")
        print(f"⭐ Average Priority: {avg_priority:.1f}/5")
        print(f"📈 Added this week: {recent_count}")
        
        if categories:
            print(f"\n📂 Categories:")
            for cat, count, avg_pri in categories:
                print(f"   {cat}: {count} ideas (avg priority: {avg_pri:.1f})")
        
        if completion_rate >= 70:
            print(f"\n🎉 Great job! You're completing {completion_rate:.0f}% of your ideas!")
        elif completion_rate >= 40:
            print(f"\n👍 Good progress! {completion_rate:.0f}% completion rate.")
        else:
            print(f"\n💪 Keep working on those ideas! {completion_rate:.0f}% completed so far.")

    def search_ideas(self, search_term):
        """Search for ideas containing specific text"""
        project_name = self.get_current_project_name()
        
        results = self.db.execute_query('''
            SELECT id, idea_text, category, priority, status, created_at, tags
            FROM quick_ideas 
            WHERE project_name = ? 
            AND (idea_text LIKE ? OR tags LIKE ? OR category LIKE ?)
            ORDER BY priority DESC, created_at DESC
        ''', (project_name, f'%{search_term}%', f'%{search_term}%', f'%{search_term}%'), fetch=True)
        
        print(f"\n🔍 Search results for '{search_term}':")
        print("=" * 40)
        
        if not results:
            print("No matching ideas found.")
            return
        
        for idea in results:
            idea_id, text, cat, priority, status, created, tags = idea
            status_icon = "✅" if status == 'completed' else "🔓"
            priority_stars = "⭐" * priority
            
            print(f"\n{status_icon} #{idea_id} {priority_stars} [{cat}]")
            
            highlighted_text = text.replace(search_term, f"**{search_term}**")
            print(f"   {highlighted_text}")
            
            if tags and search_term.lower() in tags.lower():
                print(f"   🏷️  {tags}")
            print(f"   📅 {created}")

    def brainstorm_session(self, topic=""):
        """Start an interactive brainstorming session"""
        project_name = self.get_current_project_name()
        
        print(f"\n🧠 Brainstorming Session for '{project_name}'")
        if topic:
            print(f"   Topic: {topic}")
        print("=" * 50)
        print("Enter ideas one by one. Type 'done' to finish, 'help' for commands.")
        
        idea_count = 0
        
        while True:
            try:
                user_input = input(f"\n💡 Idea #{idea_count + 1}: ").strip()
                
                if user_input.lower() == 'done':
                    break
                elif user_input.lower() == 'help':
                    print("\nCommands:")
                    print("  done - Finish brainstorming")
                    print("  help - Show this help")
                    print("  Just type your idea to add it!")
                    continue
                elif not user_input:
                    continue
                
                category = 'brainstorm'
                if topic:
                    category = f'brainstorm-{topic.lower().replace(" ", "-")}'
                
                priority = 3
                if any(word in user_input.lower() for word in ['urgent', 'important', 'critical', 'asap']):
                    priority = 5
                elif any(word in user_input.lower() for word in ['maybe', 'later', 'someday']):
                    priority = 1
                elif any(word in user_input.lower() for word in ['should', 'need to', 'must']):
                    priority = 4
                
                self.add_idea(user_input, category, priority, f'brainstorm,{topic}' if topic else 'brainstorm')
                idea_count += 1
                
            except KeyboardInterrupt:
                print("\n\n🛑 Brainstorming session cancelled")
                break
        
        print(f"\n🎉 Brainstorming complete! Added {idea_count} ideas.")
        if idea_count > 0:
            print("Use 'devflow idea list' to review your ideas.")

    def log_mood(self, project_name, mood_score, energy_level, stress_level, motivation_level, focus_difficulty='normal', notes=''):
        """Log current mood and energy levels"""
        if not self.current_session:
            print("❌ No active session. Start a session first with 'devflow start'")
            return
            
        session_id = self.current_session['id']
        
        self.db.execute_query('''
            INSERT INTO mood_tracking 
            (session_id, project_name, mood_score, energy_level, stress_level, motivation_level, focus_difficulty, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (session_id, project_name, mood_score, energy_level, stress_level, motivation_level, focus_difficulty, notes))
        
        avg_mood = (mood_score + energy_level + (11 - stress_level) + motivation_level) / 4
        emoji = "😄" if avg_mood >= 8 else "😊" if avg_mood >= 6 else "😐" if avg_mood >= 4 else "😔"
        
        print(f"\n{emoji} Mood logged successfully!")
        print(f"📊 Overall wellness score: {avg_mood:.1f}/10")
        
        if avg_mood < 5:
            print("💡 Consider taking a break or doing some energizing activities!")
        elif avg_mood >= 8:
            print("🚀 Great energy! Perfect time for tackling challenging tasks!")

    def show_mood_trends(self, project_name=None, days=7):
        """Show mood trends over time"""
        query = '''
            SELECT DATE(logged_at) as date,
                   AVG(mood_score) as avg_mood,
                   AVG(energy_level) as avg_energy,
                   AVG(stress_level) as avg_stress,
                   AVG(motivation_level) as avg_motivation,
                   COUNT(*) as entries
            FROM mood_tracking
            WHERE logged_at >= datetime('now', '-{} days')
        '''.format(days)
        
        if project_name:
            query += " AND project_name = ?"
            params = (project_name,)
        else:
            params = ()
        
        query += " GROUP BY DATE(logged_at) ORDER BY date DESC"
        
        trends = self.db.execute_query(query, params, fetch=True)
        
        if not trends:
            print("📊 No mood data found for the specified period.")
            return
        
        print(f"\n📈 Mood Trends - Last {days} days")
        print("=" * 60)
        
        for trend in trends:
            date, mood, energy, stress, motivation, entries = trend
            wellness = (mood + energy + (11 - stress) + motivation) / 4
            emoji = "😄" if wellness >= 8 else "😊" if wellness >= 6 else "😐" if wellness >= 4 else "😔"
            
            print(f"{date}: {emoji} Wellness: {wellness:.1f} (M:{mood:.1f} E:{energy:.1f} S:{stress:.1f} Mo:{motivation:.1f}) [{entries} entries]")

    def detect_code_patterns(self, project_name, file_path=None):
        """Analyze code patterns and suggest improvements"""
        if not file_path or not os.path.exists(file_path):
            print("❌ Invalid file path provided")
            return
        
        if not self.current_session:
            print("❌ No active session. Start a session first with 'devflow start'")
            return
            
        session_id = self.current_session['id']
        patterns_found = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
                
            # Analyze various patterns
            line_lengths = [len(line) for line in lines if line.strip()]
            avg_line_length = sum(line_lengths) / len(line_lengths) if line_lengths else 0
            
            long_lines = sum(1 for length in line_lengths if length > 120)
            if long_lines > len(line_lengths) * 0.1:  # More than 10% long lines
                patterns_found.append(("long_lines", long_lines, "warning", f"Found {long_lines} lines longer than 120 characters"))
            
            # Check for deeply nested code
            max_indent = 0
            for line in lines:
                if line.strip():
                    indent = len(line) - len(line.lstrip())
                    max_indent = max(max_indent, indent)
            
            if max_indent > 32:  # More than 8 levels of indentation (assuming 4 spaces)
                patterns_found.append(("deep_nesting", max_indent // 4, "warning", f"Maximum nesting level: {max_indent // 4}"))
            
            # Check function length (simple heuristic)
            in_function = False
            function_lines = 0
            max_function_length = 0
            
            for line in lines:
                stripped = line.strip()
                if stripped.startswith('def ') or stripped.startswith('function '):
                    if in_function:
                        max_function_length = max(max_function_length, function_lines)
                    in_function = True
                    function_lines = 1
                elif in_function:
                    if stripped and not stripped.startswith(' ') and not stripped.startswith('\t'):
                        max_function_length = max(max_function_length, function_lines)
                        in_function = False
                        function_lines = 0
                    else:
                        function_lines += 1
            
            if max_function_length > 50:
                patterns_found.append(("long_function", max_function_length, "info", f"Longest function: {max_function_length} lines"))
            
            # Save patterns to database
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            for pattern_type, count, severity, description in patterns_found:
                cursor.execute('''
                    INSERT INTO code_patterns 
                    (session_id, project_name, file_path, pattern_type, pattern_count, severity, description)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (session_id, project_name, file_path, pattern_type, count, severity, description))
            
            conn.commit()
            conn.close()
            
            if patterns_found:
                print(f"\n🔍 Code Pattern Analysis for {os.path.basename(file_path)}")
                print("=" * 50)
                for _, _, severity, description in patterns_found:
                    icon = "⚠️ " if severity == "warning" else "ℹ️ "
                    print(f"{icon} {description}")
            else:
                print(f"\n✅ No significant patterns detected in {os.path.basename(file_path)}")
                
        except Exception as e:
            print(f"❌ Error analyzing file: {e}")

    def start_pomodoro(self, project_name, duration=25, pomodoro_type='work'):
        """Start a pomodoro timer session"""
        if not self.current_session:
            print("❌ No active session. Start a session first with 'devflow start'")
            return
            
        session_id = self.current_session['id']
        
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO pomodoro_sessions 
            (session_id, project_name, pomodoro_type, duration_minutes)
            VALUES (?, ?, ?, ?)
        ''', (session_id, project_name, pomodoro_type, duration))
        
        pomodoro_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        print(f"\n🍅 Starting {duration}-minute {pomodoro_type} pomodoro for {project_name}")
        print("Focus time begins now! Stay concentrated.")
        
        # Simple timer implementation
        try:
            start_time = time.time()
            while True:
                elapsed = int(time.time() - start_time)
                remaining = (duration * 60) - elapsed
                
                if remaining <= 0:
                    break
                
                mins, secs = divmod(remaining, 60)
                print(f"\r⏰ Time remaining: {mins:02d}:{secs:02d}", end="", flush=True)
                time.sleep(1)
                
            print(f"\n\n🎉 Pomodoro complete! Time for a break.")
            
            # Mark as completed
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE pomodoro_sessions 
                SET completed = TRUE, completed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (pomodoro_id,))
            conn.commit()
            
            # Ask for productivity rating
            while True:
                try:
                    rating = int(input("\n📊 Rate your productivity (1-10): "))
                    if 1 <= rating <= 10:
                        cursor.execute('''
                            UPDATE pomodoro_sessions 
                            SET productivity_rating = ?
                            WHERE id = ?
                        ''', (rating, pomodoro_id))
                        conn.commit()
                        break
                    else:
                        print("Please enter a number between 1 and 10.")
                except ValueError:
                    print("Please enter a valid number.")
            
            conn.close()
                    
        except KeyboardInterrupt:
            print(f"\n\n⏸️ Pomodoro interrupted after {elapsed // 60} minutes")
            interruptions = 1
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE pomodoro_sessions 
                SET interruptions = ?, completed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (interruptions, pomodoro_id))
            conn.commit()
            conn.close()

    def show_daily_quote(self):
        """Show an inspiring daily quote for developers"""
        quotes = [
            ("The best error message is the one that never shows up.", "Thomas Fuchs"),
            ("Code is like humor. When you have to explain it, it's bad.", "Cory House"),
            ("Programming isn't about what you know; it's about what you can figure out.", "Chris Pine"),
            ("The most important property of a program is whether it accomplishes the intention of its user.", "C.A.R. Hoare"),
            ("Simplicity is the ultimate sophistication.", "Leonardo da Vinci"),
            ("Any fool can write code that a computer can understand. Good programmers write code that humans can understand.", "Martin Fowler"),
            ("First, solve the problem. Then, write the code.", "John Johnson"),
            ("Experience is the name everyone gives to their mistakes.", "Oscar Wilde"),
            ("In order to be irreplaceable, one must always be different.", "Coco Chanel"),
            ("Java is to JavaScript what car is to Carpet.", "Chris Heilmann"),
            ("The best way to get a project done faster is to start sooner.", "Jim Highsmith"),
            ("Perfection is achieved not when there is nothing more to add, but rather when there is nothing more to take away.", "Antoine de Saint-Exupery"),
            ("Ruby is rubbish! PHP is phpantastic!", "Nikita Popov"),
            ("The computer was born to solve problems that did not exist before.", "Bill Gates"),
            ("Don't comment bad code—rewrite it.", "Brian Kernighan"),
            ("Debugging is twice as hard as writing the code in the first place.", "Brian Kernighan"),
            ("Walking on water and developing software from a specification are easy if both are frozen.", "Edward V. Berard"),
            ("It's not a bug—it's an undocumented feature.", "Anonymous"),
            ("A good programmer is someone who always looks both ways before crossing a one-way street.", "Doug Linder"),
            ("Programming is the art of telling another human being what one wants the computer to do.", "Donald Knuth")
        ]
        
        today = datetime.datetime.now().date()
        
        # Check if we already showed a quote today
        shown_quote = self.db.execute_query('''
            SELECT quote_text, author FROM daily_quotes 
            WHERE shown_date = ? AND user_rating IS NOT NULL
            ORDER BY RANDOM() LIMIT 1
        ''', (today,), fetch_one=True)
        
        if shown_quote:
            quote_text, author = shown_quote
        else:
            # Select a random quote
            quote_text, author = random.choice(quotes)
            
            # Save it to database
            self.db.execute_query('''
                INSERT OR REPLACE INTO daily_quotes (quote_text, author, shown_date)
                VALUES (?, ?, ?)
            ''', (quote_text, author, today))
        
        print(f"\n💡 Daily Developer Quote")
        print("=" * 50)
        print(f'"{quote_text}"')
        print(f"   — {author}")
        print("")

    def suggest_break(self, project_name, session_duration_minutes):
        """Suggest appropriate breaks based on coding duration and patterns"""
        if not self.current_session:
            print("❌ No active session. Start a session first with 'devflow start'")
            return
            
        session_id = self.current_session['id']
        
        break_suggestions = []
        
        if session_duration_minutes >= 120:  # 2+ hours
            break_suggestions.append(("long_break", "Take a longer break - go for a walk or have lunch", 30))
        elif session_duration_minutes >= 60:  # 1+ hour
            break_suggestions.append(("medium_break", "Take a medium break - stretch, hydrate, rest your eyes", 15))
        elif session_duration_minutes >= 25:  # 25+ minutes (pomodoro)
            break_suggestions.append(("short_break", "Take a short break - look away from screen, deep breaths", 5))
        
        # Check recent mood if available
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT stress_level, energy_level FROM mood_tracking 
            WHERE project_name = ? AND logged_at >= datetime('now', '-2 hours')
            ORDER BY logged_at DESC LIMIT 1
        ''', (project_name,))
        
        recent_mood = cursor.fetchone()
        conn.close()
        if recent_mood:
            stress, energy = recent_mood
            if stress >= 8:
                break_suggestions.append(("stress_break", "High stress detected - try meditation or calm music", 10))
            if energy <= 3:
                break_suggestions.append(("energy_break", "Low energy - have a healthy snack or do light exercise", 10))
        
        if break_suggestions:
            print(f"\n🧘 Break Suggestions for {project_name}")
            print("=" * 40)
            
            for break_type, reason, duration in break_suggestions:
                print(f"⏱️  {reason} ({duration} min)")
                
                # Save suggestion to database
                conn = sqlite3.connect(self.db.db_path)
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO break_suggestions 
                    (session_id, project_name, break_type, reason, suggested_duration)
                    VALUES (?, ?, ?, ?, ?)
                ''', (session_id, project_name, break_type, reason, duration))
            
            conn.commit()
            conn.close()
            
            choice = input("\nWould you like to take a break now? (y/N): ").lower()
            if choice == 'y':
                print("✨ Great choice! Take care of yourself.")
                return True
        
        return False

    def analyze_coding_style(self, project_name, file_path=None):
        """Analyze and learn user's coding style preferences"""
        if not file_path or not os.path.exists(file_path):
            print("❌ Invalid file path provided")
            return
        
        if not self.current_session:
            print("❌ No active session. Start a session first with 'devflow start'")
            return
            
        session_id = self.current_session['id']
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
            
            # Analyze style patterns
            non_empty_lines = [line for line in lines if line.strip()]
            if not non_empty_lines:
                return
            
            # Line length analysis
            line_lengths = [len(line) for line in non_empty_lines]
            avg_line_length = sum(line_lengths) / len(line_lengths)
            
            # Function length analysis (simple heuristic)
            function_lengths = []
            current_function_length = 0
            in_function = False
            
            for line in lines:
                stripped = line.strip()
                if any(stripped.startswith(prefix) for prefix in ['def ', 'function ', 'async def ']):
                    if in_function and current_function_length > 0:
                        function_lengths.append(current_function_length)
                    in_function = True
                    current_function_length = 1
                elif in_function:
                    if stripped and not line.startswith(' ') and not line.startswith('\t'):
                        function_lengths.append(current_function_length)
                        in_function = False
                        current_function_length = 0
                    else:
                        current_function_length += 1
            
            avg_function_length = sum(function_lengths) / len(function_lengths) if function_lengths else 0
            
            # Comment analysis
            comment_lines = sum(1 for line in lines if line.strip().startswith('#') or line.strip().startswith('//') or line.strip().startswith('*'))
            comment_ratio = comment_lines / len(non_empty_lines) if non_empty_lines else 0
            
            # Indentation analysis
            indent_chars = []
            for line in non_empty_lines:
                if len(line) > len(line.lstrip()):
                    leading = line[:len(line) - len(line.lstrip())]
                    if leading:
                        indent_chars.append(leading[0])
            
            indentation_style = "spaces" if indent_chars and indent_chars[0] == ' ' else "tabs" if indent_chars and indent_chars[0] == '\t' else "mixed"
            
            # Variable naming analysis (simple)
            import re
            variables = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', content)
            snake_case = sum(1 for var in variables if '_' in var and var.islower())
            camel_case = sum(1 for var in variables if any(c.isupper() for c in var[1:]) and '_' not in var)
            
            if snake_case > camel_case * 2:
                variable_naming_style = "snake_case"
            elif camel_case > snake_case * 2:
                variable_naming_style = "camelCase"
            else:
                variable_naming_style = "mixed"
            
            # Complexity preference
            complexity_indicators = content.count('if') + content.count('for') + content.count('while') + content.count('try')
            complexity_preference = "high" if complexity_indicators > len(non_empty_lines) * 0.3 else "low" if complexity_indicators < len(non_empty_lines) * 0.1 else "moderate"
            
            # Save analysis
            self.db.execute_query('''
                INSERT INTO coding_style 
                (session_id, project_name, file_extension, avg_line_length, avg_function_length, 
                 comment_ratio, variable_naming_style, indentation_style, complexity_preference)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (session_id, project_name, os.path.splitext(file_path)[1], avg_line_length, 
                  avg_function_length, comment_ratio, variable_naming_style, indentation_style, complexity_preference))
            
            print(f"\n📊 Coding Style Analysis for {os.path.basename(file_path)}")
            print("=" * 50)
            print(f"📏 Average line length: {avg_line_length:.1f} characters")
            print(f"🔧 Average function length: {avg_function_length:.1f} lines")
            print(f"💬 Comment ratio: {comment_ratio:.1%}")
            print(f"🔤 Variable naming: {variable_naming_style}")
            print(f"📐 Indentation: {indentation_style}")
            print(f"🧠 Complexity preference: {complexity_preference}")
            
        except Exception as e:
            print(f"❌ Error analyzing coding style: {e}")

    def compare_projects(self, project_a, project_b):
        """Compare productivity metrics between two projects"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        # Get session statistics for both projects
        projects_data = {}
        
        for project in [project_a, project_b]:
            cursor.execute('''
                SELECT 
                    COUNT(*) as session_count,
                    AVG(CAST((julianday(end_time) - julianday(start_time)) * 1440 AS REAL)) as avg_duration,
                    SUM(CAST((julianday(end_time) - julianday(start_time)) * 1440 AS REAL)) as total_duration,
                    COUNT(DISTINCT DATE(start_time)) as active_days
                FROM sessions 
                WHERE project_name = ? AND end_time IS NOT NULL
            ''', (project,))
            
            stats = cursor.fetchone()
            if stats[0] > 0:  # Has sessions
                projects_data[project] = {
                    'sessions': stats[0],
                    'avg_duration': stats[1] or 0,
                    'total_duration': stats[2] or 0,
                    'active_days': stats[3]
                }
            else:
                projects_data[project] = {
                    'sessions': 0,
                    'avg_duration': 0,
                    'total_duration': 0,
                    'active_days': 0
                }
        
        # Calculate comparisons and save to database
        comparisons = []
        
        for metric in ['sessions', 'avg_duration', 'total_duration', 'active_days']:
            value_a = projects_data[project_a][metric]
            value_b = projects_data[project_b][metric]
            
            if value_b > 0:
                diff_percentage = ((value_a - value_b) / value_b) * 100
            else:
                diff_percentage = 100 if value_a > 0 else 0
            
            comparisons.append((metric, value_a, value_b, diff_percentage))
            
            # Save to database
            cursor.execute('''
                INSERT OR REPLACE INTO project_comparisons 
                (project_a, project_b, comparison_type, metric_name, value_a, value_b, difference_percentage)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (project_a, project_b, 'productivity', metric, value_a, value_b, diff_percentage))
        
        conn.commit()
        conn.close()
        
        # Display comparison
        print(f"\n📊 Project Comparison: {project_a} vs {project_b}")
        print("=" * 60)
        
        for metric, value_a, value_b, diff_pct in comparisons:
            metric_names = {
                'sessions': 'Total Sessions',
                'avg_duration': 'Avg Session Duration (min)',
                'total_duration': 'Total Duration (min)',
                'active_days': 'Active Days'
            }
            
            name = metric_names[metric]
            arrow = "📈" if diff_pct > 0 else "📉" if diff_pct < 0 else "➡️"
            
            if metric == 'avg_duration':
                print(f"{name:25}: {value_a:6.1f} vs {value_b:6.1f} {arrow} {diff_pct:+.1f}%")
            else:
                print(f"{name:25}: {value_a:6.0f} vs {value_b:6.0f} {arrow} {diff_pct:+.1f}%")
        
        # Summary
        total_diff = sum(comp[3] for comp in comparisons) / len(comparisons)
        if total_diff > 10:
            print(f"\n🏆 {project_a} is performing better overall!")
        elif total_diff < -10:
            print(f"\n🏆 {project_b} is performing better overall!")
        else:
            print(f"\n🤝 Both projects have similar productivity levels!")

def main():
    parser = argparse.ArgumentParser(
        description='DevFlow CLI - Comprehensive development workflow manager',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  devflow start
  devflow start "My Project"
  devflow stop
  devflow status
  devflow stats
  devflow template create webapp
  devflow template use webapp ./new-project
  devflow goals set 4
  devflow heatmap
  devflow export json
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
    
    subparsers.add_parser('leaderboard', help='Show project leaderboard')
    
    tags_parser = subparsers.add_parser('tags', help='Session tagging')
    tags_subparsers = tags_parser.add_subparsers(dest='tags_action')
    add_tag_parser = tags_subparsers.add_parser('add', help='Add tag to current session')
    add_tag_parser.add_argument('tag', help='Tag name')
    
    subparsers.add_parser('insights', help='Show advanced analytics and insights')
    
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
    
    snapshot_parser = subparsers.add_parser('snapshot', help='Project snapshot and progress tracking')
    snapshot_parser.add_argument('--milestone', action='store_true', help='Mark this as a milestone snapshot')
    snapshot_parser.add_argument('--notes', default='', help='Add notes to the snapshot')
    
    subparsers.add_parser('snapshots', help='Show session snapshots')
    
    progress_parser = subparsers.add_parser('progress', help='Show visual progress chart')
    progress_parser.add_argument('--days', type=int, default=7, help='Number of days to show')
    
    music_parser = subparsers.add_parser('music', help='Music productivity tracking')
    music_subparsers = music_parser.add_subparsers(dest='music_action')
    
    log_music_parser = music_subparsers.add_parser('log', help='Log current music')
    log_music_parser.add_argument('type', help='Music type (e.g., "Lo-fi Hip Hop", "Classical", "Ambient")')
    log_music_parser.add_argument('--artist', default='', help='Artist name')
    log_music_parser.add_argument('--track', default='', help='Track name')
    log_music_parser.add_argument('--genre', default='', help='Music genre')
    log_music_parser.add_argument('--mood', default='neutral', choices=['energetic', 'calm', 'focused', 'creative', 'neutral'], help='Current mood')
    log_music_parser.add_argument('--energy', type=int, default=5, choices=range(1, 11), help='Energy level 1-10')
    
    music_subparsers.add_parser('stop', help='Stop current music session')
    music_subparsers.add_parser('status', help='Show current music status')
    
    rate_music_parser = music_subparsers.add_parser('rate', help='Rate music productivity impact')
    rate_music_parser.add_argument('type', help='Music type to rate')
    rate_music_parser.add_argument('productivity', type=int, choices=range(1, 11), help='Productivity rating 1-10')
    rate_music_parser.add_argument('focus', type=int, choices=range(1, 11), help='Focus rating 1-10')
    
    music_subparsers.add_parser('analytics', help='Show music productivity analytics')
    music_subparsers.add_parser('recommend', help='Get music recommendations')
    
    voice_parser = subparsers.add_parser('voice', help='Voice command management')
    voice_subparsers = voice_parser.add_subparsers(dest='voice_action')
    
    voice_enable_parser = voice_subparsers.add_parser('enable', help='Enable voice commands')
    voice_enable_parser.add_argument('--sensitivity', type=float, default=0.7, help='Voice sensitivity (0.1-1.0)')
    voice_enable_parser.add_argument('--language', default='en-US', help='Language code (e.g., en-US, es-ES)')
    voice_enable_parser.add_argument('--wake-word', default='devflow', help='Wake word to activate commands')
    
    voice_subparsers.add_parser('disable', help='Disable voice commands')
    voice_subparsers.add_parser('status', help='Show voice command status and settings')
    voice_subparsers.add_parser('interactive', help='Start interactive voice command mode')
    
    voice_transcribe_parser = voice_subparsers.add_parser('transcribe', help='Voice-to-text transcription')
    voice_transcribe_parser.add_argument('--to-notes', action='store_true', help='Convert speech directly to session notes')
    voice_transcribe_parser.add_argument('--text', help='Text to simulate voice transcription')
    
    ideas_parser = subparsers.add_parser('idea', help='Quick ideas and brainstorming')
    ideas_subparsers = ideas_parser.add_subparsers(dest='idea_action')
    
    add_idea_parser = ideas_subparsers.add_parser('add', help='Add a quick idea or TODO')
    add_idea_parser.add_argument('text', help='The idea text')
    add_idea_parser.add_argument('--category', default='general', help='Idea category')
    add_idea_parser.add_argument('--priority', type=int, default=3, choices=range(1, 6), help='Priority level 1-5')
    add_idea_parser.add_argument('--tags', default='', help='Comma-separated tags')
    
    list_ideas_parser = ideas_subparsers.add_parser('list', help='List ideas')
    list_ideas_parser.add_argument('--category', help='Filter by category')
    list_ideas_parser.add_argument('--status', default='open', choices=['open', 'completed', 'all'], help='Filter by status')
    list_ideas_parser.add_argument('--limit', type=int, default=20, help='Maximum number of ideas to show')
    
    complete_idea_parser = ideas_subparsers.add_parser('complete', help='Mark idea as completed')
    complete_idea_parser.add_argument('id', type=int, help='Idea ID to complete')
    
    delete_idea_parser = ideas_subparsers.add_parser('delete', help='Delete an idea')
    delete_idea_parser.add_argument('id', type=int, help='Idea ID to delete')
    
    search_ideas_parser = ideas_subparsers.add_parser('search', help='Search ideas')
    search_ideas_parser.add_argument('term', help='Search term')
    
    brainstorm_parser = ideas_subparsers.add_parser('brainstorm', help='Start interactive brainstorming session')
    brainstorm_parser.add_argument('--topic', default='', help='Brainstorming topic')
    
    ideas_subparsers.add_parser('stats', help='Show ideas statistics')
    
    # Mood tracking
    mood_parser = subparsers.add_parser('mood', help='Mood and wellness tracking')
    mood_subparsers = mood_parser.add_subparsers(dest='mood_action')
    
    log_mood_parser = mood_subparsers.add_parser('log', help='Log current mood and energy levels')
    log_mood_parser.add_argument('project', help='Project name')
    log_mood_parser.add_argument('mood', type=int, help='Mood score (1-10)')
    log_mood_parser.add_argument('energy', type=int, help='Energy level (1-10)')
    log_mood_parser.add_argument('stress', type=int, help='Stress level (1-10)')
    log_mood_parser.add_argument('motivation', type=int, help='Motivation level (1-10)')
    log_mood_parser.add_argument('--focus', default='normal', help='Focus difficulty level')
    log_mood_parser.add_argument('--notes', default='', help='Additional notes')
    
    mood_trends_parser = mood_subparsers.add_parser('trends', help='Show mood trends')
    mood_trends_parser.add_argument('--project', help='Project name to filter by')
    mood_trends_parser.add_argument('--days', type=int, default=7, help='Number of days to analyze')
    
    # Code pattern detection
    patterns_parser = subparsers.add_parser('patterns', help='Code pattern analysis')
    patterns_parser.add_argument('project', help='Project name')
    patterns_parser.add_argument('file', help='File path to analyze')
    
    # Pomodoro timer
    pomodoro_parser = subparsers.add_parser('pomodoro', help='Pomodoro timer sessions')
    pomodoro_parser.add_argument('project', help='Project name')
    pomodoro_parser.add_argument('--duration', type=int, default=25, help='Duration in minutes')
    pomodoro_parser.add_argument('--type', default='work', help='Type of pomodoro (work/break)')
    
    # Daily quotes
    subparsers.add_parser('quote', help='Show inspiring daily quote')
    
    # Break suggestions
    break_parser = subparsers.add_parser('break', help='Get break suggestions')
    break_parser.add_argument('project', help='Project name')
    break_parser.add_argument('duration', type=int, help='Current session duration in minutes')
    
    # Coding style analysis
    style_parser = subparsers.add_parser('style', help='Analyze coding style')
    style_parser.add_argument('project', help='Project name')
    style_parser.add_argument('file', help='File path to analyze')
    
    # Project comparison
    compare_parser = subparsers.add_parser('compare', help='Compare project productivity')
    compare_parser.add_argument('project_a', help='First project to compare')
    compare_parser.add_argument('project_b', help='Second project to compare')
    
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
        print("  snapshot           - Take project snapshot")
        print("  snapshots          - Show session snapshots")
        print("  progress [days]    - Show visual progress chart")
        print("  music log <type>   - Log music you're listening to")
        print("  music stop         - Stop current music session")
        print("  music status       - Show current music")
        print("  music rate         - Rate music productivity impact")
        print("  music analytics    - Show music productivity stats")
        print("  music recommend    - Get music recommendations")
        print("  voice enable       - Enable voice commands")
        print("  voice interactive  - Start voice command mode")
        print("  voice transcribe   - Voice-to-text for notes")
        print("  voice status       - Show voice settings")
        print("  idea add <text>    - Add quick idea or TODO")
        print("  idea list          - List your ideas")
        print("  idea complete <id> - Mark idea as done")
        print("  idea search <term> - Search through ideas")
        print("  idea brainstorm    - Start brainstorming session")
        print("  idea stats         - Show ideas dashboard")
        print("")
        print("🧠 WELLNESS & PRODUCTIVITY:")
        print("  mood log <project> <mood> <energy> <stress> <motivation> - Log mood (1-10 scale)")
        print("  mood trends        - Show mood trends over time")
        print("  pomodoro <project> - Start pomodoro timer")
        print("  quote             - Show daily inspiring quote")
        print("  break <project> <duration> - Get break suggestions")
        print("")
        print("🔍 CODE ANALYSIS:")
        print("  patterns <project> <file> - Analyze code patterns")
        print("  style <project> <file>    - Analyze coding style")
        print("  compare <proj1> <proj2>   - Compare project productivity")
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
    elif args.command == 'snapshot':
        cli.take_snapshot(args.milestone, args.notes)
    elif args.command == 'snapshots':
        cli.show_snapshots()
    elif args.command == 'progress':
        cli.show_progress_chart(args.days)
    elif args.command == 'music':
        if args.music_action == 'log':
            cli.log_music(args.type, args.artist, args.track, args.genre, args.mood, args.energy)
        elif args.music_action == 'stop':
            cli.stop_music()
        elif args.music_action == 'status':
            cli.show_current_music()
        elif args.music_action == 'rate':
            cli.rate_music(args.type, args.productivity, args.focus)
        elif args.music_action == 'analytics':
            cli.show_music_analytics()
        elif args.music_action == 'recommend':
            cli.show_music_recommendations()
    elif args.command == 'voice':
        if args.voice_action == 'enable':
            cli.enable_voice_commands(args.sensitivity, args.language, getattr(args, 'wake_word', 'devflow'))
        elif args.voice_action == 'disable':
            cli.disable_voice_commands()
        elif args.voice_action == 'status':
            cli.show_voice_status()
        elif args.voice_action == 'interactive':
            cli.voice_interactive_mode()
        elif args.voice_action == 'transcribe':
            if args.to_notes:
                cli.voice_transcribe_to_notes(getattr(args, 'text', None))
            else:
                print("🎤 Voice transcription mode")
                print("Use --to-notes to convert speech to session notes")
                print("Example: devflow voice transcribe --to-notes")
    elif args.command == 'idea':
        if args.idea_action == 'add':
            cli.add_idea(args.text, args.category, args.priority, args.tags)
        elif args.idea_action == 'list':
            cli.list_ideas(args.category, args.status, args.limit)
        elif args.idea_action == 'complete':
            cli.complete_idea(args.id)
        elif args.idea_action == 'delete':
            cli.delete_idea(args.id)
        elif args.idea_action == 'search':
            cli.search_ideas(args.term)
        elif args.idea_action == 'brainstorm':
            cli.brainstorm_session(args.topic)
        elif args.idea_action == 'stats':
            cli.show_idea_stats()
    
    elif args.command == 'mood':
        if args.mood_action == 'log':
            cli.log_mood(args.project, args.mood, args.energy, args.stress, args.motivation, args.focus, args.notes)
        elif args.mood_action == 'trends':
            cli.show_mood_trends(args.project, args.days)
    
    elif args.command == 'patterns':
        cli.detect_code_patterns(args.project, args.file)
    
    elif args.command == 'pomodoro':
        cli.start_pomodoro(args.project, args.duration, args.type)
    
    elif args.command == 'quote':
        cli.show_daily_quote()
    
    elif args.command == 'break':
        cli.suggest_break(args.project, args.duration)
    
    elif args.command == 'style':
        cli.analyze_coding_style(args.project, args.file)
    
    elif args.command == 'compare':
        cli.compare_projects(args.project_a, args.project_b)
    
    else:
        print(f"Unknown command: {args.command}")
        print("Use 'devflow --help' for available commands")

if __name__ == '__main__':
    main()