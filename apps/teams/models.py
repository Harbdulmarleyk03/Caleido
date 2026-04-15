from django.db import models
from common.models import AbstractBaseModel
from apps.users.models import User

class Team(AbstractBaseModel):
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=100, unique=True)
    owner = models.ForeignKey(User, on_delete=models.PROTECT, related_name="owned_teams", db_index=True)

    class Meta:
        db_table = "teams_team"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class TeamMembership(AbstractBaseModel):
    ROLE_CHOICES = [
        ("owner", "Owner"),
        ("member", "Member"),
    ]

    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="memberships", db_index=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="team_memberships", db_index=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "teams_membership"
        constraints = [
            models.UniqueConstraint(
                fields=["team", "user"],
                name="unique_team_user")]

    def __str__(self):
        return f"{self.user.email} — {self.team.name} ({self.role})"