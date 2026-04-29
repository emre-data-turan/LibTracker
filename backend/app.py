from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flasgger import Swagger
from dotenv import load_dotenv
import os
import atexit
from datetime import datetime, timezone, timedelta

load_dotenv()


def _complete_expired_reservations(app):
    """Süresi dolan aktif rezervasyonları 'completed' olarak işaretle."""
    with app.app_context():
        from models import Reservation, StudyArea, Library
        from database import db

        # BUG FIX: naive UTC kullan — SQLite naive UTC saklar
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        expired = Reservation.query.filter(
            Reservation.status == "active",
            Reservation.end_time <= now,
        ).all()

        if not expired:
            return

        affected_areas = set()
        for r in expired:
            r.status = "completed"
            affected_areas.add(r.study_area_id)

        db.session.flush()

        for area_id in affected_areas:
            # BUG FIX: deprecated StudyArea.query.get() → db.session.get()
            area = db.session.get(StudyArea, area_id)
            if area:
                active_count = Reservation.query.filter_by(study_area_id=area_id, status="active").count()
                area.available_seats = max(0, area.total_seats - active_count)
                library = db.session.get(Library, area.library_id)
                if library:
                    library.current_occupancy = sum(
                        a.total_seats - a.available_seats for a in library.study_areas
                    )

        db.session.commit()


def create_app(config=None):
    app = Flask(__name__)

    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "DATABASE_URL", "sqlite:///libtracker.db"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=24)

    if config:
        app.config.update(config)

    CORS(app)
    jwt = JWTManager(app)

    Swagger(app, template={
        "info": {
            "title": "LibTracker API",
            "description": "Üniversite kütüphanesi doluluk takip sistemi — Rebs Dev",
            "version": "1.0.0",
        },
        "securityDefinitions": {
            "Bearer": {
                "type": "apiKey",
                "name": "Authorization",
                "in": "header",
                "description": "JWT token. Örnek: Bearer <token>",
            }
        },
    })

    from database import SystemDatabase
    system_db = SystemDatabase()
    system_db.init(app)

    # Token blocklist kontrolü
    from routes.auth import is_token_revoked
    jwt.token_in_blocklist_loader(is_token_revoked)

    from routes.libraries import libraries_bp
    from routes.auth import auth_bp
    from routes.reservations import reservations_bp
    from routes.feedback import feedback_bp
    from routes.stats import stats_bp

    app.register_blueprint(libraries_bp, url_prefix="/libraries")
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(reservations_bp, url_prefix="/reservations")
    app.register_blueprint(feedback_bp, url_prefix="/feedback")
    app.register_blueprint(stats_bp, url_prefix="/stats")

    with app.app_context():
        from database import db
        import models  # noqa: F401 — modelleri SQLAlchemy'e kaydet
        db.create_all()

    # Scheduler'ı test ortamında başlatma — her test çalıştırmasında sızdırır
    if not app.config.get("TESTING"):
        from apscheduler.schedulers.background import BackgroundScheduler
        scheduler = BackgroundScheduler()
        scheduler.add_job(
            func=_complete_expired_reservations,
            args=[app],
            trigger="interval",
            minutes=1,
        )
        scheduler.start()
        atexit.register(lambda: scheduler.shutdown())

    return app


if __name__ == "__main__":
    from database import SystemDatabase
    app = create_app()
    SystemDatabase().seed()
    app.run(debug=True, port=5000)
