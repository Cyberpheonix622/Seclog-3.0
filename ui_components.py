# ui_components.py

import customtkinter as ctk
import tkinter as tk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from collections import Counter
from datetime import datetime

class LoginWindow(ctk.CTkToplevel):
    """
    A separate top-level window for user login.
    """
    def __init__(self, master, auth_instance, on_success_callback):
        super().__init__(master)

        self.auth = auth_instance
        self.on_success = on_success_callback
        
        self.title("SecLog - Login")
        self.geometry("350x300")
        self.transient(master) # Keep login window on top of the main app
        self.grab_set() # Modal behavior: block interaction with the main window
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self, text="SecLog Authentication", font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, pady=(20, 15))

        self.username_entry = ctk.CTkEntry(self, placeholder_text="Username", width=250)
        self.username_entry.grid(row=1, column=0, pady=10)

        self.password_entry = ctk.CTkEntry(self, placeholder_text="Password", show="*", width=250)
        self.password_entry.grid(row=2, column=0, pady=10)
        self.password_entry.bind("<Return>", self._login_event)

        self.login_button = ctk.CTkButton(self, text="Login", command=self._login_event, width=250, height=40)
        self.login_button.grid(row=3, column=0, pady=20)

        self.status_label = ctk.CTkLabel(self, text="", text_color="red")
        self.status_label.grid(row=4, column=0, pady=(0, 10))
        
        # Center the window
        self.after(100, lambda: self.geometry(f"350x300+{master.winfo_screenwidth()//2-175}+{master.winfo_screenheight()//2-150}"))

    def _login_event(self, event=None):
        """Handles the login button click or Enter key press."""
        username = self.username_entry.get()
        password = self.password_entry.get()

        if self.auth.check_password(username, password):
            print("Login successful!")
            self.destroy() # Close the login window
            self.on_success() # Call the success callback
        else:
            self.status_label.configure(text="Invalid username or password.")

    def _on_closing(self):
        """Handles the event when the login window is closed via the 'X' button."""
        print("Login cancelled by user.")
        self.master.destroy() # Close the entire application

# ... (The rest of the file: create_sidebar, create_main_tabs, etc., is unchanged) ...
def create_sidebar(parent, app_instance):
    sidebar = ctk.CTkFrame(parent, width=220, corner_radius=0)
    sidebar.grid(row=0, column=0, sticky="ns")
    sidebar.grid_rowconfigure(9, weight=1)
    ctk.CTkLabel(sidebar, text="🔐 SecLog", font=ctk.CTkFont(size=22, weight="bold")).grid(row=0, column=0, pady=(25, 15))
    app_instance.start_button = ctk.CTkButton(sidebar, text="🚨 Start Real-Time", command=app_instance.start_real_time_monitoring, height=40)
    app_instance.start_button.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
    app_instance.stop_button = ctk.CTkButton(sidebar, text="⛔ Stop Real-Time", command=app_instance.stop_real_time_monitoring, height=40, state="disabled")
    app_instance.stop_button.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
    app_instance.log_type = ctk.StringVar(value="All")
    log_type_menu = ctk.CTkOptionMenu(sidebar, values=["All", "Security", "System", "Application"], variable=app_instance.log_type)
    log_type_menu.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
    app_instance.start_date_entry = ctk.CTkEntry(sidebar, placeholder_text="Start Date (YYYY-MM-DD)")
    app_instance.start_date_entry.grid(row=4, column=0, padx=20, pady=(10, 5), sticky="ew")
    app_instance.end_date_entry = ctk.CTkEntry(sidebar, placeholder_text="End Date (YYYY-MM-DD)")
    app_instance.end_date_entry.grid(row=5, column=0, padx=20, pady=(0, 10), sticky="ew")
    app_instance.filter_entry = ctk.CTkEntry(sidebar, placeholder_text="🔎 Keyword")
    app_instance.filter_entry.grid(row=6, column=0, padx=20, pady=(10, 5), sticky="ew")
    ctk.CTkButton(sidebar, text="🔍 Fetch Logs", command=app_instance.search_logs, height=40).grid(row=7, column=0, padx=20, pady=10, sticky="ew")
    ctk.CTkButton(sidebar, text="🔄 Reset Filters", command=app_instance.reset_filters, height=40).grid(row=8, column=0, padx=20, pady=10, sticky="ew")
    ctk.CTkButton(sidebar, text="💾 Export to CSV", command=app_instance.save_filtered_logs, height=40).grid(row=9, column=0, padx=20, pady=10, sticky="ew")
    ctk.CTkButton(sidebar, text="🌓 Toggle Theme", command=toggle_theme, height=40).grid(row=12, column=0, padx=20, pady=10, sticky="ew")
    ctk.CTkLabel(sidebar, text="v1.2", font=ctk.CTkFont(size=12, slant="italic")).grid(row=17, column=0, pady=(10, 10))

def create_main_tabs(parent, app_instance):
    tabs = ctk.CTkTabview(parent, corner_radius=10)
    tabs.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
    tabs.add("Dashboard")
    tabs.add("Logs")
    tabs.add("Summary")
    tabs.add("Alerts")
    incidents_tab = tabs.add("Incidents")
    setup_dashboard_tab(tabs.tab("Dashboard"), app_instance)
    setup_logs_tab(tabs.tab("Logs"), app_instance)
    setup_summary_tab(tabs.tab("Summary"), app_instance)
    setup_alerts_tab(tabs.tab("Alerts"), app_instance)
    setup_incidents_tab(incidents_tab, app_instance)

def setup_dashboard_tab(tab, app_instance):
    tab.grid_columnconfigure((0, 1, 2), weight=1)
    tab.grid_rowconfigure(2, weight=1)
    app_instance.total_logs_card = ctk.CTkLabel(tab, text="📊 Total Logs: 0", font=ctk.CTkFont(size=16, weight="bold"))
    app_instance.total_logs_card.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
    app_instance.security_card = ctk.CTkLabel(tab, text="🔐 Security: 0", font=ctk.CTkFont(size=14))
    app_instance.security_card.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
    app_instance.system_card = ctk.CTkLabel(tab, text="⚙️ System: 0", font=ctk.CTkFont(size=14))
    app_instance.system_card.grid(row=0, column=2, padx=10, pady=10, sticky="ew")
    app_instance.application_card = ctk.CTkLabel(tab, text="🧩 Application: 0", font=ctk.CTkFont(size=14))
    app_instance.application_card.grid(row=1, column=0, columnspan=3, padx=10, pady=(0, 10), sticky="ew")
    app_instance.graph_frame = ctk.CTkFrame(tab, height=250)
    app_instance.graph_frame.grid(row=2, column=0, columnspan=3, padx=10, pady=(5, 10), sticky="nsew")

def setup_logs_tab(tab, app_instance):
    tab.grid_columnconfigure(0, weight=1)
    tab.grid_rowconfigure(1, weight=1)
    app_instance.logs_label = ctk.CTkLabel(tab, text="Click 'Fetch Logs' to begin", font=ctk.CTkFont(size=18, weight="bold"))
    app_instance.logs_label.grid(row=0, column=0, pady=(10, 5))
    app_instance.log_textbox = ctk.CTkTextbox(tab, wrap="none", corner_radius=8, font=("Courier New", 12))
    app_instance.log_textbox.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
    app_instance.log_textbox.tag_config("Info", foreground="#5cb85c")
    app_instance.log_textbox.tag_config("Warning", foreground="#f0ad4e")
    app_instance.log_textbox.tag_config("Critical", foreground="#d9534f")

def setup_summary_tab(tab, app_instance):
    tab.grid_columnconfigure((0, 1, 2), weight=1)
    tab.grid_rowconfigure(0, weight=1)
    app_instance.event_id_summary_frame = ctk.CTkScrollableFrame(tab, label_text="Event ID Summary")
    app_instance.event_id_summary_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
    app_instance.source_summary_frame = ctk.CTkScrollableFrame(tab, label_text="Source Summary")
    app_instance.source_summary_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
    app_instance.event_type_summary_frame = ctk.CTkScrollableFrame(tab, label_text="Event Type Summary")
    app_instance.event_type_summary_frame.grid(row=0, column=2, padx=10, pady=10, sticky="nsew")

def setup_alerts_tab(tab, app_instance):
    tab.grid_columnconfigure(0, weight=1)
    tab.grid_rowconfigure(0, weight=1)
    app_instance.alerts_frame = ctk.CTkScrollableFrame(tab, label_text="Triggered Alerts")
    app_instance.alerts_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

def setup_incidents_tab(tab, app_instance):
    tab.grid_columnconfigure(0, weight=1)
    tab.grid_rowconfigure(0, weight=1)
    app_instance.incidents_frame = ctk.CTkScrollableFrame(tab, label_text="Managed Incidents")
    app_instance.incidents_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

def display_alerts(app_instance, alerts_list):
    alerts_frame = app_instance.alerts_frame
    for widget in alerts_frame.winfo_children(): widget.destroy()
    if not alerts_list:
        ctk.CTkLabel(alerts_frame, text="No alerts triggered.").pack(pady=10)
        return
    for alert in reversed(alerts_list):
        alert_item_frame = ctk.CTkFrame(alerts_frame, border_width=1, border_color="red")
        alert_item_frame.pack(fill="x", expand=True, padx=5, pady=5)
        info_frame = ctk.CTkFrame(alert_item_frame)
        info_frame.pack(side="left", fill="x", expand=True, padx=10, pady=5)
        rule_name = alert.get('rule_name', 'Unknown Rule')
        ctk.CTkLabel(info_frame, text=f"🚨 {rule_name}", font=ctk.CTkFont(weight="bold")).pack(anchor="w")
        ctk.CTkLabel(info_frame, text=f"Time: {alert.get('trigger_time', 'N/A')}").pack(anchor="w")
        ctk.CTkButton(alert_item_frame, text="Create Incident", command=lambda a=alert: app_instance.create_incident_from_alert(a)).pack(side="right", padx=10)

def display_incidents(app_instance, incidents_list):
    incidents_frame = app_instance.incidents_frame
    for widget in incidents_frame.winfo_children(): widget.destroy()
    if not incidents_list:
        ctk.CTkLabel(incidents_frame, text="No incidents created.").pack(pady=10)
        return
    status_colors = {"Open": "red", "Acknowledged": "orange", "Closed": "green"}
    for incident in incidents_list:
        incident_id = incident.get('id')
        status = incident.get('status', 'Open')
        item_frame = ctk.CTkFrame(incidents_frame, border_width=1, border_color=status_colors.get(status, "gray"))
        item_frame.pack(fill="x", expand=True, padx=5, pady=5)
        info_frame = ctk.CTkFrame(item_frame)
        info_frame.pack(side="left", fill="x", expand=True, padx=10, pady=5)
        ctk.CTkLabel(info_frame, text=f"Incident #{incident_id}: {incident.get('rule_name')}", font=ctk.CTkFont(weight="bold")).pack(anchor="w")
        ctk.CTkLabel(info_frame, text=f"Created: {incident.get('trigger_time')}", text_color="gray").pack(anchor="w")
        ctk.CTkLabel(info_frame, text=f"Status: {status}").pack(anchor="w")
        btn_frame = ctk.CTkFrame(item_frame)
        btn_frame.pack(side="right", padx=10)
        if status == "Open":
            ctk.CTkButton(btn_frame, text="Acknowledge", width=100, command=lambda i=incident_id: app_instance.update_incident_status(i, "Acknowledged")).pack(pady=2)
        if status == "Acknowledged":
            ctk.CTkButton(btn_frame, text="Close Incident", width=100, command=lambda i=incident_id: app_instance.update_incident_status(i, "Closed")).pack(pady=2)

def toggle_theme():
    current = ctk.get_appearance_mode()
    ctk.set_appearance_mode("Light" if current == "Dark" else "Dark")

def display_logs(textbox, log_list):
    textbox.configure(state="normal")
    textbox.delete("1.0", tk.END)
    if not log_list:
        textbox.insert(tk.END, "No logs found matching your criteria.")
    else:
        for log in log_list:
            line = f"[{log.get('timestamp')}] [{log.get('severity', 'Info')}] {log.get('source')} (ID {log.get('event_id')}): {log.get('message')}\n"
            severity = log.get('severity', 'Info')
            textbox.insert(tk.END, line, severity)
    textbox.see("1.0")
    textbox.configure(state="disabled")

def update_summary_cards(app_instance, total_logs_count, counts_by_type):
    app_instance.total_logs_card.configure(text=f"📊 Total Logs: {total_logs_count}")
    app_instance.security_card.configure(text=f"🔐 Security: {counts_by_type.get('Security', 0)}")
    app_instance.system_card.configure(text=f"⚙️ System: {counts_by_type.get('System', 0)}")
    app_instance.application_card.configure(text=f"🧩 Application: {counts_by_type.get('Application', 0)}")

def update_summary_tab(app_instance, logs):
    frames = [app_instance.event_id_summary_frame, app_instance.source_summary_frame, app_instance.event_type_summary_frame]
    for frame in frames:
        for widget in frame.winfo_children():
            widget.pack_forget()
            widget.destroy()
    if not logs: return
    event_ids = Counter(log.get("event_id") for log in logs)
    sources = Counter(log.get("source") for log in logs)
    event_types = Counter(log.get("event_type") for log in logs)
    for eid, count in event_ids.most_common(20):
        label = ctk.CTkLabel(app_instance.event_id_summary_frame, text=f"ID {eid}: {count} events", anchor="w")
        label.pack(fill="x", padx=5, pady=2)
    for source, count in sources.most_common(20):
        label = ctk.CTkLabel(app_instance.source_summary_frame, text=f"{source}: {count} events", anchor="w")
        label.pack(fill="x", padx=5, pady=2)
    for etype, count in event_types.most_common(20):
        label = ctk.CTkLabel(app_instance.event_type_summary_frame, text=f"{etype}: {count} events", anchor="w")
        label.pack(fill="x", padx=5, pady=2)

def draw_event_graph(parent_frame, logs):
    for widget in parent_frame.winfo_children(): widget.destroy()
    if not logs:
        ctk.CTkLabel(parent_frame, text="No data to display.").pack(expand=True)
        return
    try:
        timestamps = [datetime.strptime(log['timestamp'], "%Y-%m-%d %H:%M:%S") for log in logs if 'timestamp' in log]
        if not timestamps:
             ctk.CTkLabel(parent_frame, text="No timestamp data for graph.").pack(expand=True)
             return
        time_bins = [ts.strftime("%Y-%m-%d %H:00") for ts in timestamps]
        time_counts = Counter(time_bins)
        sorted_times = sorted(time_counts.keys())[-24:]
        counts = [time_counts[t] for t in sorted_times]
        short_labels = [t.split(' ')[1] for t in sorted_times]
        fig = Figure(figsize=(8, 4), dpi=100)
        ax = fig.add_subplot(111)
        bar_color = "#4e73df" if ctk.get_appearance_mode() == "Dark" else "#3366cc"
        ax.bar(short_labels, counts, color=bar_color)
        bg_color = "#2b2b2b" if ctk.get_appearance_mode() == "Dark" else "#f0f0f0"
        text_color = "white" if ctk.get_appearance_mode() == "Dark" else "black"
        fig.patch.set_facecolor(bg_color)
        ax.set_facecolor(bg_color)
        ax.xaxis.label.set_color(text_color)
        ax.yaxis.label.set_color(text_color)
        ax.title.set_color(text_color)
        ax.tick_params(axis='x', colors=text_color, rotation=45)
        ax.tick_params(axis='y', colors=text_color)
        ax.set_title("Event Count Over Time (Last 24 Hours)")
        ax.set_xlabel("Time (Hour of Day)")
        ax.set_ylabel("Number of Events")
        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=parent_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)
    except Exception as e:
        print(f"Error drawing graph: {e}")
        ctk.CTkLabel(parent_frame, text=f"Could not draw graph:\n{e}").pack(expand=True)