from rest_framework import serializers


class HealthCheckSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=["ok", "error"])
    checks = serializers.DictField(
        child=serializers.CharField(),
        required=False,
        help_text="Per-dependency status, e.g. database, redis, celery",
    )
