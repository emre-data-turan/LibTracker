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


# ── PUT /auth/me/password ─────────────────────────────────────────────────────

def test_update_password_success(client, auth_headers):
    """Doğru eski şifreyle yeni şifre başarıyla güncellenmeli."""
    resp = client.put("/auth/me/password", json={
        "old_password": "password123",
        "new_password": "newpassword456",
    }, headers=auth_headers)
    assert resp.status_code == 200
    assert "güncellendi" in resp.get_json()["message"]


def test_update_password_wrong_old_password(client, auth_headers):
    """Yanlış eski şifre 401 döndürmeli."""
    resp = client.put("/auth/me/password", json={
        "old_password": "wrongpassword",
        "new_password": "newpassword456",
    }, headers=auth_headers)
    assert resp.status_code == 401
    assert "hatalı" in resp.get_json()["error"]


def test_update_password_short_new_password(client, auth_headers):
    """6 karakterden kısa yeni şifre 400 döndürmeli."""
    resp = client.put("/auth/me/password", json={
        "old_password": "password123",
        "new_password": "123",
    }, headers=auth_headers)
    assert resp.status_code == 400


def test_update_password_missing_fields(client, auth_headers):
    """Eksik alan 400 döndürmeli."""
    resp = client.put("/auth/me/password", json={
        "old_password": "password123",
    }, headers=auth_headers)
    assert resp.status_code == 400


def test_update_password_requires_auth(client):
    """Token olmadan şifre güncellenemez."""
    resp = client.put("/auth/me/password", json={
        "old_password": "pass",
        "new_password": "newpass123",
    })
    assert resp.status_code == 401


# ── DELETE /auth/me ───────────────────────────────────────────────────────────

def test_delete_account_success(client):
    """Kullanıcı kendi hesabını silebilmeli."""
    client.post("/auth/register", json={
        "name": "Silinecek",
        "email": "delete@uni.edu.tr",
        "password": "pass123",
    })
    login = client.post("/auth/login", json={
        "email": "delete@uni.edu.tr",
        "password": "pass123",
    })
    token = login.get_json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.delete("/auth/me", headers=headers)
    assert resp.status_code == 200
    assert "silindi" in resp.get_json()["message"]

    # Token artık geçersiz olmalı (blocklist'e eklendi)
    me = client.get("/auth/me", headers=headers)
    assert me.status_code == 401


def test_delete_account_with_active_reservation(client, sample_library):
    """Aktif rezervasyonu olan hesap silindiğinde koltuk müsaitliği güncellenmeli."""
    from datetime import datetime, timezone, timedelta

    client.post("/auth/register", json={
        "name": "Rezervasyonlu",
        "email": "withres@uni.edu.tr",
        "password": "pass123",
    })
    login = client.post("/auth/login", json={
        "email": "withres@uni.edu.tr",
        "password": "pass123",
    })
    token = login.get_json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    future = (datetime.now(timezone.utc) + timedelta(days=1)).replace(
        hour=10, minute=0, second=0, microsecond=0
    )
    client.post("/reservations/", json={
        "study_area_id": sample_library["study_area_id"],
        "seat_number": 1,
        "start_time": future.isoformat(),
        "end_time": (future + timedelta(hours=2)).isoformat(),
    }, headers=headers)

    resp = client.delete("/auth/me", headers=headers)
    assert resp.status_code == 200


def test_delete_account_requires_auth(client):
    """Token olmadan hesap silinemez."""
    resp = client.delete("/auth/me")
    assert resp.status_code == 401
