# modules/database_handler.py

import sqlite3
import os
from collections import Counter
from datetime import datetime, timedelta
import csv
import gzip # 👈 Import for compression

class DatabaseHandler:
    def __init__(self, db_path="data/seclog.db", archive_path="data/logs_archive/"):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        os.makedirs(archive_path, exist_ok=True) # 👈 Ensure archive directory exists
        self.db_path = db_path
        self.archive_path = archive_path
        self.conn = None
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            self.setup_database()
            # 🔹 CHANGE: Call archive instead of delete 🔹
            self.archive_old_logs(retention_days=30)
        except sqlite3.Error as e:
            print(f"Database error: {e}")

    # 🔹 REPLACED METHOD: This now archives before deleting 🔹
    def archive_old_logs(self, retention_days):
        """
        Selects logs older than the retention period, saves them to a compressed
        CSV file, and then deletes them from the database.
        """
        cursor = self.conn.cursor()
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        cutoff_timestamp = cutoff_date.strftime("%Y-%m-%d %H:%M:%S")

        print(f"Archiving logs older than {retention_days} days (before {cutoff_timestamp})...")
        try:
            # Step 1: Select old logs
            cursor.execute("SELECT * FROM logs WHERE timestamp < ?", (cutoff_timestamp,))
            old_logs = [dict(row) for row in cursor.fetchall()]

            if not old_logs:
                print("No old logs to archive.")
                return

            # Step 2: Write old logs to a compressed archive file
            archive_filename = f"archive_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv.gz"
            archive_filepath = os.path.join(self.archive_path, archive_filename)
            headers = old_logs[0].keys()

            with gzip.open(archive_filepath, 'wt', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
                writer.writerows(old_logs)
            
            print(f"Successfully archived {len(old_logs)} logs to {archive_filepath}")

            # Step 3: Delete the old logs from the database
            cursor.execute("DELETE FROM logs WHERE timestamp < ?", (cutoff_timestamp,))
            self.conn.commit()
            print(f"Successfully deleted {len(old_logs)} archived logs from the live database.")

        except Exception as e:
            print(f"Failed during log archival process: {e}")

    # ... (rest of the file is unchanged) ...
    def setup_database(self):
        cursor = self.conn.cursor()
        cursor.execute("""CREATE TABLE IF NOT EXISTS logs (id INTEGER PRIMARY KEY, timestamp TEXT, logfile TEXT, source TEXT, event_id TEXT, event_type TEXT, severity TEXT, message TEXT, UNIQUE(timestamp, logfile, source, event_id, message))""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS incidents (id INTEGER PRIMARY KEY, rule_name TEXT, trigger_time TEXT, status TEXT, notes TEXT)""")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON logs (timestamp);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_logfile ON logs (logfile);")
        self.conn.commit()
        print("Database setup complete. 'logs' and 'incidents' tables are ready.")

    def create_incident(self, alert):
        cursor = self.conn.cursor()
        try:
            cursor.execute("INSERT INTO incidents (rule_name, trigger_time, status, notes) VALUES (?, ?, ?, ?)", (alert['rule_name'], alert['trigger_time'], 'Open', ''))
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Failed to create incident: {e}")
            return None

    def get_all_incidents(self):
        cursor = self.conn.cursor()
        try:
            cursor.execute("SELECT * FROM incidents ORDER BY trigger_time DESC")
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"Failed to get incidents: {e}")
            return []

    def update_incident_status(self, incident_id, new_status):
        cursor = self.conn.cursor()
        try:
            cursor.execute("UPDATE incidents SET status = ? WHERE id = ?", (new_status, incident_id))
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Failed to update incident status: {e}")

    def insert_logs(self, logs):
        if not logs: return
        cursor = self.conn.cursor()
        logs_to_insert = []
        for log in logs:
            if "error" not in log:
                logs_to_insert.append((log.get("timestamp"), log.get("logfile"), log.get("source"), log.get("event_id"), log.get("event_type"), log.get("severity"), log.get("message")))
        if not logs_to_insert: return
        try:
            cursor.executemany("INSERT OR IGNORE INTO logs (timestamp, logfile, source, event_id, event_type, severity, message) VALUES (?, ?, ?, ?, ?, ?, ?)", logs_to_insert)
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Failed to insert logs into database: {e}")

    def query_logs(self, log_sources=None, start_date=None, end_date=None, keyword=None):
        cursor = self.conn.cursor()
        query = "SELECT * FROM logs"
        conditions, params = [], []
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
        cursor = self.conn.cursor()
        query = "SELECT COUNT(*) FROM logs WHERE logfile = ? AND timestamp >= ?"
        params = [logfile, start_time]
        for key, value in conditions.items():
            query += f" AND {key} = ?"
            params.append(value)
        try:
            cursor.execute(query, params)
            return cursor.fetchone()[0]
        except sqlite3.Error as e:
            print(f"Failed to count logs for rule: {e}")
            return 0
            
    def close(self):
        if self.conn: self.conn.close()