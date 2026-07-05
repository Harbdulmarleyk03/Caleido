from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from apps.health.services import HealthService
from drf_spectacular.utils import extend_schema, OpenApiResponse
from apps.health.serializers import HealthCheckSerializer


class HealthAPIView(APIView):
    permission_classes = []
    authentication_classes = []

    @extend_schema(
        request=None,
        responses={
            200: OpenApiResponse(response=HealthCheckSerializer, description="All dependencies healthy"),
            503: OpenApiResponse(response=HealthCheckSerializer, description="One or more dependencies failing"),
        },
        description="Readiness probe — checks DB, Redis, and Celery worker connectivity.",
    )
    def get(self, request):
        data = HealthService.run_all_check()
        if data["status"] == "ok":
            return Response(data, status=status.HTTP_200_OK)
        return Response(data, status=status.HTTP_503_SERVICE_UNAVAILABLE)
