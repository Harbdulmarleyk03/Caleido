from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from apps.health.services import HealthService


class HealthAPIView(APIView):
    permission_classes = []
    authentication_classes = []

    def get(self, request):
        data = HealthService.run_all_check()
        if data["status"] == "ok":
            return Response(data, status=status.HTTP_200_OK)
        return Response(data, status=status.HTTP_503_SERVICE_UNAVAILABLE)
