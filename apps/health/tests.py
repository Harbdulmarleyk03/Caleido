import pytest
from unittest.mock import patch
from django import db


@pytest.mark.django_db
class TestHealthCheck:

    @patch("apps.health.services.connections")
    @patch("apps.health.services.cache")
    @patch("apps.health.services.app.control.ping")
    def test_all_dependencies_healthy(
        self, mock_ping, mock_cache, mock_connections, api_client
    ):
        mock_ping.return_value = [{"worker@host": {"ok": "pong"}}]
        mock_cursor = (
            mock_connections.__getitem__.return_value.temporary_connection.return_value.__enter__.return_value
        )
        mock_cursor.fetchone.return_value = (1,)
        mock_cache.get.return_value = "test-probe-key"
        with patch("apps.health.services.uuid.uuid4", return_value="test-probe-key"):
            response = api_client.get("/api/v1/health/")
        assert response.status_code == 200
        assert response.data["status"] == "ok"
        assert response.data["checks"]["db"] == "ok"
        assert response.data["checks"]["redis"] == "ok"
        assert response.data["checks"]["celery"] == "ok"

    @patch("apps.health.services.connections")
    @patch("apps.health.services.cache")
    @patch("apps.health.services.app.control.ping")
    def test_db_is_down(self, mock_ping, mock_cache, mock_connections, api_client):
        mock_ping.return_value = [{"worker@host": {"ok": "pong"}}]
        mock_connections.__getitem__.return_value.temporary_connection.side_effect = (
            db.Error("Connection refused")
        )
        mock_cache.get.return_value = "test-probe-key"
        with patch("apps.health.services.uuid.uuid4", return_value="test-probe-key"):
            response = api_client.get("/api/v1/health/")
        assert response.status_code == 503
        assert response.data["checks"]["db"] == "error"

    @patch("apps.health.services.connections")
    @patch("apps.health.services.cache")
    @patch("apps.health.services.app.control.ping")
    def test_redis_is_down(self, mock_ping, mock_cache, mock_connections, api_client):
        mock_ping.return_value = [{"worker@host": {"ok": "pong"}}]
        mock_cache.set.side_effect = ConnectionError("Redis unreachable")
        mock_cursor = (
            mock_connections.__getitem__.return_value.temporary_connection.return_value.__enter__.return_value
        )
        mock_cursor.fetchone.return_value = (1,)
        response = api_client.get("/api/v1/health/")
        assert response.status_code == 503
        assert response.data["checks"]["redis"] == "error"

    @patch("apps.health.services.connections")
    @patch("apps.health.services.cache")
    @patch("apps.health.services.app.control.ping")
    def test_celery_is_down(self, mock_ping, mock_cache, mock_connections, api_client):
        mock_ping.side_effect = OSError("Broker unreachable")
        mock_cursor = (
            mock_connections.__getitem__.return_value.temporary_connection.return_value.__enter__.return_value
        )
        mock_cursor.fetchone.return_value = (1,)
        mock_cache.get.return_value = "test-probe-key"
        with patch("apps.health.services.uuid.uuid4", return_value="test-probe-key"):
            response = api_client.get("/api/v1/health/")
        assert response.status_code == 503
        assert response.data["checks"]["celery"] == "error"

    @patch("apps.health.services.connections")
    @patch("apps.health.services.cache")
    @patch("apps.health.services.app.control.ping")
    def test_two_dependencies_are_down(
        self, mock_ping, mock_cache, mock_connections, api_client
    ):
        mock_connections.__getitem__.return_value.temporary_connection.side_effect = (
            db.Error("down")
        )
        mock_cache.set.side_effect = Exception("down")
        mock_ping.return_value = [{"worker@host": {"ok": "pong"}}]
        response = api_client.get("/api/v1/health/")
        assert response.status_code == 503
        assert response.data["checks"]["db"] == "error"
        assert response.data["checks"]["redis"] == "error"
        assert response.data["checks"]["celery"] == "ok"
