"""qbXML error handling."""
from __future__ import annotations


# Common qbXML status codes → friendly messages.
QBXML_STATUS_MESSAGES = {
    1: "No matching records found.",
    3100: "Duplicate name found in QuickBooks.",
    3120: "The referenced object is not found in QuickBooks.",
    3140: "There is an invalid reference in the request.",
    3170: "The record is currently in use by another user. Try again in a moment.",
    3180: "QuickBooks rejected the request due to insufficient permissions for the integration user.",
    3200: "Object cannot be found.",
    3260: "Insufficient permission level to perform this action.",
    3261: "This feature is not enabled in this QuickBooks company file.",
    3270: "The QuickBooks feature is not supported in this edition.",
    3300: "The referenced list element is invalid or of the wrong type.",
}


class QBError(Exception):
    """Raised when QuickBooks returns a non-zero status code."""

    def __init__(self, code: int, message: str, request_name: str = ""):
        self.code = code
        self.raw_message = message
        self.request_name = request_name
        friendly = QBXML_STATUS_MESSAGES.get(code, message)
        super().__init__(f"[{code}] {friendly} ({request_name})")

    @property
    def friendly(self) -> str:
        return QBXML_STATUS_MESSAGES.get(self.code, self.raw_message)


class QBConnectionError(Exception):
    """Raised when we cannot connect to QuickBooks at all."""


class QBNotAuthorizedError(QBConnectionError):
    """Raised when QuickBooks has not yet authorized this app for the file."""
