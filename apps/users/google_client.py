import secrets
import urllib.parse
import requests
from config.settings.base import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI

GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"

GOOGLE_AUTH_BASE_URL = "https://accounts.google.com/o/oauth2/v2/auth"

def get_google_auth_url():
    state = secrets.token_urlsafe(32)

    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "offline",
        "prompt": "consent",  # ensures refresh token
    }
    url = f"{GOOGLE_AUTH_BASE_URL}?{urllib.parse.urlencode(params)}"
    return url, state

def exchange_code_for_tokens(code):
    data = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }
    response = requests.post(GOOGLE_TOKEN_URL, data=data)
    response.raise_for_status()

    return response.json()

def get_google_user_info(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}

    response = requests.get("https://www.googleapis.com/oauth2/v3/userinfo", headers=headers)
    response.raise_for_status()
    data = response.json()
    return {
        "email": data.get("email"),
        "first_name": data.get("given_name"),
        "last_name": data.get("family_name"),
        "provider_uid": data.get("sub"),
    }