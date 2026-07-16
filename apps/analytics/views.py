from rest_framework.views import APIView
from apps.analytics.services import AnalyticService
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.analytics.cache import PERIODS
from rest_framework.exceptions import ValidationError
from apps.analytics.serializers import AnalyticsResponseSerializer
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse


class AnalyticsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Analytics"],
        summary="Get aggregated booking analytics for the authenticated owner",
        parameters=[
            OpenApiParameter(
                name="period",
                type=str,
                required=False,
                enum=list(PERIODS),
                default="all",
                description="Aggregation window for the analytics query.",
            ),
        ],
        responses={
            200: OpenApiResponse(
                response=AnalyticsResponseSerializer,
                description="Aggregated booking analytics for the authenticated owner",
            ),
            400: OpenApiResponse(description="Invalid period value"),
        },
    )
    def get(self, request):
        owner = request.user
        period = request.query_params.get("period", "all")
        if period not in PERIODS:
            raise ValidationError({"period": f"Must be one of {PERIODS}"})
        data = AnalyticService.get_owner_analytics(owner=owner, period=period)
        return Response(data)
