import customtkinter as ctk
import tkinter as tk
import threading

from log_handler import LogHandler
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

        # Initialize the backend log handler
        self.log_handler = LogHandler()

        # --- Data Storage ---
        self.all_logs = []
        self.filtered_logs = []

        # --- Configure Grid Layout ---
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Create UI Elements by calling functions from ui_components ---
        # The 'self' is passed so the component functions can attach widgets
        # (like entry fields and buttons) directly to the app instance.
        ui_components.create_sidebar(self, self)
        ui_components.create_main_tabs(self, self)

    def search_logs(self):
        """
        Handles the 'Fetch Logs' button click.
        Fetches logs in a separate thread to keep the UI responsive.
        """
        self.logs_label.configure(text="🔄 Fetching and filtering logs...")
        self.log_textbox.configure(state="normal")
        self.log_textbox.delete("1.0", tk.END)
        self.log_textbox.insert("1.0", "Searching logs... this may take a moment.")
        self.log_textbox.configure(state="disabled")

        # Get filter criteria from UI elements
        selected_log_type = self.log_type.get()
        log_types_to_fetch = ["Security", "System", "Application"] if selected_log_type == "All" else [selected_log_type]
        start_date = self.start_date_entry.get().strip()
        end_date = self.end_date_entry.get().strip()
        keyword = self.filter_entry.get().strip()

        # Run the fetching in a new thread
        threading.Thread(
            target=self._fetch_logs_thread_target,
            args=(log_types_to_fetch, start_date, end_date, keyword),
            daemon=True
        ).start()

    def _fetch_logs_thread_target(self, log_types, start_date, end_date, keyword):
        """Target function for the log fetching thread."""
        logs, counts = self.log_handler.fetch_logs(log_types, start_date, end_date, keyword)
        
        # Schedule the UI update on the main thread
        self.after(0, self._update_ui_with_fetched_logs, logs, counts)

    def _update_ui_with_fetched_logs(self, logs, counts):
        """Updates the entire UI with new log data. Must be run on the main thread."""
        self.all_logs = logs
        self.filtered_logs = logs
        
        self.logs_label.configure(text=f"Logs Loaded: {len(self.filtered_logs)} entries found")
        
        # Update all parts of the UI
        ui_components.display_logs(self.log_textbox, self.filtered_logs)
        ui_components.update_summary_cards(self, len(self.filtered_logs), counts)
        ui_components.update_summary_tab(self, self.filtered_logs)
        ui_components.draw_event_graph(self.graph_frame, self.filtered_logs)

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

    def _real_time_update_callback(self, logs, counts):
        """Callback function for the monitor to send data back to the UI."""
        # This function is called from the monitoring thread, so we must
        # schedule the UI update on the main thread using self.after()
        self.after(0, self._update_ui_with_fetched_logs, logs, counts)

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
        
        self.logs_label.configure(text="Filters reset. Click 'Fetch Logs' to reload.")
