from rest_framework.views import APIView
from apps.analytics.services import AnalyticService
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.analytics.cache import PERIODS
from rest_framework.exceptions import ValidationError


class AnalyticsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        owner = request.user
        period = request.query_params.get("period", "all")
        if period not in PERIODS:
            raise ValidationError({"period": f"Must be one of {PERIODS}"})
        data = AnalyticService.get_owner_analytics(owner=owner, period=period)
        return Response(data)
