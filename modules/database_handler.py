# modules/database_handler.py

import sqlite3
import os
from collections import Counter
from datetime import datetime, timedelta # 👈 Import timedelta

class DatabaseHandler:
    def __init__(self, db_path="data/seclog.db"):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self.conn = None
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            self.setup_database()

            # 🔹 Run cleanup on startup 🔹
            self.delete_old_logs(retention_days=120)

        except sqlite3.Error as e:
            print(f"Database error: {e}")

    def setup_database(self):
        # ... (This method is unchanged) ...
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                logfile TEXT,
                source TEXT,
                event_id TEXT,
                event_type TEXT,
                severity TEXT,
                message TEXT,
                UNIQUE(timestamp, logfile, source, event_id, message)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON logs (timestamp);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_logfile ON logs (logfile);")
        self.conn.commit()
        print("Database setup complete. 'logs' table is ready.")

    # 🔹 NEW METHOD: To delete logs older than the retention period 🔹
    def delete_old_logs(self, retention_days):
        """Deletes logs from the database that are older than the specified retention period."""
        cursor = self.conn.cursor()
        
        # Calculate the cutoff date
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        cutoff_timestamp = cutoff_date.strftime("%Y-%m-%d %H:%M:%S")
        
        print(f"Running cleanup: Deleting logs older than {retention_days} days (before {cutoff_timestamp})...")
        
        try:
            # Execute the DELETE query
            cursor.execute("DELETE FROM logs WHERE timestamp < ?", (cutoff_timestamp,))
            
            # Get the number of deleted rows and commit
            deleted_count = cursor.rowcount
            self.conn.commit()
            
            if deleted_count > 0:
                print(f"Cleanup complete. Deleted {deleted_count} old logs.")
            else:
                print("No old logs to delete.")

        except sqlite3.Error as e:
            print(f"Failed to delete old logs: {e}")

    def insert_logs(self, logs):
        # ... (This method is unchanged) ...
        if not logs: return
        cursor = self.conn.cursor()
        logs_to_insert = []
        for log in logs:
            if "error" not in log:
                logs_to_insert.append((
                    log.get("timestamp"), log.get("logfile"), log.get("source"),
                    log.get("event_id"), log.get("event_type"), log.get("severity"),
                    log.get("message")
                ))
        if not logs_to_insert: return
        try:
            cursor.executemany("""
                INSERT OR IGNORE INTO logs (timestamp, logfile, source, event_id, event_type, severity, message)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, logs_to_insert)
            self.conn.commit()
            print(f"Successfully inserted or ignored {len(logs_to_insert)} logs.")
        except sqlite3.Error as e:
            print(f"Failed to insert logs into database: {e}")

    def query_logs(self, log_sources=None, start_date=None, end_date=None, keyword=None):
        # ... (This method is unchanged) ...
        cursor = self.conn.cursor()
        query = "SELECT * FROM logs"
        conditions = []
        params = []
        if log_sources and "All" not in log_sources:
            placeholders = ', '.join('?' for _ in log_sources)
            conditions.append(f"logfile IN ({placeholders})")
            params.extend(log_sources)
        if start_date:
            conditions.append("timestamp >= ?")
            params.append(start_date)
        if end_date:
            conditions.append("timestamp < date(?, '+1 day')")
            params.append(end_date)
        if keyword:
            conditions.append("message LIKE ?")
            params.append(f"%{keyword}%")
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY timestamp DESC"
        try:
            cursor.execute(query, params)
            results = [dict(row) for row in cursor.fetchall()]
            counts = Counter(log['source'] for log in results)
            return results, counts
        except sqlite3.Error as e:
            print(f"Failed to query logs: {e}")
            return [], Counter()

    def count_logs_for_rule(self, logfile, conditions, start_time):
        # ... (This method is unchanged) ...
        cursor = self.conn.cursor()
        query = "SELECT COUNT(*) FROM logs WHERE logfile = ? AND timestamp >= ?"
        params = [logfile, start_time]
        for key, value in conditions.items():
            query += f" AND {key} = ?"
            params.append(value)
        try:
            cursor.execute(query, params)
            count = cursor.fetchone()[0]
            return count
        except sqlite3.Error as e:
            print(f"Failed to count logs for rule: {e}")
            return 0

    def close(self):
        if self.conn:
            self.conn.close()