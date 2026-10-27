from typing import Any


# SYSTEM UTILITIES SUBSYSTEM: SAFE ENVIRONMENT CONSTRUCTION
# This utility establishes a minimal, deterministic, zero-trust execution environment profile
# by sanitizing base environment variables and conditionally injecting GUI display contexts.
# [>] EXECUTING SAFE ENVIRONMENT CONSTRUCTION
def build_safe_environment(ctx: dict[str, Any], is_gui: bool = False) -> dict[str, str]:
    """
    Establishes a minimal, deterministic, zero-trust execution environment profile.

    Args:
        ctx (dict[str, Any]): Context dictionary containing user metadata, home path, and optional display context.
        is_gui (bool, optional): Flag indicating whether GUI execution variables should be injected. Defaults to False.

    Returns:
        dict[str, str]: A sanitized dictionary of environment variables for secure subprocess execution.
    """
    # BASE ENVIRONMENT DICTIONARY INITIALIZATION
    # Initializes a secure, minimal set of environment variables enforcing deterministic locale,
    # restricted PATH, and fallback home/tmp locations.
    safe_env: dict[str, str] = {
        "LC_ALL": "C",
        "PATH": "/usr/sbin:/usr/bin:/sbin:/bin",
        "HOME": str(ctx.get("home", "/tmp")),
        "TMPDIR": str(ctx.get("home", "/tmp")),
        "USER": str(ctx.get("user", "nobody")),
        "LANG": "en_US.UTF-8",
        "TERM": "xterm-256color",
    }

    # GUI CONTEXT INJECTION & DISPLAY CONFIGURATION
    # Conditionally integrates GUI display context variables, ozone platform hints,
    # and session type settings if GUI execution is enabled and display context is present.
    if is_gui and "display_context" in ctx:
        gui_vars: dict[str, str] = {
            str(k): str(v) for k, v in ctx["display_context"].items() if v
        }
        safe_env.update(gui_vars)
        safe_env["ELECTRON_OZONE_PLATFORM_HINT"] = "auto"
        safe_env["XDG_SESSION_TYPE"] = "wayland"

    return safe_env
