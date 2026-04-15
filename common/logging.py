import logging
import traceback


class RequestIDFilter(logging.Filter):
    """
    Injects request_id into every log record so you can
    trace all log lines from a single request together.
    Set on the request in middleware (Day 11 onwards).
    """
    def filter(self, record):
        if not hasattr(record, 'request_id'):
            record.request_id = 'no-request-id'
        return True