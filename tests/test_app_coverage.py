"""
app.py'deki kapsanmayan satırları tamamlayan testler.
Missing: 30-49, 60-68, 143-144, 148-156, 166-175
"""
import os
import sys
import warnings
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))


# ── _complete_expired_reservations (satır 30-49) ────────────────────────────

def test_complete_expired_reservations_marks_completed(app, sample_library):
    """Süresi geçmiş aktif rezervasyonlar 'completed' olarak işaretlenmeli."""
    res_id = None
    with app.app_context():
        from database import db
        from models import Reservation, User
        from werkzeug.security import generate_password_hash

        user = User(
            name="Expire Test",
            email="expire@test.edu.tr",
            password_hash=generate_password_hash("pass"),
            is_verified=True,
        )
        db.session.add(user)
        db.session.flush()

        past_start = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=3)
        past_end = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=1)

        res = Reservation(
            user_id=user.id,
            study_area_id=sample_library["study_area_id"],
            seat_number=1,
            start_time=past_start,
            end_time=past_end,
            status="active",
        )
        db.session.add(res)
        db.session.commit()
        res_id = res.id

    # before_request hook'u _complete_expired_reservations'ı tetikler
    client = app.test_client()
    client.get("/libraries/")

    with app.app_context():
        from database import db
        from models import Reservation
        updated = db.session.get(Reservation, res_id)
        assert updated.status == "completed"


def test_complete_expired_reservations_no_expired(app):
    """Süresi geçmiş rezervasyon yoksa fonksiyon erken çıkmalı (satır 27-28)."""
    client = app.test_client()
    # Hiç expired reservation yok, fonksiyon return etmeli — hata olmamalı
    resp = client.get("/libraries/")
    assert resp.status_code == 200


def test_complete_expired_reservations_direct(app, sample_library):
    """_complete_expired_reservations fonksiyonunu doğrudan çağır."""
    from app import _complete_expired_reservations

    with app.app_context():
        from database import db
        from models import Reservation, User
        from werkzeug.security import generate_password_hash

        user = User(
            name="Direct Test",
            email="direct@test.edu.tr",
            password_hash=generate_password_hash("pass"),
            is_verified=True,
        )
        db.session.add(user)
        db.session.flush()

        past_start = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=4)
        past_end = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=2)

        res = Reservation(
            user_id=user.id,
            study_area_id=sample_library["study_area_id"],
            seat_number=2,
            start_time=past_start,
            end_time=past_end,
            status="active",
        )
        db.session.add(res)
        db.session.commit()
        res_id = res.id

    _complete_expired_reservations(app)

    with app.app_context():
        from database import db
        from models import Reservation
        updated = db.session.get(Reservation, res_id)
        assert updated.status == "completed"


# ── SECRET_KEY uyarısı (satır 60-68) ─────────────────────────────────────────

def test_missing_secret_key_warns():
    """SECRET_KEY ve JWT_SECRET_KEY yokken RuntimeWarning çıkmalı."""
    from database import SystemDatabase
    SystemDatabase.reset_instance()

    with patch.dict(os.environ, {}, clear=False):
        env_backup = {}
        for key in ("SECRET_KEY", "JWT_SECRET_KEY"):
            env_backup[key] = os.environ.pop(key, None)

        try:
            from app import create_app
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                create_app({
                    "TESTING": False,
                    "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
                })
            runtime_warnings = [w for w in caught if issubclass(w.category, RuntimeWarning)]
            assert len(runtime_warnings) > 0
            assert "insecure" in str(runtime_warnings[0].message).lower()
        finally:
            for key, val in env_backup.items():
                if val is not None:
                    os.environ[key] = val
            SystemDatabase.reset_instance()


# ── Frontend static dosya servisi (satır 143-144, 148-156) ───────────────────

def test_serve_index(client):
    """GET / → index.html döndürmeli."""
    resp = client.get("/")
    assert resp.status_code == 200


def test_serve_frontend_existing_file(client):
    """GET /admin.html → mevcut frontend dosyası döndürmeli."""
    resp = client.get("/admin.html")
    assert resp.status_code == 200


def test_serve_frontend_nonexistent_file(client):
    """GET /nonexistent.html → 404 döndürmeli."""
    resp = client.get("/nonexistent_file_xyz.html")
    assert resp.status_code == 404


def test_serve_frontend_path_traversal(client):
    """Path traversal girişimi 404 döndürmeli."""
    resp = client.get("/../../../etc/passwd")
    assert resp.status_code in (404, 400)


# ── APScheduler bloğu (satır 166-175) ────────────────────────────────────────

def test_scheduler_starts_in_non_testing_mode():
    """TESTING=False olduğunda APScheduler başlatılmalı."""
    from database import SystemDatabase
    SystemDatabase.reset_instance()

    mock_scheduler = MagicMock()
    mock_scheduler_class = MagicMock(return_value=mock_scheduler)

    with patch("apscheduler.schedulers.background.BackgroundScheduler", mock_scheduler_class):
        from app import create_app
        create_app({
            "TESTING": False,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-key-long-enough-32bytes!!",
            "JWT_SECRET_KEY": "test-jwt-long-enough-32bytes!!",
        })

    mock_scheduler.start.assert_called_once()
    SystemDatabase.reset_instance()
