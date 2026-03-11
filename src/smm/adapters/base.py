from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class PublishResult:
    platform_post_id: str
    url: str | None = None


class AbstractPlatformAdapter(ABC):
    @abstractmethod
    async def publish(
        self,
        content: str,
        link: str | None,
        image_url: str | None,
        access_token: str,
        platform_user_id: str,
    ) -> PublishResult: ...

    @abstractmethod
    async def validate_token(self, access_token: str) -> bool: ...
