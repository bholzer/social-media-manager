from unittest.mock import patch


class TestPublishFlow:
    """End-to-end test: register, link account, create post, publish."""

    @patch("smm.workers.tasks.publish_target_task")
    async def test_full_publish_flow(self, mock_task, client):
        # 1. Register
        resp = await client.post(
            "/api/v1/auth/register",
            json={"email": "e2e@test.com", "password": "testpassword123"},
        )
        assert resp.status_code == 201
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Link social account
        resp = await client.post(
            "/api/v1/social-accounts/",
            json={
                "platform": "facebook",
                "platform_user_id": "e2e_user",
                "access_token": "e2e_token",
            },
            headers=headers,
        )
        assert resp.status_code == 201
        account_id = resp.json()["id"]

        # 3. Create post
        resp = await client.post(
            "/api/v1/posts/",
            json={
                "content": "E2E test post!",
                "targets": [{"social_account_id": account_id}],
            },
            headers=headers,
        )
        assert resp.status_code == 201
        post_id = resp.json()["id"]
        assert resp.json()["targets"][0]["status"] == "draft"

        # 4. Publish now
        resp = await client.post(
            f"/api/v1/posts/{post_id}/publish-now",
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["targets"][0]["status"] == "publishing"

        # Verify Dramatiq task was enqueued
        mock_task.send.assert_called_once()
