class TestRegister:
    async def test_register_success(self, client):
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": "new@example.com", "password": "testpassword123"},
        )
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    async def test_register_duplicate_email(self, client):
        await client.post(
            "/api/v1/auth/register",
            json={"email": "dup@example.com", "password": "testpassword123"},
        )
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": "dup@example.com", "password": "testpassword123"},
        )
        assert response.status_code == 409

    async def test_register_invalid_email(self, client):
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": "not-email", "password": "testpassword123"},
        )
        assert response.status_code == 422

    async def test_register_short_password(self, client):
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": "a@b.com", "password": "short"},
        )
        assert response.status_code == 422


class TestLogin:
    async def test_login_success(self, client):
        await client.post(
            "/api/v1/auth/register",
            json={"email": "login@example.com", "password": "testpassword123"},
        )
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "login@example.com", "password": "testpassword123"},
        )
        assert response.status_code == 200
        assert "access_token" in response.json()

    async def test_login_wrong_password(self, client):
        await client.post(
            "/api/v1/auth/register",
            json={"email": "wrong@example.com", "password": "testpassword123"},
        )
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "wrong@example.com", "password": "wrongpassword"},
        )
        assert response.status_code == 401

    async def test_login_nonexistent_user(self, client):
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "noone@example.com", "password": "testpassword123"},
        )
        assert response.status_code == 401


class TestGetMe:
    async def test_get_me_authenticated(self, authenticated_client):
        response = await authenticated_client.get("/api/v1/users/me")
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
        assert "id" in data

    async def test_get_me_unauthenticated(self, client):
        response = await client.get("/api/v1/users/me")
        assert response.status_code == 401
