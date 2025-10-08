# modules/log_handler.py

import threading
import time
import csv
from datetime import datetime
from tkinter import filedialog, messagebox
from collections import Counter
import win32evtlog
import win32evtlogutil
import pywintypes
from modules.log_normalizer import LogNormalizer

class LogHandler:
    """
    Handles fetching, monitoring, normalizing, and saving Windows Event Logs
    using the direct win32evtlog API for improved stability.
    """
    def __init__(self):
        self.monitoring = False
        self.monitor_thread = None
        self.normalizer = LogNormalizer()

    def fetch_logs(self, log_types, start_date_str, end_date_str, keyword):
        # ... (This method is unchanged) ...
        all_logs = []
        counts = Counter()
        start_dt = datetime.strptime(start_date_str, "%Y-%m-%d") if start_date_str else None
        end_dt = datetime.strptime(end_date_str, "%Y-%m-%d") if end_date_str else None
        try:
            for log_file in log_types:
                log_handle = win32evtlog.OpenEventLog(None, log_file)
                flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ
                events = True
                while events:
                    events = win32evtlog.ReadEventLog(log_handle, flags, 0)
                    if not events: break
                    for ev_obj in events:
                        time_generated = ev_obj.TimeGenerated
                        if start_dt and time_generated < start_dt: continue
                        if end_dt and time_generated > end_dt: continue
                        message = win32evtlogutil.SafeFormatMessage(ev_obj, log_file)
                        if keyword and keyword.lower() not in message.lower(): continue
                        record = {
                            "TimeGenerated": time_generated, "SourceName": ev_obj.SourceName,
                            "EventID": ev_obj.EventID & 0xFFFF, "EventType": ev_obj.EventType,
                            "Message": message, "logfile": log_file
                        }
                        normalized_record = self.normalizer.normalize("windows", record)
                        all_logs.append(normalized_record)
                counts[log_file] = len(all_logs)
                win32evtlog.CloseEventLog(log_handle)
            all_logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            return all_logs, counts
        except pywintypes.error as e:
            if e.winerror == 5: messagebox.showerror("Permissions Error", f"Access denied to '{log_file}' log. Run as admin.")
            else: messagebox.showerror("Event Log Error", f"Error reading '{log_file}'. Code: {e.winerror}")
            return [], Counter()
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")
            return [], Counter()

    def start_monitoring(self, update_callback):
        # ... (This method is unchanged) ...
        if self.monitoring: return
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, args=(update_callback,), daemon=True)
        self.monitor_thread.start()

    def stop_monitoring(self):
        # ... (This method is unchanged) ...
        self.monitoring = False

    # 🔹 UPDATED METHOD: Smarter logic to handle log rotation and clearing 🔹
    def _monitor_loop(self, update_callback):
        """Polls for new event log records with robust error handling for log rotation."""
        last_record_numbers = {}
        log_files = ["Security", "System", "Application"]
        
        while self.monitoring:
            new_logs = []
            counts = Counter()
            
            for log_file in log_files:
                log_handle = None
                try:
                    log_handle = win32evtlog.OpenEventLog(None, log_file)
                    total_records = win32evtlog.GetNumberOfEventLogRecords(log_handle)
                    
                    # Get the last record number we processed, default to the current total
                    last_seen_num = last_record_numbers.get(log_file, total_records)

                    if total_records > last_seen_num:
                        oldest_record_num = win32evtlog.GetOldestEventLogRecord(log_handle)
                        
                        # Determine where to start reading from.
                        start_from_num = last_seen_num
                        
                        # If our last seen record number is now gone (due to log wrapping/clearing),
                        # start from the oldest available record to avoid errors.
                        if start_from_num < oldest_record_num:
                            start_from_num = oldest_record_num
                        
                        # We can only seek if we have a valid starting point.
                        if start_from_num > 0:
                            flags = win32evtlog.EVENTLOG_FORWARDS_READ | win32evtlog.EVENTLOG_SEEK_READ
                            events = win32evtlog.ReadEventLog(log_handle, flags, start_from_num)
                            
                            # Filter out records we have already seen in previous loops
                            events_to_process = [e for e in events if e.RecordNumber > last_seen_num]
                        else: # The log was likely empty, read everything
                             flags = win32evtlog.EVENTLOG_FORWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ
                             events_to_process = win32evtlog.ReadEventLog(log_handle, flags, 0)

                        for ev_obj in events_to_process:
                            message = win32evtlogutil.SafeFormatMessage(ev_obj, log_file)
                            record = {
                                "TimeGenerated": ev_obj.TimeGenerated, "SourceName": ev_obj.SourceName,
                                "EventID": ev_obj.EventID & 0xFFFF, "EventType": ev_obj.EventType,
                                "Message": message, "logfile": log_file
                            }
                            normalized_record = self.normalizer.normalize("windows", record)
                            new_logs.append(normalized_record)
                            counts[log_file] += 1
                    
                    # Update the last seen number to the new total for the next cycle
                    last_record_numbers[log_file] = total_records
                
                except Exception as e:
                    print(f"Error processing '{log_file}' in monitor loop: {e}")
                
                finally:
                    if log_handle:
                        win32evtlog.CloseEventLog(log_handle)

            if new_logs:
                new_logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
                update_callback(new_logs, counts)
            
            time.sleep(3)

    def save_logs_to_csv(self, logs_to_save):
        # ... (This method is unchanged) ...
        if not logs_to_save:
            messagebox.showinfo("Export", "No logs to export.")
            return
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv", filetypes=[("CSV files", "*.csv"), ("All files", "*.*")], title="Save Logs As..."
        )
        if not filepath: return
        headers = ["timestamp", "logfile", "source", "event_id", "event_type", "severity", "message"]
        try:
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
                for log in logs_to_save:
                    filtered_log = {k: log.get(k, '') for k in headers}
                    writer.writerow(filtered_log)
            messagebox.showinfo("Export Successful", f"Successfully saved {len(logs_to_save)} logs to {filepath}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to save logs to CSV.\nError: {e}")