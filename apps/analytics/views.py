from rest_framework.views import APIView
from apps.analytics.services import AnalyticService
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.analytics.cache import PERIODS
from rest_framework.exceptions import ValidationError
from drf_spectacular.utils import extend_schema, OpenApiParameter, inline_serializer
from drf_spectacular.types import OpenApiTypes
from rest_framework import serializers as drf_serializers


class AnalyticsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="period",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                default="all",
                description=f"Aggregation window. One of {PERIODS}.",
            ),
        ],
        responses={
            # AnalyticService.get_owner_analytics() returns a free-form dict
            # whose exact keys depend on the aggregation period — documented
            # as a generic object rather than a specific serializer, so this
            # schema doesn't silently drift out of sync with that service.
            200: OpenApiTypes.OBJECT,
            400: inline_serializer(
                name="AnalyticsError",
                fields={"period": drf_serializers.ListField(child=drf_serializers.CharField())},
            ),
        },
        description="Owner-facing booking analytics (counts, trends) for the given period, cached 600s.",
    )
    def get(self, request):
        owner = request.user
        period = request.query_params.get("period", "all")
        if period not in PERIODS:
            raise ValidationError({"period": f"Must be one of {PERIODS}"})
        data = AnalyticService.get_owner_analytics(owner=owner, period=period)
        return Response(data)