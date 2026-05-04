"""
Kütüphane endpoint testleri
"""


def test_get_libraries(client, sample_library):
    resp = client.get("/libraries/")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "libraries" in data
    assert data["total"] >= 1
    assert "avg_occupancy_pct" in data
    assert "total_free_seats" in data


def test_get_library_occupancy(client, sample_library):
    lib_id = sample_library["library_id"]
    resp = client.get(f"/libraries/{lib_id}/occupancy")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "library" in data
    assert "study_areas" in data
    assert "total_available_seats" in data


def test_get_library_occupancy_not_found(client):
    resp = client.get("/libraries/99999/occupancy")
    assert resp.status_code == 404


def test_create_library_success(client, admin_headers):
    resp = client.post("/libraries/", json={
        "name": "Yeni Kütüphane",
        "location": "Merkez Kampüs",
        "total_capacity": 90,
    }, headers=admin_headers)
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["library"]["name"] == "Yeni Kütüphane"
    assert data["library"]["total_capacity"] == 90


def test_create_library_missing_name(client, admin_headers):
    resp = client.post("/libraries/", json={"total_capacity": 50}, headers=admin_headers)
    assert resp.status_code == 400


def test_create_library_zero_capacity(client, admin_headers):
    resp = client.post("/libraries/", json={"name": "X", "total_capacity": 0}, headers=admin_headers)
    assert resp.status_code == 400


def test_create_library_invalid_capacity(client, admin_headers):
    resp = client.post("/libraries/", json={"name": "X", "total_capacity": "abc"}, headers=admin_headers)
    assert resp.status_code == 400


def test_create_library_requires_admin(client, auth_headers):
    resp = client.post("/libraries/", json={
        "name": "X", "total_capacity": 30
    }, headers=auth_headers)
    assert resp.status_code == 403


def test_update_library_success(client, admin_headers, sample_library):
    lib_id = sample_library["library_id"]
    resp = client.put(f"/libraries/{lib_id}", json={
        "name": "Güncel Kütüphane",
        "current_occupancy": 5,
    }, headers=admin_headers)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["library"]["name"] == "Güncel Kütüphane"


def test_update_library_invalid_occupancy(client, admin_headers, sample_library):
    lib_id = sample_library["library_id"]
    resp = client.put(f"/libraries/{lib_id}", json={"current_occupancy": -1}, headers=admin_headers)
    assert resp.status_code == 400


def test_update_library_occupancy_over_capacity(client, admin_headers, sample_library):
    lib_id = sample_library["library_id"]
    resp = client.put(f"/libraries/{lib_id}", json={"current_occupancy": 9999}, headers=admin_headers)
    assert resp.status_code == 400


def test_update_library_invalid_capacity(client, admin_headers, sample_library):
    lib_id = sample_library["library_id"]
    resp = client.put(f"/libraries/{lib_id}", json={"total_capacity": "bad"}, headers=admin_headers)
    assert resp.status_code == 400


def test_update_library_capacity_redistributes_seats(client, admin_headers, sample_library):
    lib_id = sample_library["library_id"]
    resp = client.put(f"/libraries/{lib_id}", json={"total_capacity": 120}, headers=admin_headers)
    assert resp.status_code == 200


def test_update_library_requires_admin(client, auth_headers, sample_library):
    lib_id = sample_library["library_id"]
    resp = client.put(f"/libraries/{lib_id}", json={"name": "X"}, headers=auth_headers)
    assert resp.status_code == 403


def test_delete_library_success(client, admin_headers, sample_library):
    lib_id = sample_library["library_id"]
    resp = client.delete(f"/libraries/{lib_id}", headers=admin_headers)
    assert resp.status_code == 200
    assert "silindi" in resp.get_json()["message"]


def test_delete_library_not_found(client, admin_headers):
    resp = client.delete("/libraries/99999", headers=admin_headers)
    assert resp.status_code == 404


def test_delete_library_requires_admin(client, auth_headers, sample_library):
    lib_id = sample_library["library_id"]
    resp = client.delete(f"/libraries/{lib_id}", headers=auth_headers)
    assert resp.status_code == 403
