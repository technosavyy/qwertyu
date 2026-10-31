"""Typed exceptions. Library code raises these; only entry points turn them into exit codes."""


class WindfcError(Exception):
    """Base class for every error this package raises on purpose."""


class ElexonError(WindfcError):
    """The Elexon API could not be reached or returned something unusable."""


class ElexonHttpError(ElexonError):
    """The Elexon API answered with an HTTP error status."""

    def __init__(self, status_code: int, body: str) -> None:
        super().__init__(f"Elexon API returned HTTP {status_code}: {body}")
        self.status_code = status_code


class SnapshotError(WindfcError):
    """Source data or a snapshot on disk is missing, malformed or inconsistent."""


class InsufficientDataError(WindfcError):
    """A calculation needs data that is not there, for example metrics over zero hours."""
