import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from database import SystemDatabase


@pytest.fixture(scope="function")
def app():
    SystemDatabase.reset_instance()
    from app import create_app
    application = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "JWT_SECRET_KEY": "test-secret",
        "WTF_CSRF_ENABLED": False,
    })
    yield application
    SystemDatabase.reset_instance()


@pytest.fixture(scope="function")
def client(app):
    return app.test_client()


@pytest.fixture(scope="function")
def seeded_app(app):
    """Seed verisiyle dolu uygulama."""
    SystemDatabase().seed()
    return app


@pytest.fixture(scope="function")
def auth_headers(client):
    """Kayıtlı + giriş yapmış kullanıcının Authorization header'ı."""
    client.post("/auth/register", json={
        "name": "Test Öğrenci",
        "email": "test@university.edu.tr",
        "password": "password123",
    })
    resp = client.post("/auth/login", json={
        "email": "test@university.edu.tr",
        "password": "password123",
    })
    token = resp.get_json()["token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def registered_user(client):
    """Kayıtlı kullanıcı bilgilerini döndürür."""
    resp = client.post("/auth/register", json={
        "name": "Test User",
        "email": "user@university.edu.tr",
        "password": "testpass123",
    })
    data = resp.get_json()
    return {"user": data["user"], "token": data["token"]}


@pytest.fixture(scope="function")
def sample_library(app):
    """Test için örnek kütüphane oluşturur."""
    with app.app_context():
        from database import db
        from models import Library, StudyArea
        lib = Library(
            name="Test Kütüphane",
            location="Test Kampüs",
            total_capacity=50,
            current_occupancy=10,
            is_open=True,
        )
        db.session.add(lib)
        db.session.flush()
        area = StudyArea(
            library_id=lib.id,
            name="Test Alan",
            total_seats=20,
            available_seats=15,
            area_type="general",
        )
        db.session.add(area)
        db.session.commit()
        return {"library_id": lib.id, "study_area_id": area.id}
