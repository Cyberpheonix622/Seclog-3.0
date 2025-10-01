import win32evtlog
import threading
from datetime import datetime
import csv
from tkinter import filedialog, messagebox

class LogHandler:
    """
    Handles all backend logic for fetching, filtering, monitoring,
    and exporting Windows Event Logs.
    """
    def __init__(self):
        self.monitoring = False
        self.monitor_thread = None

    def fetch_logs(self, log_types, start_date, end_date, keyword):
        """
        Fetches and filters logs based on the provided criteria.

        Returns:
            A tuple containing a list of log records (dicts) and a dictionary
            of log counts by type.
        """
        logs = []
        log_type_counts = {"Security": 0, "System": 0, "Application": 0}

        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d") if start_date else None
            end_dt = datetime.strptime(end_date, "%Y-%m-%d") if end_date else None
        except ValueError:
            messagebox.showerror("Invalid Date", "Please enter valid date(s) in YYYY-MM-DD format.")
            return [], log_type_counts

        for log_type in log_types:
            try:
                handle = win32evtlog.OpenEventLog(None, log_type)
                flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ
                total_records = win32evtlog.GetNumberOfEventLogRecords(handle)
                
                events_read = 0
                while events_read < total_records:
                    events = win32evtlog.ReadEventLog(handle, flags, 0, 1024) # Read in chunks
                    if not events:
                        break
                    
                    for ev_obj in events:
                        time_generated = ev_obj.TimeGenerated
                        
                        # Apply date filtering
                        if start_dt and time_generated < start_dt:
                            continue
                        if end_dt and time_generated > end_dt:
                            continue

                        record = {
                            "TimeGenerated": time_generated.strftime("%Y-%m-%d %H:%M:%S"),
                            "SourceName": ev_obj.SourceName,
                            "EventID": str(ev_obj.EventID & 0xFFFF),
                            "EventType": str(ev_obj.EventType),
                            "Category": str(ev_obj.EventCategory),
                            "Message": ' '.join(str(s).strip() for s in ev_obj.StringInserts) if ev_obj.StringInserts else ""
                        }

                        # Apply keyword filtering
                        if not keyword or keyword.lower() in str(record).lower():
                            logs.append(record)
                            if log_type in log_type_counts:
                                log_type_counts[log_type] += 1
                    
                    events_read += len(events)
                win32evtlog.CloseEventLog(handle)
            except Exception as e:
                print(f"Error reading {log_type} log: {e}")
                # messagebox.showerror("Error", f"Failed to read {log_type} log: {str(e)}")

        return logs, log_type_counts

    def start_monitoring(self, callback_func):
        """Starts the real-time log monitoring thread."""
        if self.monitoring:
            messagebox.showinfo("Real-Time", "Already monitoring.")
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, args=(callback_func,), daemon=True)
        self.monitor_thread.start()

    def stop_monitoring(self):
        """Stops the real-time log monitoring."""
        self.monitoring = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            # The thread will exit its loop based on the self.monitoring flag
            print("Stopping monitoring thread...")

    def _monitor_loop(self, callback_func):
        """The actual monitoring logic that runs in a separate thread."""
        # This is a simplified example. Real-time monitoring is complex.
        # For a robust solution, you'd need to handle event sources properly.
        # This example will periodically re-fetch logs to simulate real-time updates.
        print("Monitoring thread started.")
        # This is a placeholder for a more advanced real-time implementation
        # A true real-time implementation would use Win32 API calls like `NotifyChangeEventLog`
        # which are more complex. For this project, a periodic poll is a reasonable simulation.
        while self.monitoring:
            # Simulate fetching new logs every 5 seconds
            # In a real app, you would only fetch *new* events since the last check
            logs, counts = self.fetch_logs(["Security", "System", "Application"], None, None, "")
            if self.monitoring: # Check again in case it was stopped during fetch
                callback_func(logs, counts)
            threading.Event().wait(5)
        print("Monitoring thread stopped.")

    def save_logs_to_csv(self, logs_to_save):
        """Saves a list of log records to a CSV file."""
        if not logs_to_save:
            messagebox.showwarning("No Data", "No filtered log data to save.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, "w", newline='', encoding="utf-8") as f:
                    if logs_to_save:
                        writer = csv.DictWriter(f, fieldnames=logs_to_save[0].keys())
                        writer.writeheader()
                        writer.writerows(logs_to_save)
                messagebox.showinfo("Success", f"Logs successfully saved to {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file: {str(e)}")
