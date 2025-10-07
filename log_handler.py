# log_handler.py

import threading
import time
import csv
from datetime import datetime
from tkinter import filedialog, messagebox
from collections import Counter

# This version uses the more stable 'win32evtlog' instead of 'wmi'
import win32evtlog 
import win32evtlogutil
import win32api
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
        """
        Fetches and filters logs directly from the event log API.
        """
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
                    if not events:
                        break
                    
                    for ev_obj in events:
                        # --- Filtering ---
                        time_generated = ev_obj.TimeGenerated
                        if start_dt and time_generated < start_dt:
                            continue
                        if end_dt and time_generated > end_dt:
                            continue
                        
                        message = win32evtlogutil.SafeFormatMessage(ev_obj, log_file)
                        if keyword and keyword.lower() not in message.lower():
                            continue
                        
                        # --- Normalization ---
                        record = {
                            "TimeGenerated": time_generated,
                            "SourceName": ev_obj.SourceName,
                            "EventID": ev_obj.EventID & 0xFFFF, # Mask to get lower 16 bits
                            "EventType": ev_obj.EventType,
                            "Message": message
                        }
                        normalized_record = self.normalizer.normalize("windows", record)
                        all_logs.append(normalized_record)
                
                counts[log_file] = len(all_logs) # This count is cumulative for now
                win32evtlog.CloseEventLog(log_handle)
            
            all_logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            return all_logs, counts

        except pywintypes.error as e:
            if e.winerror == 5: # Access is denied
                 messagebox.showerror("Permissions Error", f"Access denied when trying to read the '{log_file}' log.\nPlease run the application as an administrator.")
            else:
                messagebox.showerror("Event Log Error", f"Failed to read from '{log_file}'.\nError code: {e.winerror}\n{e.strerror}")
            return [], Counter()
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")
            return [], Counter()

    def start_monitoring(self, update_callback):
        """Starts the real-time log monitoring in a background thread."""
        if self.monitoring:
            return
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, args=(update_callback,), daemon=True)
        self.monitor_thread.start()

    def stop_monitoring(self):
        """Stops the real-time log monitoring."""
        self.monitoring = False

    def _monitor_loop(self, update_callback):
        """Polls for new event log records."""
        last_record_numbers = {}
        log_files = ["Security", "System", "Application"]
        
        while self.monitoring:
            new_logs = []
            counts = Counter()
            try:
                for log_file in log_files:
                    log_handle = win32evtlog.OpenEventLog(None, log_file)
                    total_records = win32evtlog.GetNumberOfEventLogRecords(log_handle)
                    
                    last_seen = last_record_numbers.get(log_file, total_records)
                    
                    if total_records > last_seen:
                        flags = win32evtlog.EVENTLOG_FORWARDS_READ | win32evtlog.EVENTLOG_SEEK_READ
                        events = win32evtlog.ReadEventLog(log_handle, flags, last_seen)
                        
                        for ev_obj in events:
                            message = win32evtlogutil.SafeFormatMessage(ev_obj, log_file)
                            record = {
                                "TimeGenerated": ev_obj.TimeGenerated,
                                "SourceName": ev_obj.SourceName,
                                "EventID": ev_obj.EventID & 0xFFFF,
                                "EventType": ev_obj.EventType,
                                "Message": message
                            }
                            normalized_record = self.normalizer.normalize("windows", record)
                            new_logs.append(normalized_record)
                            counts[log_file] += 1
                    
                    last_record_numbers[log_file] = total_records
                    win32evtlog.CloseEventLog(log_handle)

                if new_logs:
                    new_logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
                    update_callback(new_logs, counts)
            
            except Exception as e:
                print(f"Error in monitor loop: {e}")

            time.sleep(3)

    def save_logs_to_csv(self, logs_to_save):
        """Saves a list of log dictionaries to a CSV file."""
        if not logs_to_save:
            messagebox.showinfo("Export", "No logs to export.")
            return
        
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv", filetypes=[("CSV files", "*.csv"), ("All files", "*.*")], title="Save Logs As..."
        )
        if not filepath: return

        headers = ["timestamp", "source", "event_id", "event_type", "severity", "message"]
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