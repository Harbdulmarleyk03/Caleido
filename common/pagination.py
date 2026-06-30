from rest_framework.pagination import CursorPagination


class BookmarkCursorPagination(CursorPagination):
    page_size = 20
    ordering = ("-start_time", "id")
    page_size_query_param = "page_size"
    max_page_size = 100


class EventTypeCursorPagination(CursorPagination):
    page_size = 20
    ordering = ("-created_at", "id")
    page_size_query_param = "page_size"
    max_page_size = 100


class AvailabilityRuleCursorPagination(CursorPagination):
    page_size = 50  # rules per event type are few — larger page size is fine
    ordering = ("day_of_week", "start_time", "id")
    page_size_query_param = "page_size"
    max_page_size = 200


class DateOverrideCursorPagination(CursorPagination):
    page_size = 50
    ordering = ("specific_date", "id")
    page_size_query_param = "page_size"
    max_page_size = 200
