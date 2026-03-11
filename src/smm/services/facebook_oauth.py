import secrets
from dataclasses import dataclass
from urllib.parse import urlencode

import httpx

from smm.adapters.constants import GRAPH_API_BASE_URL
from smm.config import settings

OAUTH_AUTHORIZE = "https://www.facebook.com/v19.0/dialog/oauth"
OAUTH_TOKEN = f"{GRAPH_API_BASE_URL}/oauth/access_token"

# Permissions needed to publish posts to pages
SCOPES = "pages_show_list,pages_read_engagement,pages_manage_posts"


def build_authorize_url(state: str) -> str:
    params = {
        "client_id": settings.facebook_app_id,
        "redirect_uri": f"{settings.base_url}/api/v1/oauth/facebook/callback",
        "state": state,
        "scope": SCOPES,
        "response_type": "code",
    }
    return f"{OAUTH_AUTHORIZE}?{urlencode(params)}"


def generate_state() -> str:
    return secrets.token_urlsafe(32)


@dataclass
class FacebookTokens:
    access_token: str
    expires_in: int


@dataclass
class FacebookPage:
    page_id: str
    name: str
    access_token: str


async def exchange_code(code: str) -> FacebookTokens:
    """Exchange authorization code for a short-lived user token."""
    params = {
        "client_id": settings.facebook_app_id,
        "client_secret": settings.facebook_app_secret,
        "redirect_uri": (
            f"{settings.base_url}/api/v1/oauth/facebook/callback"
        ),
        "code": code,
    }
    async with httpx.AsyncClient() as client:
        resp = await client.get(OAUTH_TOKEN, params=params)
        resp.raise_for_status()
        data = resp.json()
    return FacebookTokens(
        access_token=data["access_token"],
        expires_in=data.get("expires_in", 3600),
    )


async def get_long_lived_token(short_token: str) -> FacebookTokens:
    """Exchange short-lived token for a long-lived token (~60 days)."""
    params = {
        "grant_type": "fb_exchange_token",
        "client_id": settings.facebook_app_id,
        "client_secret": settings.facebook_app_secret,
        "fb_exchange_token": short_token,
    }
    async with httpx.AsyncClient() as client:
        resp = await client.get(OAUTH_TOKEN, params=params)
        resp.raise_for_status()
        data = resp.json()
    return FacebookTokens(
        access_token=data["access_token"],
        expires_in=data.get("expires_in", 5184000),
    )


async def get_user_pages(user_token: str) -> list[FacebookPage]:
    """Fetch pages the user manages (needed for publishing)."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{GRAPH_API_BASE_URL}/me/accounts",
            params={"access_token": user_token},
        )
        resp.raise_for_status()
        data = resp.json()
    return [
        FacebookPage(
            page_id=p["id"],
            name=p["name"],
            access_token=p["access_token"],
        )
        for p in data.get("data", [])
    ]


async def get_user_profile(token: str) -> dict:
    """Get the Facebook user's basic profile info."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{GRAPH_API_BASE_URL}/me",
            params={"access_token": token, "fields": "id,name"},
        )
        resp.raise_for_status()
        return resp.json()
