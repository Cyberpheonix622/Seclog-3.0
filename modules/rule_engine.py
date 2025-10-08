# modules/rule_engine.py

import json
from datetime import datetime, timedelta

class RuleEngine:
    """
    Loads SIMPLE alert rules from a JSON file and checks them against the log database.
    """
    def __init__(self, rules_filepath="rules.json", db_handler=None):
        self.rules = self._load_rules(rules_filepath)
        self.db_handler = db_handler

    def _load_rules(self, filepath):
        """Loads and validates rules from a JSON file."""
        try:
            with open(filepath, 'r') as f:
                rules = json.load(f)
                
            # 🔹 THE FIX: Only load rules that are enabled AND are NOT correlation rules. 🔹
            enabled_rules = [
                rule for rule in rules 
                if rule.get("enabled", False) and rule.get("type") != "correlation"
            ]

            print(f"Successfully loaded {len(enabled_rules)} enabled simple rules.")
            return enabled_rules
        except FileNotFoundError:
            print(f"Error: Rules file not found at '{filepath}'.")
            return []
        except json.JSONDecodeError:
            print(f"Error: Could not decode JSON from '{filepath}'. Check for syntax errors.")
            return []

    def check_alerts(self):
        """
        Iterates through all enabled simple rules and checks them against the database.
        Returns a list of triggered alerts.
        """
        if not self.db_handler:
            print("Error: Database handler is not configured.")
            return []
        
        triggered_alerts = []

        for rule in self.rules:
            time_window = rule["aggregation"]["time_window_minutes"]
            threshold = rule["aggregation"]["threshold"]
            
            start_time = datetime.now() - timedelta(minutes=time_window)
            start_time_str = start_time.strftime("%Y-%m-%d %H:%M:%S")

            log_count = self.db_handler.count_logs_for_rule(
                logfile=rule["logfile"],
                conditions=rule["conditions"],
                start_time=start_time_str
            )

            # This print statement is removed from the final version for cleaner output,
            # but is useful for debugging.
            # print(f"Checking rule '{rule['rule_name']}': Found {log_count} matching logs (Threshold: {threshold})")

            if log_count >= threshold:
                alert = {
                    "rule_name": rule["rule_name"],
                    "description": rule["description"],
                    "trigger_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "count": log_count,
                    "threshold": threshold,
                    "time_window_minutes": time_window
                }
                triggered_alerts.append(alert)
        
        return triggered_alerts