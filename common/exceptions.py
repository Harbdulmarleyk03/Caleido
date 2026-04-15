import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import (
    APIException,
    ValidationError,
    AuthenticationFailed,
    NotAuthenticated,
    PermissionDenied,
    NotFound,
    MethodNotAllowed,
    Throttled,
)
from django.core.exceptions import (
    ObjectDoesNotExist,
    PermissionDenied as DjangoPermissionDenied,
)
from django.http import Http404

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Central exception handler for the entire API.

    Every error response has this exact shape:
    {
        "error":   "snake_case_error_code",
        "message": "Human readable message.",
        "details": { "field": ["error detail"] }
    }

    This means your frontend always knows exactly
    where to look for error information.
    """

    # --- Step 1: Convert Django exceptions to DRF exceptions ---
    # DRF's default handler only knows about DRF exceptions.
    # We need to handle Django's own exceptions too.
    exc = _convert_django_exception(exc)

    # --- Step 2: Let DRF handle what it knows about ---
    response = exception_handler(exc, context)

    # --- Step 3: Handle what DRF couldn't ---
    if response is None:
        response = _handle_unknown_exception(exc, context)
        return response

    # --- Step 4: Reshape the response into our uniform format ---
    response.data = _build_error_response(exc, response)

    return response


# ------------------------------------------------------------------
# Exception conversion
# ------------------------------------------------------------------

def _convert_django_exception(exc):
    """
    Map Django core exceptions → DRF exceptions so they get
    proper HTTP status codes instead of 500 errors.
    """
    if isinstance(exc, Http404):
        return NotFound()

    if isinstance(exc, ObjectDoesNotExist):
        return NotFound()

    if isinstance(exc, DjangoPermissionDenied):
        return PermissionDenied()

    return exc  # return unchanged if no conversion needed


# ------------------------------------------------------------------
# Unknown / unhandled exceptions (500s)
# ------------------------------------------------------------------

def _handle_unknown_exception(exc, context):
    """
    Called when DRF has no idea what the exception is.
    These are true 500 server errors — log the full traceback.
    """
    view = context.get('view')
    view_name = view.__class__.__name__ if view else 'Unknown'

    # Log with full traceback so you can debug in Sentry / logs
    logger.exception(
        "Unhandled exception in view '%s': %s",
        view_name,
        str(exc),
    )

    return Response(
        {
            'error': 'server_error',
            'message': 'An unexpected error occurred. Please try again later.',
            'details': {},
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


# ------------------------------------------------------------------
# Response builder
# ------------------------------------------------------------------

def _build_error_response(exc, response):
    """
    Build the uniform error response dict from a DRF exception.
    """
    return {
        'error': _get_error_code(exc, response.status_code),
        'message': _get_message(exc, response.data),
        'details': _get_details(exc, response.data),
    }


def _get_error_code(exc, status_code):
    """
    Map exception type → snake_case error code string.
    Frontend uses this to programmatically handle errors.
    """
    # Check specific exception types first
    if isinstance(exc, ValidationError):
        return 'validation_error'
    if isinstance(exc, (AuthenticationFailed, NotAuthenticated)):
        return 'authentication_failed'
    if isinstance(exc, PermissionDenied):
        return 'permission_denied'
    if isinstance(exc, NotFound):
        return 'not_found'
    if isinstance(exc, MethodNotAllowed):
        return 'method_not_allowed'
    if isinstance(exc, Throttled):
        return 'throttled'
    if isinstance(exc, ConflictError):
        return 'conflict'

    # Fall back to status code mapping
    mapping = {
        400: 'bad_request',
        401: 'authentication_failed',
        403: 'permission_denied',
        404: 'not_found',
        405: 'method_not_allowed',
        409: 'conflict',
        429: 'throttled',
        500: 'server_error',
    }
    return mapping.get(status_code, 'error')


def _get_message(exc, data):
    """
    Extract a single human-readable summary message.
    This is what you show in a toast/alert on the frontend.
    """
    # Throttled exceptions have a helpful wait message
    if isinstance(exc, Throttled):
        wait = exc.wait
        if wait is not None:
            return f'Request limit exceeded. Try again in {int(wait)} seconds.'
        return 'Request limit exceeded. Try again later.'

    if isinstance(data, dict):
        # DRF puts single-message errors under 'detail'
        if 'detail' in data:
            return str(data['detail'])
        # Validation errors sometimes put errors under 'non_field_errors'
        if 'non_field_errors' in data:
            errors = data['non_field_errors']
            return str(errors[0]) if errors else 'Invalid input.'
        return 'Invalid input. Please check the details and try again.'

    if isinstance(data, list) and data:
        return str(data[0])

    return str(data)


def _get_details(exc, data):
    """
    Return field-level error details.
    Used by the frontend to highlight specific form fields.

    Example output:
    {
        "email": ["This field is required."],
        "password": ["Must be at least 8 characters."]
    }
    """
    # Single-message errors (detail key) have no field-level details
    if isinstance(data, dict) and 'detail' in data:
        return {}

    # Validation errors — return the full field error dict
    if isinstance(exc, ValidationError) and isinstance(data, dict):
        return data

    return {}


# ------------------------------------------------------------------
# Custom exception classes
# ------------------------------------------------------------------

class ConflictError(APIException):
    """
    409 Conflict — used when a booking slot is already taken,
    a slug is already in use, etc.

    Usage in a view or service:
        raise ConflictError("This time slot is no longer available.")
    """
    status_code = status.HTTP_409_CONFLICT
    default_detail = 'A conflict occurred.'
    default_code = 'conflict'


class ServiceUnavailableError(APIException):
    """
    503 Service Unavailable — used when an external service
    (Google Calendar, Stripe) is down.

    Usage:
        raise ServiceUnavailableError("Google Calendar is unavailable.")
    """
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = 'Service temporarily unavailable.'
    default_code = 'service_unavailable'


class AppError(APIException):
    """
    Base class for all application-specific errors.

    Instead of raising generic exceptions in services.py,
    raise specific subclasses of AppError. They automatically
    get caught by custom_exception_handler and returned
    with the correct HTTP status code and error shape.

    Example — defining a specific error:
        class SlotUnavailableError(AppError):
            status_code = 409
            default_detail = 'This slot is no longer available.'
            default_code = 'slot_unavailable'

    Example — raising it in services.py:
        if slot_is_taken:
            raise SlotUnavailableError()

    Example — raising with a custom message:
        raise AppError('Something specific went wrong.', code='specific_error')
    """
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'An application error occurred.'
    default_code = 'app_error'