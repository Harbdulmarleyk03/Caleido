from django.db import connections
from common.exceptions import ServiceUnavailableError
from django import db
from django.db.utils import ConnectionDoesNotExist
from django.conf import settings
from config.celery import app
import uuid
from django.core.cache import cache


class HealthService:

    @staticmethod
    def check_database():
        alias = "default"
        try:
            connection = connections[alias]
        except ConnectionDoesNotExist as e:
            raise ServiceUnavailableError("Database alias does not exist") from e
        try:
            with connection.temporary_connection() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
        except db.Error as e:
            raise ServiceUnavailableError(str(e).rsplit(":")[0]) from e
        else:
            if result != (1,):
                raise ServiceUnavailableError(
                    "Health Check query did not return the expected result."
                )

    @staticmethod
    def check_redis():
        probe_key = str(uuid.uuid4())
        try:
            cache.set(
                probe_key, probe_key, timeout=settings.HEALTH_CHECK_TIMEOUTS["REDIS"]
            )
            result = cache.get(probe_key)
        except Exception:
            raise ServiceUnavailableError(
                "Unable to connect to Redis: Connection Error"
            )
        if result != probe_key:
            raise ServiceUnavailableError("Redis returned unexpected value")

    @staticmethod
    def check_celery():
        try:
            ping_result = app.control.ping(
                timeout=settings.HEALTH_CHECK_TIMEOUTS["CELERY"]
            )
        except NotImplementedError as e:
            raise ServiceUnavailableError(
                "NotImplementedError: Make sure CELERY_RESULT_BACKEND is set"
            ) from e
        except Exception as e:
            raise ServiceUnavailableError(
                f"Unable to reach Celery broker: {type(e).__name__}"
            ) from e
        else:
            if not ping_result:
                raise ServiceUnavailableError("Celery workers unavailable")

    @staticmethod
    def run_all_check():
        results = {}
        overall_status = "ok"  # assume healthy, degrade on failure
        try:
            HealthService.check_database()
            results["db"] = "ok"
        except ServiceUnavailableError:
            results["db"] = "error"
            overall_status = "error"

        try:
            HealthService.check_redis()
            results["redis"] = "ok"
        except ServiceUnavailableError:
            results["redis"] = "error"
            overall_status = "error"

        try:
            HealthService.check_celery()
            results["celery"] = "ok"
        except ServiceUnavailableError:
            results["celery"] = "error"
            overall_status = "error"

        return {"status": overall_status, "checks": results}
