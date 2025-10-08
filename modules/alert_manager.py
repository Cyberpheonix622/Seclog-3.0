# modules/alert_manager.py

class AlertManager:
    """Manages the lifecycle of alerts."""
    def __init__(self):
        self.active_alerts = []

    def process_new_alerts(self, new_alerts):
        """Adds new, unique alerts to the active list."""
        for new_alert in new_alerts:
            # Simple check to avoid adding the exact same alert again
            if new_alert not in self.active_alerts:
                self.active_alerts.append(new_alert)
        
        # Newest alerts first
        self.active_alerts.sort(key=lambda x: x['trigger_time'], reverse=True)

    def get_active_alerts(self):
        """Returns the current list of active alerts."""
        return self.active_alerts

    def remove_alert(self, alert_to_remove):
        """Removes an alert, typically after it's converted to an incident."""
        self.active_alerts = [alert for alert in self.active_alerts if alert != alert_to_remove]