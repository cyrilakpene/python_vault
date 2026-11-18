import os


# SYSTEM UTILITIES SUBSYSTEM: DATA SOURCE RESOLUTION
# This utility resolves inbound data inputs into readable strings by inspecting file extensions
# and reading file contents if a valid path exists, or falling back to raw stream data.
# [>] EXECUTING DATA SOURCE RESOLUTION
def resolve_data_source(data_input: str) -> str:
    """
    Resolves data_input into a readable log string, supporting both
    file paths and direct raw stream buffers.

    Args:
        data_input (str): The file path to a log/text file or a direct raw stream string buffer.

    Returns:
        str: The fully resolved text contents or the original data input string.

    Raises:
        OSError: If an error occurs while opening or reading the target file path.
    """
    # FILE PATH VALIDATION & CONTENT EXTRACTION
    # Checks if the input string represents a valid file path with a log or text extension,
    # then safely reads and returns its contents.
    if data_input.lower().endswith((".log", ".txt")) and os.path.isfile(data_input):
        with open(data_input, "r") as f:
            return f.read()

    # RAW STREAM FALLBACK
    # Returns the input string directly as a raw stream buffer if no matching file path is found.
    return str(data_input)
