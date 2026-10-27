from .context import RuntimeContext

# Initialize default runtime contexts
runtime_context_1 = RuntimeContext(
    target_group="secure-note",
    base_dir="~/.log/secure-note/system",
    max_log_days=7,
).bootstrap()

runtime_context_2 = RuntimeContext(
    target_group="secure-note",
    base_dir="~/.log/secure-note/telemetry",
    max_log_days=7,
    skip_security_checks=True,
).bootstrap()

context = runtime_context_1.manifest
log_path = runtime_context_1.session_path
telemetry_path = runtime_context_2.session_path

__all__ = [
    "RuntimeContext",
    "runtime_context_1",
    "runtime_context_2",
    "context",
    "log_path",
    "telemetry_path",
]
