"""
Auth sistemi unit testleri — Barış Küçükkıya
"""


def test_register_success(client):
    """Geçerli üniversite e-postasıyla kayıt başarılı olmalı."""
    resp = client.post("/auth/register", json={
        "name": "Ali Veli",
        "email": "ali@university.edu.tr",
        "password": "secure123",
    })
    data = resp.get_json()
    assert resp.status_code == 201
    assert "token" in data
    assert data["user"]["email"] == "ali@university.edu.tr"
    assert data["user"]["is_verified"] is True


def test_register_duplicate_email(client):
    """Aynı e-postayla iki kez kayıt yapılamamalı."""
    payload = {"name": "Ali", "email": "ali@uni.edu.tr", "password": "pass123"}
    client.post("/auth/register", json=payload)
    resp = client.post("/auth/register", json=payload)
    assert resp.status_code == 409
    assert "zaten kayıtlı" in resp.get_json()["error"]


def test_register_invalid_email_domain(client):
    """Gmail veya genel e-postalar reddedilmeli."""
    resp = client.post("/auth/register", json={
        "name": "Test",
        "email": "test@gmail.com",
        "password": "pass123",
    })
    assert resp.status_code == 400
    assert "üniversite" in resp.get_json()["error"].lower()


def test_register_missing_fields(client):
    """Eksik alan içeren istek 400 döndürmeli."""
    resp = client.post("/auth/register", json={"email": "x@uni.edu.tr"})
    assert resp.status_code == 400


def test_register_short_password(client):
    """6 karakterden kısa şifre reddedilmeli."""
    resp = client.post("/auth/register", json={
        "name": "Test",
        "email": "test@uni.edu.tr",
        "password": "123",
    })
    assert resp.status_code == 400


def test_login_success(client):
    """Doğru kimlik bilgileriyle giriş token döndürmeli."""
    client.post("/auth/register", json={
        "name": "Zeynep",
        "email": "zeynep@uni.edu.tr",
        "password": "mypassword",
    })
    resp = client.post("/auth/login", json={
        "email": "zeynep@uni.edu.tr",
        "password": "mypassword",
    })
    data = resp.get_json()
    assert resp.status_code == 200
    assert "token" in data
    assert data["user"]["email"] == "zeynep@uni.edu.tr"


def test_login_wrong_password(client):
    """Yanlış şifre 401 döndürmeli."""
    client.post("/auth/register", json={
        "name": "Mehmet",
        "email": "mehmet@uni.edu.tr",
        "password": "correct",
    })
    resp = client.post("/auth/login", json={
        "email": "mehmet@uni.edu.tr",
        "password": "wrong",
    })
    assert resp.status_code == 401


def test_login_nonexistent_user(client):
    """Kayıtsız e-posta ile giriş 401 döndürmeli."""
    resp = client.post("/auth/login", json={
        "email": "nobody@uni.edu.tr",
        "password": "any",
    })
    assert resp.status_code == 401


def test_logout_invalidates_token(client):
    """Logout sonrası token ile istek yapılamaz."""
    client.post("/auth/register", json={
        "name": "Ayşe",
        "email": "ayse@uni.edu.tr",
        "password": "mypass123",
    })
    login_resp = client.post("/auth/login", json={
        "email": "ayse@uni.edu.tr",
        "password": "mypass123",
    })
    token = login_resp.get_json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    logout_resp = client.post("/auth/logout", headers=headers)
    assert logout_resp.status_code == 200

    # Logout sonrası aynı token ile /auth/me isteği başarısız olmalı
    me_resp = client.get("/auth/me", headers=headers)
    assert me_resp.status_code == 401


def test_me_requires_auth(client):
    """/auth/me token olmadan 401 döndürmeli."""
    resp = client.get("/auth/me")
    assert resp.status_code == 401


def test_me_returns_user_info(client, auth_headers):
    """/auth/me geçerli token ile kullanıcı bilgisi döndürmeli."""
    resp = client.get("/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.get_json()
    assert "user" in data
    assert "email" in data["user"]
