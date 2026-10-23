from datetime import datetime


# SESSION LOGGING & FILE I/O PERSISTENCE ENGINE
# This utility manages background session logging, precise timestamp generation,
# and safe file appending with defensive error handling to protect main execution threads.
# [>] EXECUTING SESSION LOG COMMIT
def commit_log(log_path: str | None, log_symbol: str, message: str) -> None:
    """
    Manages background session logging, timestamp generation, and safe file writing with defensive error handling.

    Args:
        log_path: Optional file system path string where log entries are written.
        log_symbol: Symbol or prefix character identifying the log category or status.
        message: The content string to record in the log file.
    """
    # LOG PATH EXISTENCE CHECK
    # Verifies whether a valid log file path has been provided before attempting file I/O operations.
    if log_path:
        try:
            # FILE APPEND & TIMESTAMP GENERATION
            # Opens the target log file in append mode, generates a current time string,
            # and writes the formatted log entry safely.
            with open(log_path, "a", encoding="utf-8") as f:
                ts = datetime.now().strftime("%H:%M:%S")
                f.write(f"[{ts}] {log_symbol} {message}\n")
        except Exception:
            # DEFENSIVE EXCEPTION CATCH & SILENT FALLBACK
            # Catches any file system or write errors, failing silently to prevent background
            # logging failures from crashing the primary UI or application flow.
            pass
