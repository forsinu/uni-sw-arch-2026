import uuid

import httpx


BASE_URL = "http://localhost:8000"


class TestAuthenticationAPI:
    @classmethod
    def setup_class(cls):
        cls.testEmail = f"user_{uuid.uuid4().hex[:6]}@example.com"
        cls.testPassword = "SuperSecurePassword123!"

        cls.client = httpx.Client(
            base_url=BASE_URL, headers={"Content-Type": "application/json"}
        )

    @classmethod
    def teardown_class(cls):
        cls.client.close()

    def test01_RegistrationSuccess(self):
        payload = {"email": self.testEmail, "password": self.testPassword}

        response = self.client.post("/api/v1/auth/register", json=payload)

        assert response.status_code == 201, (
            f"Expected 201, got {response.status_code}. Msg: {response.text}"
        )

    def test02_RegistrationDuplicate(self):
        payload = {"email": self.testEmail, "password": self.testPassword}

        response = self.client.post("/api/v1/auth/register", json=payload)

        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    def test03_LoginSuccess(self):
        payload = {"email": self.testEmail, "password": self.testPassword}

        response = self.client.post("/api/v1/auth/login", json=payload)

        assert response.status_code == 200

        data = response.json()
        assert "at" in data, "Access Token key 'at' missing from body response mapping."
        assert data["tt"] == "bearer"

        assert "rt" in response.cookies, (
            "The HttpOnly Refresh Token cookie 'rt' was not returned by the API."
        )
        assert response.cookies["rt"] != ""

        print(response.cookies["rt"])

    def test04_RerfreshTokenSuccess(self):

        print(self.client.cookies)
        response = self.client.get("/api/v1/auth/refresh")

        assert response.status_code == 200, response.json()["detail"]
        data = response.json()

        assert "at" in data
        assert data["tt"] == "bearer"

        assert "rt" in response.cookies

    def test05_LoginInvalidCredentialsFail(self):
        payload = {"email": self.testEmail, "password": "WrongPasswordStringAttempt"}

        response = self.client.post("/api/v1/auth/login", json=payload)

        assert response.status_code == 400
        assert "Incorrect email or password" in response.json()["detail"]

    def test06_LoginRateLimitingLockout(self):
        bruteForceEmail = f"attacker_{uuid.uuid4().hex[:6]}@example.com"

        payload = {"email": bruteForceEmail, "password": "WrongPasswordOnPurpose"}

        allowedAttempts = 5

        for attempt in range(allowedAttempts):
            response = self.client.post("/api/v1/auth/login", json=payload)
            assert response.status_code == 400, (
                f"Attempt {attempt + 1} failed with unexpected status: {response.status_code}"
            )

            assert "Incorrect email or password" in response.json()["detail"]

        lockout_response = self.client.post("/api/v1/auth/login", json=payload)

        assert lockout_response.status_code == 429, (
            f"Rate limiter failed! Expected 429 on attempt 6, but got {lockout_response.status_code}"
        )

        data = lockout_response.json()
        assert (
            "Too many failed actions" in data["detail"]
            or "Locked out" in data["detail"]
        )

        print(
            f"\n Rate Limiter confirmed: Received expected 429 on attempt {allowedAttempts + 1}."
        )
