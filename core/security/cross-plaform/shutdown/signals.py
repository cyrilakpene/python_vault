import signal

# SYSTEM UTILITIES SUBSYSTEM: CROSS-PLATFORM TERMINATION SIGNALS
# This constant tuple defines standard cross-platform process termination signals
# used for graceful shutdown and interrupt handling.
# [>] INITIALIZING CROSS-PLATFORM TERMINATION SIGNALS
default_signals: tuple[signal.Signals, ...] = (
    signal.SIGINT,  # Keyboard interrupt (Ctrl+C)
    signal.SIGTERM,  # Standard termination request
)

# SYSTEM UTILITIES SUBSYSTEM: UNIX HUP INTEGRATION & TERMINAL DISCONNECT SIGNAL
# Conditionally integrates the SIGHUP signal into the default termination signals tuple
# to ensure graceful shutdown handling upon Unix terminal disconnection events.
# [>] CONFIGURING UNIX TERMINAL DISCONNECT SIGNAL
if hasattr(signal, "SIGHUP"):
    # HUP SIGNAL DETECTION & INCLUSION
    # Verifies platform support for SIGHUP and extends the default signals tuple
    # with terminal hang-up handling.
    default_signals += (signal.SIGHUP,)
