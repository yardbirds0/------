# -*- coding: utf-8 -*-
"""
Unit Tests for Chat Database Manager
"""

import unittest
import tempfile
import os
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.chat.db_manager import ChatDatabaseManager


class TestChatDatabaseManager(unittest.TestCase):
    """Test cases for ChatDatabaseManager"""

    def setUp(self):
        """Create temporary database for testing"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_chat.db")
        self.db_manager = ChatDatabaseManager(self.db_path)

    def tearDown(self):
        """Clean up test database"""
        self.db_manager.close()

        # Remove test database
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        os.rmdir(self.temp_dir)

    def test_database_creation(self):
        """Test database file is created"""
        self.db_manager.connect()
        self.assertTrue(os.path.exists(self.db_path))

    def test_schema_initialization(self):
        """Test schema is initialized correctly"""
        self.db_manager.connect()

        # Check tables exist
        tables = self.db_manager.fetchall(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        table_names = [row['name'] for row in tables]

        self.assertIn('sessions', table_names)
        self.assertIn('messages', table_names)

    def test_fts_virtual_table(self):
        """Test FTS5 virtual table is created"""
        self.db_manager.connect()

        # Check FTS5 table exists
        fts_tables = self.db_manager.fetchall(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='messages_fts'"
        )

        self.assertEqual(len(fts_tables), 1)

    def test_insert_session(self):
        """Test inserting a session"""
        self.db_manager.connect()

        session_id = "test_session_001"
        title = "Test Session"

        self.db_manager.execute(
            "INSERT INTO sessions (id, title) VALUES (?, ?)",
            (session_id, title)
        )

        # Verify insert
        result = self.db_manager.fetchone(
            "SELECT * FROM sessions WHERE id = ?",
            (session_id,)
        )

        self.assertIsNotNone(result)
        self.assertEqual(result['id'], session_id)
        self.assertEqual(result['title'], title)

    def test_insert_message(self):
        """Test inserting a message"""
        self.db_manager.connect()

        # Create session first
        session_id = "test_session_002"
        self.db_manager.execute(
            "INSERT INTO sessions (id, title) VALUES (?, ?)",
            (session_id, "Test Session")
        )

        # Insert message
        message_id = "test_message_001"
        content = "Hello, this is a test message"

        self.db_manager.execute(
            "INSERT INTO messages (id, session_id, role, content) VALUES (?, ?, ?, ?)",
            (message_id, session_id, "user", content)
        )

        # Verify insert
        result = self.db_manager.fetchone(
            "SELECT * FROM messages WHERE id = ?",
            (message_id,)
        )

        self.assertIsNotNone(result)
        self.assertEqual(result['id'], message_id)
        self.assertEqual(result['content'], content)

    def test_fts_trigger(self):
        """Test FTS5 trigger on message insert"""
        self.db_manager.connect()

        # Create session
        session_id = "test_session_003"
        self.db_manager.execute(
            "INSERT INTO sessions (id, title) VALUES (?, ?)",
            (session_id, "Test Session")
        )

        # Insert message
        message_id = "test_message_002"
        content = "Search me in full text search"

        self.db_manager.execute(
            "INSERT INTO messages (id, session_id, role, content) VALUES (?, ?, ?, ?)",
            (message_id, session_id, "assistant", content)
        )

        # Search using FTS5
        results = self.db_manager.fetchall(
            "SELECT * FROM messages_fts WHERE content MATCH ?",
            ("search",)
        )

        self.assertGreater(len(results), 0)

    def test_cascade_delete(self):
        """Test cascade delete when session is deleted"""
        self.db_manager.connect()

        # Create session and message
        session_id = "test_session_004"
        message_id = "test_message_003"

        self.db_manager.execute(
            "INSERT INTO sessions (id, title) VALUES (?, ?)",
            (session_id, "Test Session")
        )

        self.db_manager.execute(
            "INSERT INTO messages (id, session_id, role, content) VALUES (?, ?, ?, ?)",
            (message_id, session_id, "user", "Test content")
        )

        # Delete session
        self.db_manager.execute(
            "DELETE FROM sessions WHERE id = ?",
            (session_id,)
        )

        # Verify message is also deleted
        message = self.db_manager.fetchone(
            "SELECT * FROM messages WHERE id = ?",
            (message_id,)
        )

        self.assertIsNone(message)

    def test_context_manager(self):
        """Test using database as context manager"""
        with ChatDatabaseManager(self.db_path) as db:
            # Should be connected
            self.assertIsNotNone(db.connection)

            # Insert test data
            db.execute(
                "INSERT INTO sessions (id, title) VALUES (?, ?)",
                ("ctx_session", "Context Manager Test")
            )

        # After context, connection should be closed
        self.assertIsNone(db.connection)

        # Data should persist
        db2 = ChatDatabaseManager(self.db_path)
        db2.connect()

        result = db2.fetchone(
            "SELECT * FROM sessions WHERE id = ?",
            ("ctx_session",)
        )

        self.assertIsNotNone(result)
        db2.close()


def run_tests():
    """Run all tests"""
    unittest.main(argv=[''], verbosity=2, exit=False)


if __name__ == '__main__':
    run_tests()
