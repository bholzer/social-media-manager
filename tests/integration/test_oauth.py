from unittest.mock import patch

from smm.services.facebook_oauth import (
    FacebookPage,
    FacebookTokens,
)


class TestFacebookOAuthFlow:
    async def test_connect_redirects_to_facebook(
        self, authenticated_client
    ):
        resp = await authenticated_client.get(
            "/api/v1/oauth/facebook/connect",
            follow_redirects=False,
        )
        assert resp.status_code == 307
        assert "facebook.com" in resp.headers["location"]
        assert "state=" in resp.headers["location"]

    async def test_connect_requires_auth(self, client):
        resp = await client.get("/api/v1/oauth/facebook/connect")
        assert resp.status_code == 401

    async def test_callback_invalid_state(self, client):
        resp = await client.get(
            "/api/v1/oauth/facebook/callback",
            params={"code": "test", "state": "bogus"},
        )
        assert resp.status_code == 400
        assert "Invalid" in resp.json()["detail"]

    @patch("smm.api.v1.oauth.get_user_profile")
    @patch("smm.api.v1.oauth.get_user_pages")
    @patch("smm.api.v1.oauth.get_long_lived_token")
    @patch("smm.api.v1.oauth.exchange_code")
    async def test_callback_no_pages_connects_profile(
        self,
        mock_exchange,
        mock_long_lived,
        mock_pages,
        mock_profile,
        authenticated_client,
        session,
    ):
        # First, trigger connect to create state
        resp = await authenticated_client.get(
            "/api/v1/oauth/facebook/connect",
            follow_redirects=False,
        )
        location = resp.headers["location"]
        # Extract state from redirect URL
        import urllib.parse

        parsed = urllib.parse.urlparse(location)
        params = urllib.parse.parse_qs(parsed.query)
        state = params["state"][0]

        mock_exchange.return_value = FacebookTokens(
            access_token="short", expires_in=3600
        )
        mock_long_lived.return_value = FacebookTokens(
            access_token="long_tok", expires_in=5184000
        )
        mock_pages.return_value = []
        mock_profile.return_value = {"id": "fb_123", "name": "Test User"}

        resp = await authenticated_client.get(
            "/api/v1/oauth/facebook/callback",
            params={"code": "auth_code", "state": state},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["message"] == "Facebook profile connected"
        assert data["platform_user_id"] == "fb_123"

    @patch("smm.api.v1.oauth.get_user_pages")
    @patch("smm.api.v1.oauth.get_long_lived_token")
    @patch("smm.api.v1.oauth.exchange_code")
    async def test_callback_with_pages_returns_list(
        self,
        mock_exchange,
        mock_long_lived,
        mock_pages,
        authenticated_client,
    ):
        resp = await authenticated_client.get(
            "/api/v1/oauth/facebook/connect",
            follow_redirects=False,
        )
        import urllib.parse

        parsed = urllib.parse.urlparse(resp.headers["location"])
        state = urllib.parse.parse_qs(parsed.query)["state"][0]

        mock_exchange.return_value = FacebookTokens(
            access_token="short", expires_in=3600
        )
        mock_long_lived.return_value = FacebookTokens(
            access_token="long", expires_in=5184000
        )
        mock_pages.return_value = [
            FacebookPage(
                page_id="pg1", name="My Page", access_token="pt1"
            ),
        ]

        resp = await authenticated_client.get(
            "/api/v1/oauth/facebook/callback",
            params={"code": "auth_code", "state": state},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["pages"]) == 1
        assert data["pages"][0]["page_id"] == "pg1"
        assert "oauth_user_token" in data

    @patch("smm.api.v1.oauth.get_user_pages")
    async def test_connect_page(
        self,
        mock_pages,
        authenticated_client,
    ):
        mock_pages.return_value = [
            FacebookPage(
                page_id="pg1",
                name="My Page",
                access_token="page_long_tok",
            ),
        ]

        resp = await authenticated_client.post(
            "/api/v1/oauth/facebook/connect-page",
            json={
                "page_id": "pg1",
                "page_name": "My Page",
                "oauth_user_token": "user_long_tok",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "My Page"
        assert data["platform_user_id"] == "pg1"
        assert "account_id" in data

    @patch("smm.api.v1.oauth.get_user_pages")
    async def test_connect_page_already_connected(
        self,
        mock_pages,
        authenticated_client,
    ):
        mock_pages.return_value = [
            FacebookPage(
                page_id="dup_pg",
                name="Dup Page",
                access_token="tok",
            ),
        ]

        # Connect once
        await authenticated_client.post(
            "/api/v1/oauth/facebook/connect-page",
            json={
                "page_id": "dup_pg",
                "page_name": "Dup Page",
                "oauth_user_token": "user_tok",
            },
        )

        # Try again
        resp = await authenticated_client.post(
            "/api/v1/oauth/facebook/connect-page",
            json={
                "page_id": "dup_pg",
                "page_name": "Dup Page",
                "oauth_user_token": "user_tok",
            },
        )
        assert resp.status_code == 409

    @patch("smm.api.v1.oauth.get_user_pages")
    async def test_connect_page_not_found(
        self,
        mock_pages,
        authenticated_client,
    ):
        mock_pages.return_value = [
            FacebookPage(
                page_id="other",
                name="Other",
                access_token="tok",
            ),
        ]

        resp = await authenticated_client.post(
            "/api/v1/oauth/facebook/connect-page",
            json={
                "page_id": "nonexistent",
                "page_name": "Nope",
                "oauth_user_token": "user_tok",
            },
        )
        assert resp.status_code == 404
