import pytest
from django.urls import reverse
from rest_framework import status

@pytest.mark.django_db
class TestAvailabilityRuleView:

    def test_create_availability_rule(self):
        pass