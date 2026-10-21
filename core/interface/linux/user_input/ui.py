import sys
import termios
import tty
from typing import Any, cast


# LOW-LEVEL TERMINAL INPUT & ANSI ESCAPE PARSING ENGINE
# Reads low-level standard input keypresses directly by manipulating TTY terminal attributes.
# Captures standard characters, handles terminal interrupt signals, maps navigational WASD keys,
# and decodes multi-byte ANSI escape sequence sequences for standard directional arrow keys.
def _read_terminal_key() -> str:
    """
    Reads single keypresses, WASD, and ANSI arrow escape sequences.

    Returns:
        str: Normalized key representation string (e.g., 'UP', 'DOWN', 'LEFT', 'RIGHT', 'ENTER', or uppercase character).

    Raises:
        KeyboardInterrupt: If the user passes the explicit Ctrl+C interrupt sequence (`\x03`).
    """
    # FILE DESCRIPTOR & TERMINAL STATE ISOLATION
    # Acquires standard input file descriptor and saves active terminal attributes for guaranteed restoration.
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)

    # DIRECTIONAL ARROW ANSI SUFFIX MAP
    # Maps terminal escape sequence trailing characters to standard uppercase direction strings.
    arrow_map = {"A": "UP", "B": "DOWN", "C": "RIGHT", "D": "LEFT"}

    # CARRIAGE RETURN & NEWLINE NORMALIZATION MAP
    # Maps raw carriage return and line feed character inputs to unified ENTER token identifiers.
    control_map = {"\r": "ENTER", "\n": "ENTER"}

    try:
        # RAW TTY TERMINAL MODE ACTIVATION
        # Switches terminal into unbuffered raw mode to intercept single keypresses immediately without line buffering.
        tty.setraw(fd)
        ch = sys.stdin.read(1)

        # INTERRUPT SIGNAL DETECTION
        # Explicitly traps Ctrl+C (`\x03`) byte sequence and raises a native KeyboardInterrupt.
        if ch == "\x03":
            raise KeyboardInterrupt

        # ANSI ESCAPE SEQUENCE DECODER (DIRECTIONAL ARROWS)
        # Evaluates initial escape byte (`\x1b`), reading trailing control bytes to decode arrow keys.
        if ch == "\x1b":
            ch2 = sys.stdin.read(1)
            if ch2 == "[":
                ch3 = sys.stdin.read(1)
                return arrow_map.get(ch3, "UNKNOWN")
            return "UNKNOWN"

        # STANDARD TOKEN NORMALIZATION & CONTROL KEY MAPPING
        # Translates carriage returns/newlines via control_map or converts character keypresses (e.g., WASD) to uppercase.
        return control_map.get(ch, ch.upper())

    finally:
        # TERMINAL ATTRIBUTE RESTORATION
        # Restores original terminal configuration state upon output delivery or exception unwinding.
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


# INTERACTIVE TERMINAL 2D GRID OPTION SELECTOR ENGINE
# Provides an interactive, 2D grid-driven CLI selector using low-level key navigation (All Arrow keys / WASD).
# Features dynamic terminal line clearing, real-time 2D index wrap-around navigation, and ANSI cursor positioning.
def select_option(
    prompt: str,
    field: dict[str, Any],
) -> str:
    """
    Interactive 2D grid arrow/WASD selection handler for Linux terminals.

    Args:
        prompt: Display text presenting the selection menu context to the user.
        field: Field configuration dictionary containing 'choices', 'default', and 'cols'.

    Returns:
        str: String representation of the chosen option selected by the operator.

    Raises:
        ValueError: If choices is empty or None.
    """
    choices = cast(list[Any], field.get("choices", []))
    default = field.get("default")

    # COLUMN LAYOUT CONFIGURATION & EXTRACTION
    # Retrieves the specified number of grid columns from the field configuration,
    # defaulting to a 2-column layout if the 'cols' key is missing or undefined.
    cols = field.get("cols", 2)

    # EMPTY CHOICES VALIDATION GUARD
    # Asserts that choice collection contains valid options before initiating terminal interactive loop.
    if not choices:
        raise ValueError(
            "Field configuration with input='select' requires a non-empty 'choices' list."
        )

    # DEFAULT INDEX RESOLUTION: INITIALIZE CURSOR POSITION
    # Default cursor position to current value index if present, else 0.
    selected_index = 0
    if default is not None and default in choices:
        selected_index = choices.index(default)

    # GRID TOPOLOGY METRICS INITIALIZATION
    # Computes total choices length and sets up a 2-column spatial grid layout matrix.
    total = len(choices)
    rows = (total + cols - 1) // cols

    # DYNAMIC COLUMN WIDTH CALCULATION
    # Computes the maximum string length for choices in each column to ensure clean grid alignment.
    col_widths = [
        max(
            (
                len(str(choices[r * cols + c]))
                for r in range(rows)
                if r * cols + c < total
            ),
            default=0,
        )
        for c in range(cols)
    ]

    # 2D GRID DIRECTIONAL KEY NAVIGATION VECTOR MAP
    # Maps normalized keypress inputs (All Arrow keys & WASD aliases) to relative 2D coordinate displacement steps (row/col delta).
    nav_map = {
        "UP": (-1, 0),
        "W": (-1, 0),
        "DOWN": (1, 0),
        "S": (1, 0),
        "LEFT": (0, -1),
        "A": (0, -1),
        "RIGHT": (0, 1),
        "D": (0, 1),
    }

    # GRID RENDERER HELPER FUNCTION
    # Formats the 1D choice vector into a structured 2D layout grid, highlighting the active selection via brackets.
    def _render_grid() -> list[str]:
        lines: list[str] = []
        for r in range(rows):
            line_items: list[str] = []
            for c in range(cols):
                idx = r * cols + c
                width = col_widths[c]
                if idx < total:
                    choice = str(choices[idx])
                    if idx == selected_index:
                        line_items.append(f" ➔ {choice:<{width}}")
                    else:
                        line_items.append(f" {choice:<{width}} ")
                else:
                    line_items.append("")
            lines.append("   ".join(line_items))
        return lines

    # INITIAL MENU HEADER & GRID OPTIONS RENDERING
    # Displays prompt instructions and prints the initial multi-line 2D grid layout with the active item highlighted.
    print(f"[?] {prompt}: (Use Arrow/WASD keys to navigate, Enter to select)")
    initial_lines = _render_grid()
    for line in initial_lines:
        print(f"\033[K{line}")

    # 1D-TO-2D COORDINATE INITIALIZATION
    # Converts active 1D selected_index into initial 2D coordinates (row, col) for spatial tracking.
    r_idx = selected_index // cols
    c_idx = selected_index % cols

    # EVENT-DRIVEN INTERACTIVE 2D SELECTION LOOP
    # Listens for unbuffered terminal keypresses via the low-level key reader to update active 2D grid coordinates or finalize selection on ENTER.
    while True:
        # RAW TERMINAL KEYPRESS ACQUISITION
        # Intercepts next normalized keypress token from terminal input buffer.
        key = _read_terminal_key()

        if key in nav_map:
            dr, dc = nav_map[key]
            # 2D COORDINATE DISPLACEMENT & WRAP-AROUND MODULO CALCULATION
            # Offsets row and column indices based on spatial movement vectors and applies modulo arithmetic for seamless circular navigation.
            r_idx = (r_idx + dr) % rows
            c_idx = (c_idx + dc) % cols

            # BOUNDARY CONFINEMENT & PADDING CORRECTION
            # Recomputes 1D index, handling out-of-bounds padding slots in the trailing matrix row.
            new_index = r_idx * cols + c_idx
            if new_index >= total:
                if dr != 0:  # Vertical movement fallback correction
                    if dr > 0:
                        r_idx = 0  # Wrap to top row
                    else:
                        r_idx = rows - 1  # Wrap to bottom row
                    new_index = r_idx * cols + c_idx
                    if new_index >= total:
                        c_idx = total % cols - 1
                        new_index = r_idx * cols + c_idx
                else:  # Horizontal movement fallback correction
                    if dc > 0:
                        c_idx = 0
                    else:
                        c_idx = cols - 1
                    new_index = r_idx * cols + c_idx

            selected_index = new_index

        elif key == "ENTER":
            # TERMINAL MENU CLEANUP & FINAL SELECTION DISPLAY
            # Repositions cursor upward, clears active 2D grid rows, and prints finalized choice output.
            sys.stdout.write(f"\033[{rows}A")
            for _ in range(rows):
                sys.stdout.write("\033[K\n")
            sys.stdout.write(f"\033[{rows + 1}A\033[K")
            selected_value = str(choices[selected_index])
            print(f"[?] {prompt}: {selected_value}")
            return selected_value
        else:
            # UNRECOGNIZED KEYPRESS IGNORE
            # Ignores non-navigational key inputs and resumes event listening loop without re-rendering.
            continue

        # LIVE TERMINAL GRID RE-RENDERING
        # Repositions cursor to the top of the grid block and re-prints options with updated active coordinate highlight.
        sys.stdout.write(f"\033[{rows}A")
        updated_lines = _render_grid()
        for line in updated_lines:
            sys.stdout.write(f"\033[K{line}\n")
