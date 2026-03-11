import httpx

from smm.adapters.base import AbstractPlatformAdapter, PublishResult


class InstagramAdapter(AbstractPlatformAdapter):
    BASE_URL = "https://graph.facebook.com/v19.0"

    async def publish(
        self,
        content: str,
        link: str | None,
        image_url: str | None,
        access_token: str,
        platform_user_id: str,
    ) -> PublishResult:
        if not image_url:
            raise ValueError("Instagram requires an image_url")

        # Step 1: Create media container
        container_url = f"{self.BASE_URL}/{platform_user_id}/media"
        params = {
            "access_token": access_token,
            "image_url": image_url,
            "caption": content,
        }

        async with httpx.AsyncClient() as client:
            resp = await client.post(container_url, data=params)
            resp.raise_for_status()
            creation_id = resp.json()["id"]

            # Step 2: Publish the container
            publish_url = f"{self.BASE_URL}/{platform_user_id}/media_publish"
            resp = await client.post(
                publish_url,
                data={"access_token": access_token, "creation_id": creation_id},
            )
            resp.raise_for_status()
            media_id = resp.json()["id"]

        return PublishResult(platform_post_id=media_id)

    async def validate_token(self, access_token: str) -> bool:
        url = f"{self.BASE_URL}/me"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params={"access_token": access_token})
            return response.status_code == 200
