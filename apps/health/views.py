from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from apps.health.services import HealthService
from drf_spectacular.utils import extend_schema, OpenApiResponse
from drf_spectacular.types import OpenApiTypes


class HealthAPIView(APIView):
    permission_classes = []
    authentication_classes = []

    @extend_schema(
        auth=[],  # explicitly unauthenticated — no security scheme applies here
        responses={
            200: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="All dependencies (database, Redis, Celery) healthy.",
            ),
            503: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="One or more dependencies unhealthy — see per-dependency status in the body.",
            ),
        },
        description=(
            "Liveness/readiness probe. Independently checks database, Redis, and "
            "Celery connectivity with per-dependency timeouts. Public, unthrottled."
        ),
    )
    def get(self, request):
        data = HealthService.run_all_check()
        if data["status"] == "ok":
            return Response(data, status=status.HTTP_200_OK)
        return Response(data, status=status.HTTP_503_SERVICE_UNAVAILABLE)