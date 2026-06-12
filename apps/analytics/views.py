from rest_framework.views import APIView
from apps.analytics.services import AnalyticService
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

class AnalyticsAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        owner = request.user
        period = request.query_params.get('period')
        data = AnalyticService.get_owner_analytics(owner=owner, period=period)
        return Response(data)