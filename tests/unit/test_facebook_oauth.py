from unittest.mock import AsyncMock, MagicMock, patch
from urllib.parse import parse_qs, urlparse

from smm.services.facebook_oauth import (
    build_authorize_url,
    generate_state,
)


def _mock_httpx_client(response_data):
    """Create a mock httpx.AsyncClient that returns response_data."""
    mock_resp = MagicMock()
    mock_resp.json.return_value = response_data
    mock_resp.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_resp
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = False
    return mock_client


class TestBuildAuthorizeUrl:
    def test_contains_required_params(self):
        url = build_authorize_url("test-state")
        parsed = urlparse(url)
        params = parse_qs(parsed.query)

        assert "facebook.com" in parsed.netloc
        assert params["state"] == ["test-state"]
        assert params["response_type"] == ["code"]
        assert "pages_manage_posts" in params["scope"][0]

    def test_includes_redirect_uri(self):
        url = build_authorize_url("s")
        assert "callback" in url


class TestGenerateState:
    def test_returns_unique_values(self):
        s1 = generate_state()
        s2 = generate_state()
        assert s1 != s2
        assert len(s1) > 20


class TestExchangeCode:
    @patch("smm.services.facebook_oauth.httpx.AsyncClient")
    async def test_exchange_returns_tokens(self, mock_cls):
        mock_cls.return_value = _mock_httpx_client(
            {"access_token": "short_tok", "expires_in": 3600}
        )

        from smm.services.facebook_oauth import exchange_code

        result = await exchange_code("test-code")
        assert result.access_token == "short_tok"
        assert result.expires_in == 3600


class TestGetUserPages:
    @patch("smm.services.facebook_oauth.httpx.AsyncClient")
    async def test_returns_pages(self, mock_cls):
        mock_cls.return_value = _mock_httpx_client(
            {
                "data": [
                    {
                        "id": "page1",
                        "name": "My Page",
                        "access_token": "page_tok",
                    },
                    {
                        "id": "page2",
                        "name": "Other Page",
                        "access_token": "page_tok2",
                    },
                ]
            }
        )

        from smm.services.facebook_oauth import get_user_pages

        pages = await get_user_pages("user_tok")
        assert len(pages) == 2
        assert pages[0].page_id == "page1"
        assert pages[0].name == "My Page"

    @patch("smm.services.facebook_oauth.httpx.AsyncClient")
    async def test_returns_empty_list(self, mock_cls):
        mock_cls.return_value = _mock_httpx_client({"data": []})

        from smm.services.facebook_oauth import get_user_pages

        pages = await get_user_pages("user_tok")
        assert pages == []
