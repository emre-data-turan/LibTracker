from datetime import datetime, timezone
from database import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_verified = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # BUG FIX: lazy="dynamic" SQLAlchemy 2.0'da deprecated — lazy="select" kullan
    reservations = db.relationship("Reservation", back_populates="user", lazy="select")
    feedbacks = db.relationship("Feedback", back_populates="user", lazy="select")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "is_verified": self.is_verified,
            "is_admin": self.is_admin,
            "created_at": self.created_at.isoformat(),
        }

    def __repr__(self):
        return f"<User {self.email}>"


class Library(db.Model):
    __tablename__ = "libraries"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    total_capacity = db.Column(db.Integer, nullable=False)
    current_occupancy = db.Column(db.Integer, default=0)
    is_open = db.Column(db.Boolean, default=True)
    opening_time = db.Column(db.Time, nullable=True)
    closing_time = db.Column(db.Time, nullable=True)

    # BUG FIX: lazy="dynamic" deprecated
    study_areas = db.relationship("StudyArea", back_populates="library", lazy="select")
    feedbacks = db.relationship("Feedback", back_populates="library", lazy="select")
    usage_stats = db.relationship("UsageStatistics", back_populates="library", lazy="select")

    @property
    def occupancy_percentage(self):
        if self.total_capacity == 0:
            return 0
        return round((self.current_occupancy / self.total_capacity) * 100, 1)

    def to_dict(self):
        # BUG FIX: opening_time / closing_time eksikti — frontend bu alanları kullanıyor
        return {
            "id": self.id,
            "name": self.name,
            "location": self.location,
            "total_capacity": self.total_capacity,
            "current_occupancy": self.current_occupancy,
            "occupancy_percentage": self.occupancy_percentage,
            "is_open": self.is_open,
            "opening_time": self.opening_time.strftime("%H:%M") if self.opening_time else None,
            "closing_time": self.closing_time.strftime("%H:%M") if self.closing_time else None,
            "study_areas": [a.to_dict() for a in self.study_areas] if self.study_areas else [],
        }

    def __repr__(self):
        return f"<Library {self.name}>"


class StudyArea(db.Model):
    __tablename__ = "study_areas"

    id = db.Column(db.Integer, primary_key=True)
    library_id = db.Column(db.Integer, db.ForeignKey("libraries.id"), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    total_seats = db.Column(db.Integer, nullable=False)
    available_seats = db.Column(db.Integer, nullable=False)
    area_type = db.Column(db.String(50), default="general")  # general, silent, group

    library = db.relationship("Library", back_populates="study_areas")
    # BUG FIX: lazy="dynamic" deprecated
    reservations = db.relationship("Reservation", back_populates="study_area", lazy="select")

    def to_dict(self):
        return {
            "id": self.id,
            "library_id": self.library_id,
            "name": self.name,
            "total_seats": self.total_seats,
            "available_seats": self.available_seats,
            "area_type": self.area_type,
        }

    def __repr__(self):
        return f"<StudyArea {self.name} @ Library {self.library_id}>"


class Reservation(db.Model):
    __tablename__ = "reservations"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    study_area_id = db.Column(db.Integer, db.ForeignKey("study_areas.id"), nullable=False)
    seat_number = db.Column(db.Integer, nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default="active")  # active, cancelled, completed
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship("User", back_populates="reservations")
    study_area = db.relationship("StudyArea", back_populates="reservations")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "study_area_id": self.study_area_id,
            "seat_number": self.seat_number,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "status": self.status,
            "created_at": self.created_at.isoformat(),
        }

    def __repr__(self):
        return f"<Reservation user={self.user_id} area={self.study_area_id} seat={self.seat_number}>"


class Feedback(db.Model):
    __tablename__ = "feedbacks"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    library_id = db.Column(db.Integer, db.ForeignKey("libraries.id"), nullable=False)
    reported_occupancy = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.String(500), nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship("User", back_populates="feedbacks")
    library = db.relationship("Library", back_populates="feedbacks")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "library_id": self.library_id,
            "reported_occupancy": self.reported_occupancy,
            "comment": self.comment,
            "created_at": self.created_at.isoformat(),
        }

    def __repr__(self):
        return f"<Feedback user={self.user_id} library={self.library_id}>"


class UsageStatistics(db.Model):
    __tablename__ = "usage_statistics"

    id = db.Column(db.Integer, primary_key=True)
    library_id = db.Column(db.Integer, db.ForeignKey("libraries.id"), nullable=False)
    recorded_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    occupancy_count = db.Column(db.Integer, nullable=False)
    occupancy_percentage = db.Column(db.Float, nullable=False)
    source = db.Column(db.String(20), default="simulation")  # simulation, sensor, feedback

    library = db.relationship("Library", back_populates="usage_stats")

    def to_dict(self):
        return {
            "id": self.id,
            "library_id": self.library_id,
            "recorded_at": self.recorded_at.isoformat(),
            "occupancy_count": self.occupancy_count,
            "occupancy_percentage": self.occupancy_percentage,
            "source": self.source,
        }

    def __repr__(self):
        return f"<UsageStatistics library={self.library_id} at={self.recorded_at}>"


class TokenBlocklist(db.Model):
    """Revoke edilmiş JWT tokenları saklar — restart sonrası da geçerli."""
    __tablename__ = "token_blocklist"

    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(36), unique=True, nullable=False, index=True)
    revoked_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<TokenBlocklist jti={self.jti}>"
