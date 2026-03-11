import pytest

from smm.adapters.base import PublishResult
from smm.adapters.registry import AdapterRegistry
from smm.models.social_account import Platform


class TestPublishResult:
    def test_fields(self):
        r = PublishResult(platform_post_id="123", url="https://example.com")
        assert r.platform_post_id == "123"
        assert r.url == "https://example.com"

    def test_optional_url(self):
        r = PublishResult(platform_post_id="456")
        assert r.url is None


class TestAdapterRegistry:
    def test_get_facebook(self):
        adapter = AdapterRegistry.get(Platform.FACEBOOK)
        assert adapter is not None

    def test_get_instagram(self):
        adapter = AdapterRegistry.get(Platform.INSTAGRAM)
        assert adapter is not None

    def test_get_unregistered_platform(self):
        with pytest.raises(ValueError, match="No adapter registered"):
            AdapterRegistry.get(Platform.TWITTER)
