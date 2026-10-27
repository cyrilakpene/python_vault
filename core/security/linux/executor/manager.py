import pty
import sys
import termios
import tty
import os
from contextlib import contextmanager
from typing import Any, Generator


# SYSTEM UTILITIES SUBSYSTEM: PTY PAIR ALLOCATION
# This utility allocates and returns a new pseudo-terminal master and slave file descriptor pair
# for secure interactive subprocess execution.
# [>] EXECUTING PTY PAIR ALLOCATION
def allocate_pty_pair() -> tuple[int, int]:
    """
    Allocates and returns a pseudo-terminal (master_fd, slave_fd) pair.

    Returns:
        tuple[int, int]: A tuple containing the master and slave file descriptors `(master_fd, slave_fd)`.

    Raises:
        OSError: If the operating system fails to allocate a new pseudo-terminal pair.
    """
    # PTY PAIR GENERATION
    # Interfaces with the operating system pseudo-terminal module to open a new master/slave pair.
    return pty.openpty()


# SYSTEM UTILITIES SUBSYSTEM: PTY ECHO DISABLEMENT
# This utility clears the ECHO flag in terminal local control attributes for the PTY slave descriptor
# to prevent terminal echo loops during interactive command execution.
# [>] EXECUTING PTY ECHO DISABLEMENT
def disable_pty_echo(slave_fd: int) -> None:
    """
    Clears the ECHO flag in terminal local control attributes for the slave descriptor.

    Args:
        slave_fd (int): The PTY slave file descriptor to modify.

    Returns:
        None
    """
    # TERMINAL ATTRIBUTE RETRIEVAL & MODIFICATION
    # Attempts to retrieve current terminal settings for the slave descriptor,
    # clears the ECHO bit in the local flags (lflags) array index, and applies changes immediately.
    try:
        slave_attrs = termios.tcgetattr(slave_fd)
        slave_attrs[3] &= ~termios.ECHO  # Index 3 corresponds to local flags (lflags)
        termios.tcsetattr(slave_fd, termios.TCSANOW, slave_attrs)
    except termios.error:
        pass


# SYSTEM UTILITIES SUBSYSTEM: RAW STDIN TERMINAL CONFIGURATION
# This utility checks if standard input is an interactive TTY, saves current attributes,
# and switches the terminal into raw input mode for direct character-by-character processing.
# [>] EXECUTING RAW STDIN SETUP
def setup_raw_stdin() -> Any | None:
    """
    Sets standard input into raw mode if it is a tty, returning original settings for restoration.

    Returns:
        Any | None: The original terminal attribute settings if successfully saved, or None otherwise.
    """
    # TTY VALIDATION & RAW MODE ACTIVATION
    # Verifies if stdin is an interactive TTY, captures its attributes, and switches to raw mode,
    # gracefully handling terminal errors.
    if sys.stdin.isatty():
        try:
            old_settings = termios.tcgetattr(sys.stdin)
            tty.setraw(sys.stdin.fileno())
            return old_settings
        except termios.error:
            return None
    return None


# SYSTEM UTILITIES SUBSYSTEM: STDIN TERMINAL MODE RESTORATION
# This utility restores standard input to canonical cooked mode using previously saved
# terminal attributes upon exiting interactive raw mode.
# [>] EXECUTING STDIN MODE RESTORATION
def restore_stdin_mode(old_settings: Any) -> None:
    """
    Restores standard input to canonical cooked mode using saved terminal settings.

    Args:
        old_settings (Any): The original terminal attribute settings to restore, or None.

    Returns:
        None
    """
    # TTY VALIDATION & ATTRIBUTE RESTORATION
    # Verifies that saved settings exist and stdin is an interactive TTY,
    # then applies the original terminal attributes with draining.
    if old_settings is not None and sys.stdin.isatty():
        try:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        except termios.error:
            pass


# SYSTEM UTILITIES SUBSYSTEM: PTY DESCRIPTOR CLEANUP & CLOSURE
# This utility safely closes pseudo-terminal master and slave file descriptors,
# gracefully catching and handling any operating system or file descriptor errors.
# [>] EXECUTING DESCRIPTOR CLOSURE
def close_descriptors(master_fd: int | None, slave_fd: int | None) -> None:
    """
    Safely closes master and slave file descriptors.

    Args:
        master_fd (int | None): The PTY master file descriptor to close, or None.
        slave_fd (int | None): The PTY slave file descriptor to close, or None.

    Returns:
        None
    """
    # MASTER DESCRIPTOR CLOSURE
    # Closes the PTY master file descriptor if present, suppressing any operating system errors.
    if master_fd is not None:
        try:
            os.close(master_fd)
        except OSError:
            pass

    # SLAVE DESCRIPTOR CLOSURE
    # Closes the PTY slave file descriptor if present, suppressing any operating system errors.
    if slave_fd is not None:
        try:
            os.close(slave_fd)
        except OSError:
            pass


# SYSTEM UTILITIES SUBSYSTEM: MANAGED PTY TERMINAL LIFECYCLE CONTEXT MANAGER
# This context manager orchestrates pseudo-terminal (PTY) pair allocation, slave terminal attribute
# configuration, raw stdin mode switching, and robust cleanup/restoration upon exit.
# [>] EXECUTING MANAGED PTY TERMINAL LIFECYCLE
@contextmanager
def managed_pty_terminal() -> Generator[tuple[int, int], None, None]:
    """
    Allocates a PTY pair, configures slave attributes, sets raw stdin, and guarantees restoration/cleanup on exit.

    Yields:
        tuple[int, int]: A tuple containing the master and slave file descriptors `(master_fd, slave_fd)`.

    Raises:
        OSError: If PTY allocation or terminal attribute configuration fails.
    """
    # INITIALIZE LIFECYCLE REFERENCES
    # Sets up local descriptor variables and terminal setting placeholders prior to context activation.
    master_fd: int | None = None
    slave_fd: int | None = None
    old_tty_settings = None

    try:
        # PTY PAIR SETUP & CONFIGURATION
        # Allocates a new master/slave PTY pair, disables slave echo loops,
        # and switches standard input into raw mode while caching original settings.
        master_fd, slave_fd = allocate_pty_pair()
        disable_pty_echo(slave_fd)
        old_tty_settings = setup_raw_stdin()

        yield master_fd, slave_fd

    finally:
        # GUARANTEED RESOURCE TEARDOWN & RESTORATION
        # Restores original terminal attributes and safely closes both PTY descriptors
        # regardless of execution outcome or raised exceptions.
        restore_stdin_mode(old_tty_settings)
        close_descriptors(master_fd, slave_fd)
