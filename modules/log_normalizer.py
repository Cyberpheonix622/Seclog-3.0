# modules/log_normalizer.py

from datetime import datetime

class LogNormalizer:
    SEVERITY_KEYWORDS = {
        "error": "Critical", "fail": "Warning", "denied": "Warning",
        "warning": "Warning", "success": "Info", "information": "Info",
        "audit success": "Info", "audit failure": "Warning"
    }
    EVENT_TYPE_MAP = {
        "1": "Error", "2": "Warning", "4": "Information",
        "8": "Success Audit", "16": "Failure Audit"
    }

    def normalize(self, source_type, log_data):
        if source_type.lower() == "windows":
            return self._normalize_windows_log(log_data)
        # ... (other types if you add them) ...
        else:
            return self._normalize_generic_log(log_data)

    def _normalize_windows_log(self, log):
        try:
            timestamp = log.get("TimeGenerated")
            if isinstance(timestamp, datetime):
                timestamp = timestamp.strftime("%Y-%m-%d %H:%M:%S")

            event_type = self.EVENT_TYPE_MAP.get(str(log.get("EventType")), "Unknown")
            message = log.get("Message", "")
            severity = self._determine_severity(message, event_type)

            return {
                "timestamp": timestamp,
                "logfile": log.get("logfile", "Unknown"),  # 👈 **CHANGE: Add logfile field**
                "source": log.get("SourceName", "Unknown"),
                "event_id": str(log.get("EventID", "")),
                "event_type": event_type,
                "severity": severity,
                "message": message,
                "raw_log": log
            }
        except Exception as e:
            return {"error": f"Normalization failed: {e}", "raw_log": log}

    # ... (rest of the class is unchanged) ...
    def _normalize_generic_log(self, log):
        try:
            message = log.get("message") or log.get("msg") or str(log)
            severity = self._determine_severity(message)
            return {
                "timestamp": log.get("timestamp") or datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                "logfile": log.get("logfile", "Generic"),
                "source": log.get("source", "Generic"),
                "event_id": str(log.get("event_id", "N/A")),
                "event_type": log.get("event_type", "Unknown"),
                "severity": severity,
                "message": message,
                "raw_log": log
            }
        except Exception as e:
            return {"error": f"Generic normalization failed: {e}", "raw_log": log}

    def _determine_severity(self, message, event_type=None):
        msg_lower = message.lower()
        for key, sev in self.SEVERITY_KEYWORDS.items():
            if key in msg_lower:
                return sev
        if event_type in ("Error", "Failure Audit"):
            return "Critical"
        if event_type in ("Warning",):
            return "Warning"
        return "Info"