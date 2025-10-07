# modules/log_normalizer.py

from datetime import datetime

class LogNormalizer:
    """
    Converts raw logs from various sources (Windows, Syslog, etc.)
    into a consistent normalized structure for storage and analysis.
    """

    SEVERITY_KEYWORDS = {
        "error": "Critical",
        "fail": "Warning",
        "denied": "Warning",
        "warning": "Warning",
        "success": "Info",
        "information": "Info",
        "audit success": "Info",
        "audit failure": "Warning"
    }

    EVENT_TYPE_MAP = {
        "1": "Error",
        "2": "Warning",
        "4": "Information",
        "8": "Success Audit",
        "16": "Failure Audit"
    }

    def normalize(self, source_type, log_data):
        """
        Entry point — determines which normalization method to apply.
        """
        if source_type.lower() == "windows":
            return self.normalize_windows_log(log_data)
        elif source_type.lower() == "syslog":
            return self.normalize_syslog_message(log_data)
        else:
            return self.normalize_generic_log(log_data)

    # ---------------- WINDOWS EVENT LOGS ---------------- #
    def normalize_windows_log(self, log):
        """
        Normalize a single Windows event log dictionary.
        Expected keys: TimeGenerated, SourceName, EventID, EventType, Message
        """
        try:
            timestamp = log.get("TimeGenerated")
            if isinstance(timestamp, datetime):
                timestamp = timestamp.strftime("%Y-%m-%d %H:%M:%S")

            event_type = self.EVENT_TYPE_MAP.get(str(log.get("EventType")), "Unknown")
            message = log.get("Message", "")
            severity = self._determine_severity(message, event_type)

            return {
                "timestamp": timestamp,
                "source": log.get("SourceName", "Unknown"),
                "event_id": str(log.get("EventID", "")),
                "event_type": event_type,
                "severity": severity,
                "message": message,
                "raw_log": log
            }
        except Exception as e:
            return {"error": f"Normalization failed: {e}", "raw_log": log}

    # ---------------- SYSLOG ---------------- #
    def normalize_syslog_message(self, raw_message):
        """
        Parse a raw syslog message string and convert it into normalized structure.
        Example input: "<34>Oct 11 22:14:15 mymachine su: 'su root' failed"
        """
        try:
            parts = raw_message.split(" ", 4)
            if len(parts) < 5:
                raise ValueError("Invalid syslog format")

            timestamp = self._parse_syslog_time(parts[0:3])
            source = parts[3]
            message = parts[4]

            severity = self._determine_severity(message)
            return {
                "timestamp": timestamp,
                "source": source,
                "event_id": "N/A",
                "event_type": "Syslog",
                "severity": severity,
                "message": message,
                "raw_log": raw_message
            }
        except Exception as e:
            return {"error": f"Syslog normalization failed: {e}", "raw_log": raw_message}

    # ---------------- GENERIC ---------------- #
    def normalize_generic_log(self, log):
        """Fallback normalization for unknown log sources."""
        try:
            message = log.get("message") or log.get("msg") or str(log)
            severity = self._determine_severity(message)
            return {
                "timestamp": log.get("timestamp") or datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                "source": log.get("source", "Generic"),
                "event_id": str(log.get("event_id", "N/A")),
                "event_type": log.get("event_type", "Unknown"),
                "severity": severity,
                "message": message,
                "raw_log": log
            }
        except Exception as e:
            return {"error": f"Generic normalization failed: {e}", "raw_log": log}

    # ---------------- HELPERS ---------------- #
    def _parse_syslog_time(self, time_parts):
        try:
            month, day, time_str = time_parts
            timestamp = f"{datetime.utcnow().year} {month} {day} {time_str}"
            dt = datetime.strptime(timestamp, "%Y %b %d %H:%M:%S")
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

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
