# main_app.py

import customtkinter as ctk
import tkinter as tk
import threading

from log_handler import LogHandler
from modules.database_handler import DatabaseHandler
from modules.rule_engine import RuleEngine
import ui_components

class SecurityLogApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("SecLog - Windows Security Log Viewer")
        self.geometry("1100x650")
        self.minsize(900, 500)

        # Initialize backend handlers
        self.log_handler = LogHandler()
        self.db_handler = DatabaseHandler()
        self.rule_engine = RuleEngine(db_handler=self.db_handler)

        # --- Data Storage ---
        self.filtered_logs = []
        self.triggered_alerts = [] # 👈 **CHANGE: Add a list to store alerts**

        # --- Configure Grid Layout & UI ---
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        ui_components.create_sidebar(self, self)
        ui_components.create_main_tabs(self, self)

    def search_logs(self):
        self.logs_label.configure(text="🔄 Syncing latest logs and searching database...")
        self.log_textbox.configure(state="normal")
        self.log_textbox.delete("1.0", tk.END)
        self.log_textbox.insert("1.0", "This may take a moment...")
        self.log_textbox.configure(state="disabled")
        selected_log_type = self.log_type.get()
        log_sources = ["Security", "System", "Application"] if selected_log_type == "All" else [selected_log_type]
        start_date = self.start_date_entry.get().strip() or None
        end_date = self.end_date_entry.get().strip() or None
        keyword = self.filter_entry.get().strip() or None
        threading.Thread(
            target=self._sync_and_query_thread,
            args=(log_sources, start_date, end_date, keyword),
            daemon=True
        ).start()

    def _sync_and_query_thread(self, log_sources, start_date, end_date, keyword):
        print("Syncing latest logs from Windows...")
        latest_logs, _ = self.log_handler.fetch_logs(log_sources, None, None, None)
        self.db_handler.insert_logs(latest_logs)
        
        print("Querying the database...")
        queried_logs, counts = self.db_handler.query_logs(log_sources, start_date, end_date, keyword)
        
        # Run the alert check and store any new alerts
        new_alerts = self.rule_engine.check_alerts()
        if new_alerts:
            self.triggered_alerts.extend(new_alerts)
            print(f"🚨 Found {len(new_alerts)} new alerts!")
        
        # Schedule the UI update on the main thread
        self.after(0, self._update_ui_with_db_results, queried_logs, counts)

    def _update_ui_with_db_results(self, logs, counts):
        """Updates the entire UI with new log data and alerts."""
        self.filtered_logs = logs
        
        self.logs_label.configure(text=f"Logs Found in Database: {len(self.filtered_logs)} entries")
        
        # Update all parts of the UI
        ui_components.display_logs(self.log_textbox, self.filtered_logs)
        ui_components.update_summary_cards(self, len(self.filtered_logs), counts)
        ui_components.update_summary_tab(self, self.filtered_logs)
        ui_components.draw_event_graph(self.graph_frame, self.filtered_logs)
        
        # 👈 **CHANGE: Update the alerts panel as well**
        ui_components.display_alerts(self.alerts_frame, self.triggered_alerts)

    # ... (rest of the methods are unchanged) ...
    def start_real_time_monitoring(self):
        self.log_handler.start_monitoring(self._real_time_update_callback)
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.logs_label.configure(text="🔄 Real-Time Monitoring Started...")

    def stop_real_time_monitoring(self):
        self.log_handler.stop_monitoring()
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self.logs_label.configure(text="Real-Time Monitoring Stopped.")

    def _real_time_update_callback(self, new_logs, counts):
        self.db_handler.insert_logs(new_logs)
        # In a real-time scenario, we might want to check alerts here as well
        new_alerts = self.rule_engine.check_alerts()
        if new_alerts:
            self.triggered_alerts.extend(new_alerts)
            print(f"🚨 Found {len(new_alerts)} new REAL-TIME alerts!")

        # Prepend new logs to the current view
        self.filtered_logs = new_logs + self.filtered_logs
        # Update the entire UI
        self.after(0, self._update_ui_with_db_results, self.filtered_logs, counts)
        
    def save_filtered_logs(self):
        self.log_handler.save_logs_to_csv(self.filtered_logs)

    def reset_filters(self):
        self.start_date_entry.delete(0, tk.END)
        self.end_date_entry.delete(0, tk.END)
        self.filter_entry.delete(0, tk.END)
        self.log_type.set("All")
        self.filtered_logs = []
        self.log_textbox.configure(state="normal")
        self.log_textbox.delete("1.0", tk.END)
        self.log_textbox.configure(state="disabled")
        self.logs_label.configure(text="Filters reset. Click 'Fetch Logs' to search the database.")