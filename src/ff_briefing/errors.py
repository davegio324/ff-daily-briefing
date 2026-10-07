class BriefingError(Exception):
    """Base for every expected, user-facing failure; the CLI prints it without a traceback."""
