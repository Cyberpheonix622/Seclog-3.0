# main_app.py

import customtkinter as ctk
import tkinter as tk
import threading

from log_handler import LogHandler
from modules.database_handler import DatabaseHandler
from modules.rule_engine import RuleEngine
from modules.alert_manager import AlertManager
from modules.correlation_engine import CorrelationEngine
import ui_components

class SecurityLogApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("SecLog - Windows Security Log Viewer")
        self.geometry("1200x700")
        self.minsize(1000, 600)

        # Initialize backend handlers
        self.log_handler = LogHandler()
        self.db_handler = DatabaseHandler()
        self.rule_engine = RuleEngine(db_handler=self.db_handler)
        self.alert_manager = AlertManager()
        self.correlation_engine = CorrelationEngine(db_handler=self.db_handler)

        self.filtered_logs = []
        self.incidents = []
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        ui_components.create_sidebar(self, self)
        ui_components.create_main_tabs(self, self)
        self.refresh_incidents()

    def _sync_and_query_thread(self, log_sources, start_date, end_date, keyword):
        print("Syncing latest logs...")
        latest_logs, _ = self.log_handler.fetch_logs(log_sources, None, None, None)
        self.db_handler.insert_logs(latest_logs)
        print("Querying database...")
        queried_logs, counts = self.db_handler.query_logs(log_sources, start_date, end_date, keyword)
        
        # --- Run both alert engines ---
        new_alerts = self.rule_engine.check_alerts()
        new_correlation_alerts = self.correlation_engine.check_correlations()
        all_new_alerts = new_alerts + new_correlation_alerts
        if all_new_alerts:
            self.alert_manager.process_new_alerts(all_new_alerts)
            print(f"🚨 Processed {len(all_new_alerts)} new alerts!")
        
        self.after(0, self._update_ui, queried_logs, counts)

    def _update_ui(self, logs, counts):
        self.filtered_logs = logs
        self.logs_label.configure(text=f"Logs Found: {len(self.filtered_logs)} entries")
        ui_components.display_alerts(self, self.alert_manager.get_active_alerts())
        ui_components.display_logs(self.log_textbox, self.filtered_logs)
        ui_components.update_summary_cards(self, len(self.filtered_logs), counts)
        ui_components.update_summary_tab(self, self.filtered_logs)
        ui_components.draw_event_graph(self.graph_frame, self.filtered_logs)
        self.refresh_incidents()

    # 🔹 UPDATED REAL-TIME CALLBACK with detailed logging 🔹
    def _real_time_update_callback(self, new_logs, counts):
        """
        Callback for the monitor. Inserts new logs, checks all alert engines, and updates UI.
        """
        if not new_logs:
            return

        print(f"\n[Real-Time] Received {len(new_logs)} new logs.")
        self.db_handler.insert_logs(new_logs)

        print("[Real-Time] Running alert engines...")
        new_simple_alerts = self.rule_engine.check_alerts()
        new_correlation_alerts = self.correlation_engine.check_correlations()
        
        print(f"[Real-Time] Found {len(new_simple_alerts)} simple alerts.")
        print(f"[Real-Time] Found {len(new_correlation_alerts)} correlation alerts.")

        all_new_alerts = new_simple_alerts + new_correlation_alerts
        if all_new_alerts:
            self.alert_manager.process_new_alerts(all_new_alerts)
            print(f"🚨 [Real-Time] Processed {len(all_new_alerts)} new alerts!")

        # Prepend new logs to the currently displayed logs for immediate feedback
        self.filtered_logs = new_logs + self.filtered_logs
        
        # Schedule a full UI refresh
        self.after(0, self._update_ui, self.filtered_logs, counts)

    # ... (rest of the file is unchanged) ...
    def create_incident_from_alert(self, alert):
        incident_id = self.db_handler.create_incident(alert)
        if incident_id:
            self.alert_manager.remove_alert(alert)
            self._update_ui(self.filtered_logs, {})

    def search_logs(self):
        self.logs_label.configure(text="🔄 Syncing & Searching...")
        threading.Thread(target=self._sync_and_query_thread, args=(
            ["Security", "System", "Application"] if self.log_type.get() == "All" else [self.log_type.get()],
            self.start_date_entry.get().strip() or None,
            self.end_date_entry.get().strip() or None,
            self.filter_entry.get().strip() or None
        ), daemon=True).start()

    def refresh_incidents(self):
        self.incidents = self.db_handler.get_all_incidents()
        ui_components.display_incidents(self, self.incidents)

    def update_incident_status(self, incident_id, new_status):
        self.db_handler.update_incident_status(incident_id, new_status)
        self.refresh_incidents()

    def start_real_time_monitoring(self):
        self.log_handler.start_monitoring(self._real_time_update_callback)
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")

    def stop_real_time_monitoring(self):
        self.log_handler.stop_monitoring()
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        
    def save_filtered_logs(self):
        self.log_handler.save_logs_to_csv(self.filtered_logs)

    def reset_filters(self):
        self.start_date_entry.delete(0, tk.END)
        self.end_date_entry.delete(0, tk.END)
        self.filter_entry.delete(0, tk.END)
        self.log_type.set("All")