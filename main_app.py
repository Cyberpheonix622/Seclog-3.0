# main_app.py

import customtkinter as ctk
import tkinter as tk
import threading

from log_handler import LogHandler
from modules.database_handler import DatabaseHandler
import ui_components

class SecurityLogApp(ctk.CTk):
    """
    The main application class that ties the UI and the backend logic together.
    """
    def __init__(self):
        super().__init__()

        self.title("SecLog - Windows Security Log Viewer")
        self.geometry("1100x650")
        self.minsize(900, 500)

        # Initialize backend handlers
        self.log_handler = LogHandler()
        self.db_handler = DatabaseHandler()

        # --- Data Storage ---
        self.filtered_logs = []

        # --- Configure Grid Layout ---
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Create UI Elements ---
        ui_components.create_sidebar(self, self)
        ui_components.create_main_tabs(self, self)

    def search_logs(self):
        """
        Handles the 'Fetch Logs' button.
        It now syncs latest logs and then queries the entire database in a thread.
        """
        self.logs_label.configure(text="🔄 Syncing latest logs and searching database...")
        self.log_textbox.configure(state="normal")
        self.log_textbox.delete("1.0", tk.END)
        self.log_textbox.insert("1.0", "This may take a moment...")
        self.log_textbox.configure(state="disabled")

        # Get filter criteria from UI elements
        selected_log_type = self.log_type.get()
        log_sources = ["Security", "System", "Application"] if selected_log_type == "All" else [selected_log_type]
        start_date = self.start_date_entry.get().strip() or None
        end_date = self.end_date_entry.get().strip() or None
        keyword = self.filter_entry.get().strip() or None

        # Run the fetching and querying in a new thread to keep UI responsive
        threading.Thread(
            target=self._sync_and_query_thread,
            args=(log_sources, start_date, end_date, keyword),
            daemon=True
        ).start()

    def _sync_and_query_thread(self, log_sources, start_date, end_date, keyword):
        """
        Target for the background thread.
        Step 1: Fetch latest logs from Windows to ensure DB is up to date.
        Step 2: Query the entire database with the user's filters.
        """
        # Step 1: Sync latest logs. We fetch a limited number from each source.
        print("Syncing latest logs from Windows...")
        latest_logs, _ = self.log_handler.fetch_logs(log_sources, None, None, None)
        self.db_handler.insert_logs(latest_logs)
        
        # Step 2: Query the database with the user's filters.
        print("Querying the database...")
        queried_logs, counts = self.db_handler.query_logs(log_sources, start_date, end_date, keyword)
        
        # Schedule the UI update on the main thread
        self.after(0, self._update_ui_with_db_results, queried_logs, counts)

    def _update_ui_with_db_results(self, logs, counts):
        """Updates the entire UI with new log data from the database query."""
        self.filtered_logs = logs
        
        self.logs_label.configure(text=f"Logs Found in Database: {len(self.filtered_logs)} entries")
        
        # Update all parts of the UI
        ui_components.display_logs(self.log_textbox, self.filtered_logs)
        ui_components.update_summary_cards(self, len(self.filtered_logs), counts)
        ui_components.update_summary_tab(self, self.filtered_logs)
        ui_components.draw_event_graph(self.graph_frame, self.filtered_logs)

    # ... (start_real_time, stop_real_time, save, reset) ...
    def start_real_time_monitoring(self):
        """Handles the 'Start Real-Time' button click."""
        self.log_handler.start_monitoring(self._real_time_update_callback)
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.logs_label.configure(text="🔄 Real-Time Monitoring Started...")

    def stop_real_time_monitoring(self):
        """Handles the 'Stop Real-Time' button click."""
        self.log_handler.stop_monitoring()
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self.logs_label.configure(text="Real-Time Monitoring Stopped.")

    def _real_time_update_callback(self, new_logs, counts):
        """Callback for real-time monitor. Inserts new logs into DB and UI."""
        self.db_handler.insert_logs(new_logs)
        self.filtered_logs = new_logs + self.filtered_logs
        self._update_ui_with_db_results(self.filtered_logs, counts)
        
    def save_filtered_logs(self):
        """Handles the 'Export to CSV' button click."""
        self.log_handler.save_logs_to_csv(self.filtered_logs)

    def reset_filters(self):
        """Resets all filter fields and clears the log view."""
        self.start_date_entry.delete(0, tk.END)
        self.end_date_entry.delete(0, tk.END)
        self.filter_entry.delete(0, tk.END)
        self.log_type.set("All")
        
        self.filtered_logs = []
        self.log_textbox.configure(state="normal")
        self.log_textbox.delete("1.0", tk.END)
        self.log_textbox.configure(state="disabled")
        
        self.logs_label.configure(text="Filters reset. Click 'Fetch Logs' to search the database.")