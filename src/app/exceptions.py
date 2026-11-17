"""Custom exceptions fuer Generierungslimits."""


class GenerationTimeoutError(Exception):
    """Wird geworfen, wenn ein Generierungsalgorithmus das Timeout ueberschreitet."""

    def __init__(self, elapsed: float, timeout: int):
        self.elapsed = elapsed
        self.timeout = timeout
        super().__init__(f"Generation timed out after {elapsed:.1f}s (limit: {timeout}s)")