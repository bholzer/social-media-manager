import datetime
import uuid


class TestPostCRUD:
    async def _create_account(self, client):
        """Helper to create a social account and return its ID."""
        resp = await client.post(
            "/api/v1/social-accounts/",
            json={
                "platform": "facebook",
                "platform_user_id": str(uuid.uuid4()),
                "access_token": "tok",
            },
        )
        return resp.json()["id"]

    async def test_create_post(self, authenticated_client):
        account_id = await self._create_account(authenticated_client)
        response = await authenticated_client.post(
            "/api/v1/posts/",
            json={
                "content": "Hello world!",
                "targets": [{"social_account_id": account_id}],
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["content"] == "Hello world!"
        assert len(data["targets"]) == 1
        assert data["targets"][0]["status"] == "draft"

    async def test_create_scheduled_post(self, authenticated_client):
        account_id = await self._create_account(authenticated_client)
        future = (
            datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=1)
        ).isoformat()
        response = await authenticated_client.post(
            "/api/v1/posts/",
            json={
                "content": "Scheduled post",
                "scheduled_at": future,
                "targets": [{"social_account_id": account_id}],
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["targets"][0]["status"] == "scheduled"

    async def test_create_post_invalid_account(self, authenticated_client):
        response = await authenticated_client.post(
            "/api/v1/posts/",
            json={
                "content": "Bad target",
                "targets": [{"social_account_id": str(uuid.uuid4())}],
            },
        )
        assert response.status_code == 400

    async def test_list_posts(self, authenticated_client):
        account_id = await self._create_account(authenticated_client)
        for i in range(3):
            await authenticated_client.post(
                "/api/v1/posts/",
                json={
                    "content": f"Post {i}",
                    "targets": [{"social_account_id": account_id}],
                },
            )
        response = await authenticated_client.get("/api/v1/posts/")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["items"]) == 3

    async def test_list_posts_pagination(self, authenticated_client):
        account_id = await self._create_account(authenticated_client)
        for i in range(5):
            await authenticated_client.post(
                "/api/v1/posts/",
                json={
                    "content": f"Post {i}",
                    "targets": [{"social_account_id": account_id}],
                },
            )
        response = await authenticated_client.get("/api/v1/posts/?page=1&size=2")
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 5

    async def test_get_post(self, authenticated_client):
        account_id = await self._create_account(authenticated_client)
        create_resp = await authenticated_client.post(
            "/api/v1/posts/",
            json={
                "content": "Get me",
                "targets": [{"social_account_id": account_id}],
            },
        )
        post_id = create_resp.json()["id"]
        response = await authenticated_client.get(f"/api/v1/posts/{post_id}")
        assert response.status_code == 200
        assert response.json()["content"] == "Get me"

    async def test_update_post(self, authenticated_client):
        account_id = await self._create_account(authenticated_client)
        create_resp = await authenticated_client.post(
            "/api/v1/posts/",
            json={
                "content": "Original",
                "targets": [{"social_account_id": account_id}],
            },
        )
        post_id = create_resp.json()["id"]
        response = await authenticated_client.patch(
            f"/api/v1/posts/{post_id}",
            json={"content": "Updated"},
        )
        assert response.status_code == 200
        assert response.json()["content"] == "Updated"

    async def test_delete_post(self, authenticated_client):
        account_id = await self._create_account(authenticated_client)
        create_resp = await authenticated_client.post(
            "/api/v1/posts/",
            json={
                "content": "Delete me",
                "targets": [{"social_account_id": account_id}],
            },
        )
        post_id = create_resp.json()["id"]
        response = await authenticated_client.delete(f"/api/v1/posts/{post_id}")
        assert response.status_code == 204

        response = await authenticated_client.get(f"/api/v1/posts/{post_id}")
        assert response.status_code == 404

    async def test_cross_user_post_isolation(self, client):
        # User 1 creates a post
        resp1 = await client.post(
            "/api/v1/auth/register",
            json={"email": "postuser1@test.com", "password": "testpassword123"},
        )
        token1 = resp1.json()["access_token"]
        headers1 = {"Authorization": f"Bearer {token1}"}

        acct_resp = await client.post(
            "/api/v1/social-accounts/",
            json={
                "platform": "facebook",
                "platform_user_id": "u1acct",
                "access_token": "tok",
            },
            headers=headers1,
        )
        account_id = acct_resp.json()["id"]

        post_resp = await client.post(
            "/api/v1/posts/",
            json={
                "content": "User 1 post",
                "targets": [{"social_account_id": account_id}],
            },
            headers=headers1,
        )
        post_id = post_resp.json()["id"]

        # User 2 cannot access it
        resp2 = await client.post(
            "/api/v1/auth/register",
            json={"email": "postuser2@test.com", "password": "testpassword123"},
        )
        token2 = resp2.json()["access_token"]
        headers2 = {"Authorization": f"Bearer {token2}"}

        response = await client.get(f"/api/v1/posts/{post_id}", headers=headers2)
        assert response.status_code == 404

    async def test_unauthenticated_access(self, client):
        response = await client.get("/api/v1/posts/")
        assert response.status_code == 401
