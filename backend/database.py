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
        from models import Library, StudyArea, UsageStatistics, User, Reservation
        from werkzeug.security import generate_password_hash
        import random

        with self._app.app_context():
            # Seed Admin User
            admin_email = "admin@libtracker.edu"
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
                    name="Main Library",
                    location="Main Campus, Block A",
                    total_capacity=300,
                    current_occupancy=random.randint(50, 250),
                    is_open=True,
                    opening_time=time(8, 0),
                    closing_time=time(22, 0),
                ),
                Library(
                    name="Engineering Library",
                    location="Engineering Faculty, Block B",
                    total_capacity=150,
                    current_occupancy=random.randint(20, 130),
                    is_open=True,
                    opening_time=time(8, 30),
                    closing_time=time(21, 0),
                ),
                Library(
                    name="Social Sciences Reading Room",
                    location="Admin Building, Ground Floor",
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
                base_seats = lib.total_capacity // 3
                rem = lib.total_capacity % 3
                total_occupied = 0
                for i, atype in enumerate(area_types, 1):
                    seats = base_seats + (1 if i <= rem else 0)
                    avail = random.randint(0, seats)
                    total_occupied += (seats - avail)
                    area = StudyArea(
                        library_id=lib.id,
                        name=f"{atype.capitalize()} Area {i}",
                        total_seats=seats,
                        available_seats=avail,
                        area_type=atype,
                    )
                    db.session.add(area)
                lib.current_occupancy = total_occupied

            # Son 7 gün için saatlik istatistik verisi (simülasyon)
            now = datetime.now(timezone.utc)
            for lib in libraries:
                for day_offset in range(7):
                    for hour in range(8, 22):
                        recorded = (now - timedelta(days=day_offset)).replace(
                            hour=hour, minute=0, second=0, microsecond=0
                        )
                        if recorded > now:
                            continue
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

            for lib in libraries:
                for area in lib.study_areas:
                    for i in range(2):
                        start_t = now + timedelta(hours=i)
                        end_t = start_t + timedelta(hours=2)
                        res = Reservation(
                            user_id=admin_user.id,
                            study_area_id=area.id,
                            seat_number=i+1,
                            start_time=start_t,
                            end_time=end_t,
                            status="active"
                        )
                        db.session.add(res)

            db.session.commit()

    @classmethod
    def reset_instance(cls):
        """Yalnızca test ortamında kullanılır."""
        with cls._lock:
            cls._instance = None
