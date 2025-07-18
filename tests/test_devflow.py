# DevFlow CLI Test Suite

import unittest
import tempfile
import shutil
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from devflow import DevFlowDB, DevFlowCLI

class TestDevFlowDB(unittest.TestCase):
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / 'test.db'
        self.db = DevFlowDB(self.db_path)
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_database_initialization(self):
        tables = self.db.execute_query(
            "SELECT name FROM sqlite_master WHERE type='table'",
            fetch=True
        )
        table_names = [table[0] for table in tables]
        
        expected_tables = ['sessions', 'templates', 'goals', 'activity']
        for table in expected_tables:
            self.assertIn(table, table_names)
    
    def test_session_crud(self):
        self.db.execute_query(
            "INSERT INTO sessions (project_name, project_path, start_time) VALUES (?, ?, ?)",
            ('test-project', '/test/path', '2025-01-01T10:00:00')
        )
        
        sessions = self.db.execute_query(
            "SELECT project_name FROM sessions WHERE project_name = ?",
            ('test-project',), fetch=True
        )
        
        self.assertEqual(len(sessions), 1)
        self.assertEqual(sessions[0][0], 'test-project')

class TestDevFlowCLI(unittest.TestCase):
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / 'test.db'
        self.cli = DevFlowCLI()
        self.cli.db = DevFlowDB(self.db_path)
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_format_duration(self):
        self.assertEqual(self.cli.format_duration(30), "30s")
        self.assertEqual(self.cli.format_duration(90), "1m 30s")
        self.assertEqual(self.cli.format_duration(3661), "1h 1m")
    
    def test_intensity_character(self):
        self.assertEqual(self.cli.get_intensity_char(0), '░')
        self.assertEqual(self.cli.get_intensity_char(30), '▒')
        self.assertEqual(self.cli.get_intensity_char(120), '▓')
        self.assertEqual(self.cli.get_intensity_char(300), '█')

if __name__ == '__main__':
    unittest.main()
