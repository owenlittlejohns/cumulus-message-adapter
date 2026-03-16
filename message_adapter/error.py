"""Error handling utilities for cumulus-message-adapter."""

import sys


def write_error(error: str) -> None:
    """Write error message to stderr and flush."""
    sys.stderr.write(error + "\n")
    sys.stderr.flush()
