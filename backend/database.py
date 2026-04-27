import threading
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class SystemDatabase:
    """
    Singleton: uygulama boyunca tek bir SystemDatabase örneği var.
    __new__ override + threading.Lock ile thread-safe garanti edilir.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                # İkinci kez kontrol: lock alındıktan sonra başka thread
                # zaten oluşturmuş olabilir.
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def init(self, app):
        """Flask app bağlamında çağrılır; yalnızca bir kez çalışır."""
        if self._initialized:
            return
        db.init_app(app)
        self._app = app
        self._initialized = True

    @property
    def session(self):
        return db.session

    @property
    def engine(self):
        return db.engine

    def create_tables(self):
        with self._app.app_context():
            db.create_all()

    def drop_tables(self):
        with self._app.app_context():
            db.drop_all()

    def seed(self):
        """
        Geliştirme ortamı için örnek veri yükler.
        Gerçek sensör verisi olmadığından simülasyon kullanılır.
        """
        from datetime import datetime, time, timezone, timedelta
        from models import Library, StudyArea, UsageStatistics, User
        from werkzeug.security import generate_password_hash
        import random

        with self._app.app_context():
            # Seed Admin User
            admin_email = "admin"
            admin_user = User.query.filter_by(email=admin_email).first()
            if not admin_user:
                admin_user = User(
                    name="admin",
                    email=admin_email,
                    password_hash=generate_password_hash("admin"),
                    is_admin=True,
                    is_verified=True
                )
                db.session.add(admin_user)
                db.session.commit()

            if Library.query.first():
                return  # Zaten seed yapılmış

            libraries = [
                Library(
                    name="Merkez Kütüphane",
                    location="Ana Kampüs, A Blok",
                    total_capacity=300,
                    current_occupancy=random.randint(50, 250),
                    is_open=True,
                    opening_time=time(8, 0),
                    closing_time=time(22, 0),
                ),
                Library(
                    name="Mühendislik Kütüphanesi",
                    location="Mühendislik Fakültesi, B Blok",
                    total_capacity=150,
                    current_occupancy=random.randint(20, 130),
                    is_open=True,
                    opening_time=time(8, 30),
                    closing_time=time(21, 0),
                ),
                Library(
                    name="Sosyal Bilimler Okuma Salonu",
                    location="İdari Bina, Zemin Kat",
                    total_capacity=80,
                    current_occupancy=random.randint(0, 70),
                    is_open=True,
                    opening_time=time(9, 0),
                    closing_time=time(20, 0),
                ),
            ]
            db.session.add_all(libraries)
            db.session.flush()

            area_types = ["general", "silent", "group"]
            for lib in libraries:
                for i, atype in enumerate(area_types, 1):
                    seats = lib.total_capacity // 3
                    area = StudyArea(
                        library_id=lib.id,
                        name=f"{atype.capitalize()} Alan {i}",
                        total_seats=seats,
                        available_seats=random.randint(0, seats),
                        area_type=atype,
                    )
                    db.session.add(area)

            # Son 7 gün için saatlik istatistik verisi (simülasyon)
            now = datetime.now(timezone.utc)
            for lib in libraries:
                for day_offset in range(7):
                    for hour in range(8, 22):
                        recorded = now - timedelta(days=day_offset, hours=(now.hour - hour))
                        peak_factor = 1.0 if hour in (10, 11, 14, 15, 16) else 0.5
                        occ = int(lib.total_capacity * peak_factor * random.uniform(0.3, 0.9))
                        stat = UsageStatistics(
                            library_id=lib.id,
                            recorded_at=recorded,
                            occupancy_count=occ,
                            occupancy_percentage=round(occ / lib.total_capacity * 100, 1),
                            source="simulation",
                        )
                        db.session.add(stat)

            db.session.commit()

    @classmethod
    def reset_instance(cls):
        """Yalnızca test ortamında kullanılır."""
        with cls._lock:
            cls._instance = None
