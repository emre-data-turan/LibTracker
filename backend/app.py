from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flasgger import Swagger
from dotenv import load_dotenv
import os
import atexit
import warnings
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
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

    secret_key = os.getenv("SECRET_KEY")
    jwt_secret = os.getenv("JWT_SECRET_KEY")

    if not secret_key or not jwt_secret:
        if not config or not config.get("TESTING"):
            warnings.warn(
                "SECRET_KEY and JWT_SECRET_KEY are not set! "
                "Using insecure defaults. Set them in .env for production.",
                RuntimeWarning,
                stacklevel=2,
            )
        secret_key = secret_key or "dev-secret-key"
        jwt_secret = jwt_secret or "dev-jwt-secret"

    app.config["SECRET_KEY"] = secret_key
    app.config["JWT_SECRET_KEY"] = jwt_secret
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "DATABASE_URL", "sqlite:///libtracker.db"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=24)

    if config:
        app.config.update(config)

    CORS(app, origins=[
        "http://localhost:5000",
        "http://127.0.0.1:5000",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "http://localhost:3000",
    ])
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

    @app.before_request
    def clean_expired_reservations_hook():
        _complete_expired_reservations(app)

    @app.after_request
    def add_header(response):
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '-1'
        return response

    # ── Serve frontend static files ────────────────────────
    frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
    frontend_dir = os.path.abspath(frontend_dir)

    @app.route("/")
    def serve_index():
        from flask import send_from_directory
        return send_from_directory(frontend_dir, "index.html")

    @app.route("/<path:filename>")
    def serve_frontend(filename):
        from flask import send_from_directory
        from flask import abort
        filepath = os.path.abspath(os.path.join(frontend_dir, filename))
        if os.path.commonpath([frontend_dir, filepath]) != frontend_dir:
            abort(404)
        if os.path.isfile(filepath):
            return send_from_directory(frontend_dir, filename)
        # Fall through to 404 for unknown paths
        abort(404)

    with app.app_context():
        from database import db
        import models  # noqa: F401 — modelleri SQLAlchemy'e kaydet
        db.create_all()
        system_db.seed()

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
