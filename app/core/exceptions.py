"""Custom exceptions for the AeroInsight application.

Defines domain-specific exceptions that provide structured error handling
across the service layer, infrastructure, and API endpoints.
"""

from __future__ import annotations


# ---------------------------------------------------------------------------
# Base exceptions
# ---------------------------------------------------------------------------


class AeroInsightError(Exception):
    """Base exception for all application errors."""

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


# ---------------------------------------------------------------------------
# Domain exceptions
# ---------------------------------------------------------------------------


class ConceptNotFoundError(AeroInsightError):
    """Raised when a concept with the given ID does not exist."""

    def __init__(self, concept_id: int):
        super().__init__(
            message=f"Concept with id={concept_id} was not found.",
            details={"concept_id": concept_id},
        )
        self.concept_id = concept_id


class EvaluationExistsError(AeroInsightError):
    """Raised when attempting to create an evaluation for a concept that already has one."""

    def __init__(self, concept_id: int):
        super().__init__(
            message=(
                f"Concept id={concept_id} already has an evaluation. "
                "Delete the concept and resubmit to re-evaluate."
            ),
            details={"concept_id": concept_id},
        )
        self.concept_id = concept_id


class EvaluationNotFoundError(AeroInsightError):
    """Raised when a concept does not have an evaluation."""

    def __init__(self, concept_id: int):
        super().__init__(
            message=f"Concept id={concept_id} does not have an evaluation.",
            details={"concept_id": concept_id},
        )
        self.concept_id = concept_id


class ReportNotFoundError(AeroInsightError):
    """Raised when a report with the given ID does not exist."""

    def __init__(self, report_id: int):
        super().__init__(
            message=f"Report with id={report_id} was not found.",
            details={"report_id": report_id},
        )
        self.report_id = report_id


class ValidationError(AeroInsightError):
    """Raised when input validation fails."""

    def __init__(self, message: str, field: str | None = None):
        details = {"field": field} if field else {}
        super().__init__(message=message, details=details)
        self.field = field


# ---------------------------------------------------------------------------
# Infrastructure exceptions
# ---------------------------------------------------------------------------


class VectorStoreError(AeroInsightError):
    """Raised when ChromaDB operations fail."""

    def __init__(self, message: str, operation: str | None = None):
        details = {"operation": operation} if operation else {}
        super().__init__(message=message, details=details)
        self.operation = operation


class LLMServiceError(AeroInsightError):
    """Raised when LLM API calls fail."""

    def __init__(
        self, message: str, model: str | None = None, error_type: str | None = None
    ):
        details = {}
        if model:
            details["model"] = model
        if error_type:
            details["error_type"] = error_type
        super().__init__(message=message, details=details)
        self.model = model
        self.error_type = error_type


class DatabaseError(AeroInsightError):
    """Raised when database operations fail."""

    def __init__(self, message: str, operation: str | None = None):
        details = {"operation": operation} if operation else {}
        super().__init__(message=message, details=details)
        self.operation = operation


# ---------------------------------------------------------------------------
# API exceptions
# ---------------------------------------------------------------------------


class RateLimitError(AeroInsightError):
    """Raised when API rate limits are exceeded."""

    def __init__(self, message: str, retry_after: int | None = None):
        details = {"retry_after": retry_after} if retry_after else {}
        super().__init__(message=message, details=details)
        self.retry_after = retry_after


class ServiceUnavailableError(AeroInsightError):
    """Raised when a required service is temporarily unavailable."""

    def __init__(self, service: str, message: str | None = None):
        msg = message or f"Service {service} is temporarily unavailable."
        super().__init__(message=msg, details={"service": service})
        self.service = service


class AuthenticationError(AeroInsightError):
    """Raised when a request cannot be authenticated."""

    def __init__(self, message: str = "Authentication required."):
        super().__init__(message=message)


class AuthorizationError(AeroInsightError):
    """Raised when an authenticated user is not allowed to perform an action."""

    def __init__(self, message: str = "You are not authorized to perform this action."):
        super().__init__(message=message)


class InvalidCredentialsError(AeroInsightError):
    """Raised when login credentials are invalid."""

    def __init__(self):
        super().__init__(message="Invalid username or password.")


class UserAlreadyExistsError(AeroInsightError):
    """Raised when a user with the same username already exists."""

    def __init__(self, username: str):
        super().__init__(
            message=f"User '{username}' already exists.",
            details={"username": username},
        )
