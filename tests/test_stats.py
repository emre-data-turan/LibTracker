"""
İstatistik endpoint testleri
"""


def test_overview_success(client, admin_headers):
    resp = client.get("/stats/overview", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.get_json()
    assert "current_occupants" in data
    assert "active_reservations" in data
    assert "total_feedbacks" in data
    assert "recent_feedbacks" in data
    assert "recent_reservations" in data


def test_overview_requires_admin(client, auth_headers):
    resp = client.get("/stats/overview", headers=auth_headers)
    assert resp.status_code == 403


def test_overview_requires_auth(client):
    resp = client.get("/stats/overview")
    assert resp.status_code == 401


def test_peak_hours_success(client, admin_headers):
    resp = client.get("/stats/peak-hours", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.get_json()
    assert "peak_hours" in data
    assert "days_analyzed" in data


def test_peak_hours_with_params(client, admin_headers, sample_library):
    lib_id = sample_library["library_id"]
    resp = client.get(f"/stats/peak-hours?library_id={lib_id}&days=14", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.get_json()["days_analyzed"] == 14


def test_peak_hours_requires_admin(client, auth_headers):
    resp = client.get("/stats/peak-hours", headers=auth_headers)
    assert resp.status_code == 403


def test_daily_usage_success(client, admin_headers):
    resp = client.get("/stats/daily-usage", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.get_json()
    assert "daily_usage" in data
    assert "days_analyzed" in data


def test_daily_usage_with_params(client, admin_headers, sample_library):
    lib_id = sample_library["library_id"]
    resp = client.get(f"/stats/daily-usage?library_id={lib_id}&days=3", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.get_json()["days_analyzed"] == 3


def test_daily_usage_requires_admin(client, auth_headers):
    resp = client.get("/stats/daily-usage", headers=auth_headers)
    assert resp.status_code == 403


def test_daily_reservations_success(client, admin_headers):
    resp = client.get("/stats/daily-reservations", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.get_json()
    assert "daily_reservations" in data
    assert "days_analyzed" in data


def test_daily_reservations_with_days(client, admin_headers):
    resp = client.get("/stats/daily-reservations?days=30", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.get_json()["days_analyzed"] == 30


def test_daily_reservations_requires_admin(client, auth_headers):
    resp = client.get("/stats/daily-reservations", headers=auth_headers)
    assert resp.status_code == 403
