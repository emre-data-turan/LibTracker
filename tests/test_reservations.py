"""
Rezervasyon sistemi unit + entegrasyon testleri — Barış Küçükkıya
"""
from datetime import datetime, timezone, timedelta


def _future(days=1, hour=10):
    dt = datetime.now(timezone.utc).replace(hour=hour, minute=0, second=0, microsecond=0)
    return (dt + timedelta(days=days)).isoformat()


def test_create_reservation_success(client, auth_headers, sample_library):
    """Geçerli verilerle rezervasyon başarıyla oluşturulmalı."""
    resp = client.post("/reservations/", json={
        "study_area_id": sample_library["study_area_id"],
        "seat_number": 1,
        "start_time": _future(1, 10),
        "end_time": _future(1, 12),
    }, headers=auth_headers)
    data = resp.get_json()
    assert resp.status_code == 201
    assert "reservation" in data
    assert data["reservation"]["status"] == "active"


def test_create_reservation_conflict(client, auth_headers, sample_library):
    """Aynı koltuk, aynı saat için iki rezervasyon çakışmalı."""
    payload = {
        "study_area_id": sample_library["study_area_id"],
        "seat_number": 2,
        "start_time": _future(2, 10),
        "end_time": _future(2, 12),
    }
    first = client.post("/reservations/", json=payload, headers=auth_headers)
    assert first.status_code == 201

    second = client.post("/reservations/", json=payload, headers=auth_headers)
    assert second.status_code == 409
    assert "rezerve" in second.get_json()["error"]


def test_create_reservation_partial_overlap(client, auth_headers, sample_library):
    """Kısmi örtüşen zaman dilimi de çakışma sayılmalı."""
    area_id = sample_library["study_area_id"]
    client.post("/reservations/", json={
        "study_area_id": area_id, "seat_number": 3,
        "start_time": _future(3, 10), "end_time": _future(3, 14),
    }, headers=auth_headers)

    resp = client.post("/reservations/", json={
        "study_area_id": area_id, "seat_number": 3,
        "start_time": _future(3, 12), "end_time": _future(3, 16),
    }, headers=auth_headers)
    assert resp.status_code == 409


def test_create_reservation_no_overlap(client, auth_headers, sample_library):
    """Birbiriyle örtüşmeyen saatler aynı koltuğa rezerve edilebilmeli."""
    area_id = sample_library["study_area_id"]
    r1 = client.post("/reservations/", json={
        "study_area_id": area_id, "seat_number": 4,
        "start_time": _future(4, 9), "end_time": _future(4, 11),
    }, headers=auth_headers)
    r2 = client.post("/reservations/", json={
        "study_area_id": area_id, "seat_number": 4,
        "start_time": _future(4, 11), "end_time": _future(4, 13),
    }, headers=auth_headers)
    assert r1.status_code == 201
    assert r2.status_code == 201


def test_create_reservation_end_before_start(client, auth_headers, sample_library):
    """Bitiş zamanı başlangıçtan önce olamaz."""
    resp = client.post("/reservations/", json={
        "study_area_id": sample_library["study_area_id"],
        "seat_number": 5,
        "start_time": _future(5, 14),
        "end_time": _future(5, 10),
    }, headers=auth_headers)
    assert resp.status_code == 400


def test_create_reservation_invalid_seat(client, auth_headers, sample_library):
    """Koltuk numarası alan kapasitesini aşamaz."""
    resp = client.post("/reservations/", json={
        "study_area_id": sample_library["study_area_id"],
        "seat_number": 9999,
        "start_time": _future(6, 10),
        "end_time": _future(6, 12),
    }, headers=auth_headers)
    assert resp.status_code == 400


def test_create_reservation_requires_auth(client, sample_library):
    """Token olmadan rezervasyon yapılamaz."""
    resp = client.post("/reservations/", json={
        "study_area_id": sample_library["study_area_id"],
        "seat_number": 1,
        "start_time": _future(7, 10),
        "end_time": _future(7, 12),
    })
    assert resp.status_code == 401


def test_get_user_reservations(client, auth_headers, registered_user, sample_library):
    """Kullanıcı kendi rezervasyonlarını görebilmeli."""
    # registered_user fixture'ı auth_headers'dan farklı kullanıcı, başka token gerek
    # Bunun yerine auth_headers kullanıcısının ID'sini me endpoint'inden alalım
    me = client.get("/auth/me", headers=auth_headers)
    user_id = me.get_json()["user"]["id"]

    client.post("/reservations/", json={
        "study_area_id": sample_library["study_area_id"],
        "seat_number": 6,
        "start_time": _future(8, 10),
        "end_time": _future(8, 12),
    }, headers=auth_headers)

    resp = client.get(f"/reservations/user/{user_id}", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["count"] >= 1
    assert all(r["status"] == "active" for r in data["reservations"])


def test_get_reservations_forbidden_for_other_user(client, auth_headers, registered_user):
    """Başkasının rezervasyonlarına erişim yasak."""
    other_id = registered_user["user"]["id"]
    resp = client.get(f"/reservations/user/{other_id}", headers=auth_headers)
    assert resp.status_code == 403


def test_cancel_reservation(client, auth_headers, sample_library):
    """Rezervasyon başarıyla iptal edilebilmeli."""
    create = client.post("/reservations/", json={
        "study_area_id": sample_library["study_area_id"],
        "seat_number": 7,
        "start_time": _future(9, 10),
        "end_time": _future(9, 12),
    }, headers=auth_headers)
    res_id = create.get_json()["reservation"]["id"]

    cancel = client.delete(f"/reservations/{res_id}", headers=auth_headers)
    assert cancel.status_code == 200
    assert "iptal" in cancel.get_json()["message"]


def test_cancel_nonexistent_reservation(client, auth_headers):
    """Olmayan rezervasyonu iptal etmek 404 döndürmeli."""
    resp = client.delete("/reservations/99999", headers=auth_headers)
    assert resp.status_code == 404


def test_cancel_reservation_wrong_user(client, sample_library):
    """Başka kullanıcının rezervasyonunu iptal etmek 403 döndürmeli."""
    # Kullanıcı 1 rezervasyon oluşturur
    client.post("/auth/register", json={
        "name": "User1", "email": "user1@uni.edu.tr", "password": "pass123"
    })
    r1 = client.post("/auth/login", json={"email": "user1@uni.edu.tr", "password": "pass123"})
    headers1 = {"Authorization": f"Bearer {r1.get_json()['token']}"}

    create = client.post("/reservations/", json={
        "study_area_id": sample_library["study_area_id"],
        "seat_number": 8,
        "start_time": _future(10, 10),
        "end_time": _future(10, 12),
    }, headers=headers1)
    res_id = create.get_json()["reservation"]["id"]

    # Kullanıcı 2 iptal etmeye çalışır
    client.post("/auth/register", json={
        "name": "User2", "email": "user2@uni.edu.tr", "password": "pass123"
    })
    r2 = client.post("/auth/login", json={"email": "user2@uni.edu.tr", "password": "pass123"})
    headers2 = {"Authorization": f"Bearer {r2.get_json()['token']}"}

    resp = client.delete(f"/reservations/{res_id}", headers=headers2)
    assert resp.status_code == 403
