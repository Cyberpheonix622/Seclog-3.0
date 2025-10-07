# modules/database_handler.py

import sqlite3
import os

class DatabaseHandler:
    """
    Handles all interactions with the SQLite database for storing and retrieving logs.
    """
    def __init__(self, db_path="data/seclog.db"):
        """
        Initializes the database connection and ensures the necessary table exists.
        
        Args:
            db_path (str): The path to the SQLite database file.
        """
        # Ensure the 'data' directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        self.db_path = db_path
        self.conn = None
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.setup_database()
        except sqlite3.Error as e:
            print(f"Database error: {e}")

    def setup_database(self):
        """
        Creates the 'logs' table if it does not already exist.
        A UNIQUE constraint is added to prevent duplicate log entries.
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                source TEXT,
                event_id TEXT,
                event_type TEXT,
                severity TEXT,
                message TEXT,
                UNIQUE(timestamp, source, event_id, message)
            )
        """)
        # Create an index on the timestamp for faster queries
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON logs (timestamp);")
        self.conn.commit()
        print("Database setup complete. 'logs' table is ready.")

    def insert_logs(self, logs):
        """
        Inserts a list of normalized log dictionaries into the database.
        Uses INSERT OR IGNORE to skip any logs that are already present.

        Args:
            logs (list): A list of log dictionaries.
        """
        if not logs:
            return

        cursor = self.conn.cursor()
        
        # Prepare data for insertion, ensuring all keys are present
        logs_to_insert = []
        for log in logs:
            if "error" not in log: # Don't store normalization errors
                logs_to_insert.append((
                    log.get("timestamp"),
                    log.get("source"),
                    log.get("event_id"),
                    log.get("event_type"),
                    log.get("severity"),
                    log.get("message")
                ))

        if not logs_to_insert:
            return
            
        try:
            # executemany is highly efficient for bulk inserts
            cursor.executemany("""
                INSERT OR IGNORE INTO logs (timestamp, source, event_id, event_type, severity, message)
                VALUES (?, ?, ?, ?, ?, ?)
            """, logs_to_insert)
            
            self.conn.commit()
            print(f"Successfully inserted or ignored {len(logs_to_insert)} logs into the database.")
        except sqlite3.Error as e:
            print(f"Failed to insert logs into database: {e}")

    def close(self):
        """Closes the database connection."""
        if self.conn:
            self.conn.close()