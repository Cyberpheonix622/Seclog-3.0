# modules/correlation_engine.py

import json
from datetime import datetime, timedelta

class CorrelationEngine:
    """
    Loads multi-step correlation rules and checks for complex attack patterns.
    """
    def __init__(self, rules_filepath="rules.json", db_handler=None):
        self.correlation_rules = self._load_rules(rules_filepath)
        self.db_handler = db_handler

    def _load_rules(self, filepath):
        """Loads only rules with type 'correlation'."""
        try:
            with open(filepath, 'r') as f:
                all_rules = json.load(f)
            # Filter for enabled, correlation-type rules
            corr_rules = [
                rule for rule in all_rules 
                if rule.get("enabled", False) and rule.get("type") == "correlation"
            ]
            print(f"Successfully loaded {len(corr_rules)} correlation rules.")
            return corr_rules
        except Exception as e:
            print(f"Error loading correlation rules: {e}")
            return []

    def check_correlations(self):
        """
        A simplified correlation check.
        For each rule, it checks if all steps occurred within the time window.
        """
        if not self.db_handler:
            return []

        print("\n--- Checking for Correlations ---")
        triggered_alerts = []

        for rule in self.correlation_rules:
            all_steps_found = True
            
            # Define the overall time window for the entire multi-step attack
            time_window = rule["time_window_minutes"]
            end_time = datetime.now()
            start_time = end_time - timedelta(minutes=time_window)
            
            print(f"Checking correlation rule: '{rule['rule_name']}'")

            # Check if logs for each step exist within the time window
            for step in rule["steps"]:
                log_count = self.db_handler.count_logs_for_rule(
                    logfile=step["logfile"],
                    conditions=step["conditions"],
                    start_time=start_time.strftime("%Y-%m-%d %H:%M:%S")
                )

                if log_count < step.get("threshold", 1):
                    all_steps_found = False
                    break # If one step is missing, the pattern is broken
            
            if all_steps_found:
                alert = {
                    "rule_name": rule["rule_name"],
                    "description": rule["description"],
                    "trigger_time": end_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "count": "N/A", # Count is complex in correlation, simplifying for now
                    "threshold": "N/A",
                    "time_window_minutes": time_window
                }
                triggered_alerts.append(alert)
        
        return triggered_alerts