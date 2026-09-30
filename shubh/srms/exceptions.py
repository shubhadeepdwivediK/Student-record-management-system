"""Custom exception hierarchy so callers can handle errors precisely."""


class SRMSError(Exception):
    """Base class for all application errors."""


class ValidationError(SRMSError):
    """Input failed validation."""


class NotFoundError(SRMSError):
    """Requested record does not exist."""


class DuplicateError(SRMSError):
    """A unique field (roll number, email, course code...) already exists."""


class AuthError(SRMSError):
    """Authentication failed."""


class PermissionDenied(AuthError):
    """Logged-in user lacks permission for the action."""
