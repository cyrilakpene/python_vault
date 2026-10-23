# Comprehensive Reference Guide: The `report_status()` Engine

The `report_status()` function implements a character-based terminal feedback and background logging system. By utilizing a localized mapping of symbolic status indicators, it ensures applications provide granular, parseable visual feedback and persistent logs without polluting the global namespace.

---

## 1. Core Function Signature & Parameters

```python
def report_status(
    state: str,
    message: str,
    stream: TextIO | None = None,
    log_path: str | None = None,
    is_verbose: bool = False,
    silent: bool = False,
    is_loop: float | int | bool = False,
    step: int | None = None,
) -> None:
```

* **`state`**: The symbolic key (e.g., `'done'`, `'fail'`, `'info'`) representing the event state.
* **`message`**: The descriptive text rendered alongside the status symbol.
* **`stream`**: Target IO stream for terminal output (defaults to `sys.stdout`, or `sys.stderr` for errors).
* **`log_path`**: File system path for background session logging.
* **`is_verbose`**: Toggle for high-density reporting; suppresses `'debug'` calls if `False`.
* **`silent`**: Global override; if `True`, suppresses terminal output while honoring file logs.
* **`is_loop`**: Throttle interval. Acts as seconds for time-based evaluation, or as the milestone step frequency when `step` is provided.
* **`step`**: Optional current execution index (e.g., chunk or row count) enabling modulo-based milestone throttling when paired with `is_loop`.

---

## 2. Symbolic State & Mapping Matrix

The engine maps specific string inputs to standardized terminal symbols via an internal `status_map`:

| State Key | Symbol Rendered | Description / Intent |
| :--- | :--- | :--- |
| `"task"` | `[>]` | Start of a task or directional flow |
| `"info"` | `[~]` | Contextual information or general flow |
| `"log_info"` | ` [~]` | Internal logging representation variant |
| `"warn"` | `[!]` | Attention or warning required |
| `"item"` | `  [-]` | Sub-details or nested list items |
| `"done"` | `[+]` | Success confirmation (bypasses throttles and cleans cache) |
| `"fail"` | `[x]` | Failure state (bypasses throttles, routes to stderr, cleans cache) |
| `"input"` | `[?]` | User interaction prompt |
| `"debug"` | ` [d]` | Technical detail (suppressed unless `is_verbose=True`) |
| `"proc"` | `[*]` | Active or ongoing processing state |

*Note: Any unrecognized state gracefully defaults to `[ ]` to prevent runtime crashes.*

---

## 3. Execution Pipeline & Gates

The internal architecture processes messages through multiple defensive and functional gates:

1. **Throttling Gate (`is_loop` & `step`)**: 
   * Prevents terminal flooding during recurring execution loops.
   * Supports **Step-based throttling** via modulo math against `step` when paired with `is_loop` (always fires on step 0).
   * Supports **Temporal throttling** using time-deltas (`time.time()`) against an internal module-level cache (`_LOOP_CACHE`) when `step` is omitted.
   * **Terminal Bypass**: States like `'done'` and `'fail'` always bypass the throttle gate.
2. **Persistence Gate (`log_path`)**: 
   * Appends timestamped events (`[HH:MM:SS] [symbol] message`) to a target file using UTF-8 encoding.
   * Fails silently if the filesystem is read-only or full to prioritize main terminal output flow.
3. **Verbosity Gate (`is_verbose`)**: 
   * Suppresses `'debug'` messages unless `is_verbose=True`.
4. **Silence Gate (`silent`)**: 
   * Suppresses terminal output entirely when active (unless overridden by verbosity) while still allowing file logging.
5. **Stream Resolution (`stream`)**: 
   * Automatically routes `'warn'` and `'fail'` states to `sys.stderr`, and all other states to `sys.stdout` if no explicit stream is provided.

---

## 4. Practical Code Examples

### Basic Status Reporting
```python
from report_status import report_status

# Standard task and success reporting
report_status("task", "Initializing application database...")
report_status("done", "Database connection established successfully.")
```

### Error Reporting (Auto-Routed to Stderr)
```python
# Automatically routes to sys.stderr
report_status("warn", "Configuration file missing optimal parameters.")
report_status("fail", "Critical failure: Could not bind to port 8080.")
```

### Verbose Debug Logging
```python
# Suppressed unless is_verbose=True is passed
report_status("debug", "Memory allocation size: 512MB", is_verbose=True)
```

### Background Session File Logging
```python
# Writes a timestamped log entry to disk while printing to the terminal
report_status("info", "User authentication token generated.", log_path="session.log")
```

### Step-Based Loop Throttling
```python
# Fires on step 0, then every 10 steps, and always on 'done'
for i in range(101):
    report_status("proc", f"Processing batch chunk {i}", is_loop=10, step=i)

report_status("done", "Batch processing complete.")
```

### Temporal-Based Throttling
```python
import time

# Throttles repeated info messages to fire at most once every 2 seconds
for _ in range(5):
    report_status("info", "Waiting for network handshake...", is_loop=2)
    time.sleep(1)
```