import httpx

from smm.adapters.base import AbstractPlatformAdapter, PublishResult
from smm.adapters.constants import GRAPH_API_BASE_URL


class FacebookAdapter(AbstractPlatformAdapter):
    BASE_URL = GRAPH_API_BASE_URL

    async def publish(
        self,
        content: str,
        link: str | None,
        image_url: str | None,
        access_token: str,
        platform_user_id: str,
    ) -> PublishResult:
        url = f"{self.BASE_URL}/{platform_user_id}/feed"
        params = {"access_token": access_token, "message": content}
        if link:
            params["link"] = link

        async with httpx.AsyncClient() as client:
            response = await client.post(url, data=params)
            response.raise_for_status()
            data = response.json()

        return PublishResult(
            platform_post_id=data["id"],
            url=f"https://facebook.com/{data['id']}",
        )

    async def validate_token(self, access_token: str) -> bool:
        url = f"{self.BASE_URL}/me"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params={"access_token": access_token})
            return response.status_code == 200
