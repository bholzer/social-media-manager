class TestSocialAccountCRUD:
    async def test_create_social_account(self, authenticated_client):
        response = await authenticated_client.post(
            "/api/v1/social-accounts/",
            json={
                "platform": "facebook",
                "platform_user_id": "12345",
                "access_token": "fb_token_123",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["platform"] == "facebook"
        assert data["platform_user_id"] == "12345"
        assert "access_token" not in data  # Should not expose token

    async def test_list_social_accounts(self, authenticated_client):
        await authenticated_client.post(
            "/api/v1/social-accounts/",
            json={
                "platform": "facebook",
                "platform_user_id": "111",
                "access_token": "tok1",
            },
        )
        await authenticated_client.post(
            "/api/v1/social-accounts/",
            json={
                "platform": "instagram",
                "platform_user_id": "222",
                "access_token": "tok2",
            },
        )

        response = await authenticated_client.get("/api/v1/social-accounts/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    async def test_get_social_account(self, authenticated_client):
        create_resp = await authenticated_client.post(
            "/api/v1/social-accounts/",
            json={
                "platform": "facebook",
                "platform_user_id": "333",
                "access_token": "tok3",
            },
        )
        account_id = create_resp.json()["id"]

        response = await authenticated_client.get(
            f"/api/v1/social-accounts/{account_id}"
        )
        assert response.status_code == 200
        assert response.json()["id"] == account_id

    async def test_delete_social_account(self, authenticated_client):
        create_resp = await authenticated_client.post(
            "/api/v1/social-accounts/",
            json={
                "platform": "facebook",
                "platform_user_id": "444",
                "access_token": "tok4",
            },
        )
        account_id = create_resp.json()["id"]

        response = await authenticated_client.delete(
            f"/api/v1/social-accounts/{account_id}"
        )
        assert response.status_code == 204

        response = await authenticated_client.get(
            f"/api/v1/social-accounts/{account_id}"
        )
        assert response.status_code == 404

    async def test_cross_user_isolation(self, client):
        # Register user 1
        resp1 = await client.post(
            "/api/v1/auth/register",
            json={"email": "user1@test.com", "password": "testpassword123"},
        )
        token1 = resp1.json()["access_token"]

        # Create account as user 1
        create_resp = await client.post(
            "/api/v1/social-accounts/",
            json={
                "platform": "facebook",
                "platform_user_id": "555",
                "access_token": "tok5",
            },
            headers={"Authorization": f"Bearer {token1}"},
        )
        account_id = create_resp.json()["id"]

        # Register user 2
        resp2 = await client.post(
            "/api/v1/auth/register",
            json={"email": "user2@test.com", "password": "testpassword123"},
        )
        token2 = resp2.json()["access_token"]

        # User 2 should not see user 1's account
        response = await client.get(
            f"/api/v1/social-accounts/{account_id}",
            headers={"Authorization": f"Bearer {token2}"},
        )
        assert response.status_code == 404

    async def test_unauthenticated_access(self, client):
        response = await client.get("/api/v1/social-accounts/")
        assert response.status_code == 401
