from smm.adapters.base import AbstractPlatformAdapter
from smm.adapters.facebook import FacebookAdapter
from smm.adapters.instagram import InstagramAdapter
from smm.models.social_account import Platform


class AdapterRegistry:
    _adapters: dict[Platform, AbstractPlatformAdapter] = {
        Platform.FACEBOOK: FacebookAdapter(),
        Platform.INSTAGRAM: InstagramAdapter(),
    }

    @classmethod
    def get(cls, platform: Platform) -> AbstractPlatformAdapter:
        adapter = cls._adapters.get(platform)
        if adapter is None:
            raise ValueError(f"No adapter registered for platform: {platform}")
        return adapter

    @classmethod
    def register(cls, platform: Platform, adapter: AbstractPlatformAdapter) -> None:
        cls._adapters[platform] = adapter
