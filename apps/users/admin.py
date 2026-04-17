from django.contrib import admin
from .models import User, OAuthProvider, OutstandingToken, BlacklistedToken

admin.site.register(User)
admin.site.register(OAuthProvider)
admin.site.register(OutstandingToken)
admin.site.register(BlacklistedToken)