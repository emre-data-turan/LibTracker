"""
Feedback sistemi testleri — Barış Küçükkıya
"""


def test_submit_feedback_success(client, auth_headers, sample_library):
    """Geçerli verilerle feedback gönderilebilmeli."""
    resp = client.post("/feedback/", json={
        "library_id": sample_library["library_id"],
        "reported_occupancy": 75,
        "comment": "Biraz kalabalık.",
    }, headers=auth_headers)
    data = resp.get_json()
    assert resp.status_code == 201
    assert data["feedback"]["reported_occupancy"] == 75


def test_submit_feedback_requires_auth(client, sample_library):
    """Token olmadan feedback gönderilemez."""
    resp = client.post("/feedback/", json={
        "library_id": sample_library["library_id"],
        "reported_occupancy": 50,
    })
    assert resp.status_code == 401


def test_submit_feedback_invalid_occupancy(client, auth_headers, sample_library):
    """0-100 dışı doluluk değeri reddedilmeli."""
    resp = client.post("/feedback/", json={
        "library_id": sample_library["library_id"],
        "reported_occupancy": 150,
    }, headers=auth_headers)
    assert resp.status_code == 400


def test_submit_feedback_rate_limit(client, auth_headers, sample_library):
    """Aynı kullanıcı 30 dk içinde 2 kez feedback gönderememeli."""
    lib_id = sample_library["library_id"]
    first = client.post("/feedback/", json={
        "library_id": lib_id, "reported_occupancy": 60
    }, headers=auth_headers)
    assert first.status_code == 201

    second = client.post("/feedback/", json={
        "library_id": lib_id, "reported_occupancy": 70
    }, headers=auth_headers)
    assert second.status_code == 429


def test_get_library_feedback(client, auth_headers, sample_library):
    """Kütüphane feedback'leri listelenebilmeli."""
    lib_id = sample_library["library_id"]
    client.post("/feedback/", json={
        "library_id": lib_id, "reported_occupancy": 45
    }, headers=auth_headers)

    resp = client.get(f"/feedback/{lib_id}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["count"] >= 1
    assert "feedbacks" in data


def test_get_feedback_nonexistent_library(client):
    """Olmayan kütüphane için feedback listesi 404 döndürmeli."""
    resp = client.get("/feedback/99999")
    assert resp.status_code == 404


def test_feedback_missing_fields(client, auth_headers, sample_library):
    """Zorunlu alan eksikse 400 döndürmeli."""
    resp = client.post("/feedback/", json={
        "library_id": sample_library["library_id"]
        # reported_occupancy eksik
    }, headers=auth_headers)
    assert resp.status_code == 400
