from .context import RuntimeContext

# Initialize default runtime contexts
runtime_context_1 = RuntimeContext(
    target_group="users",
    base_dir="~/.log/mkv-encode/system",
    max_log_days=7,
).bootstrap()

context = runtime_context_1.manifest
log_path = runtime_context_1.session_path

__all__ = [
    "context",
    "log_path",
]
