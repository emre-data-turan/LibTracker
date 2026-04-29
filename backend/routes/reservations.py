from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Reservation, StudyArea
from database import db
from datetime import datetime, timezone

reservations_bp = Blueprint("reservations", __name__)


def _to_naive_utc(dt: datetime) -> datetime:
    """
    Aware datetime'ı naive UTC'ye dönüştürür.
    Naive datetime UTC kabul edilir (SQLite'ın depolama biçimiyle tutarlı).
    """
    if dt.tzinfo is None:
        return dt
    return dt.astimezone(timezone.utc).replace(tzinfo=None)


def _has_conflict(study_area_id: int, seat_number: int, start: datetime, end: datetime, exclude_id: int = None) -> bool:
    """
    Aynı koltuk için çakışan aktif rezervasyon var mı?
    İki zaman dilimi çakışır: start1 < end2 AND start2 < end1
    """
    query = Reservation.query.filter(
        Reservation.study_area_id == study_area_id,
        Reservation.seat_number == seat_number,
        Reservation.status == "active",
        Reservation.start_time < end,
        Reservation.end_time > start,
    )
    if exclude_id:
        query = query.filter(Reservation.id != exclude_id)
    return query.first() is not None


@reservations_bp.route("/", methods=["POST"])
@jwt_required()
def create_reservation():
    """
    Yeni koltuk rezervasyonu oluşturur.
    ---
    tags:
      - Reservations
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [study_area_id, seat_number, start_time, end_time]
          properties:
            study_area_id:
              type: integer
            seat_number:
              type: integer
            start_time:
              type: string
              example: "2026-05-10T10:00:00"
            end_time:
              type: string
              example: "2026-05-10T12:00:00"
    responses:
      201:
        description: Rezervasyon oluşturuldu
      400:
        description: Geçersiz veri
      409:
        description: Koltuk bu saatte zaten dolu
    """
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}

    study_area_id = data.get("study_area_id")
    seat_number = data.get("seat_number")
    start_str = data.get("start_time")
    end_str = data.get("end_time")

    if not all([study_area_id, seat_number, start_str, end_str]):
        return jsonify({"error": "study_area_id, seat_number, start_time, end_time zorunludur"}), 400

    try:
        start = _to_naive_utc(datetime.fromisoformat(start_str))
        end = _to_naive_utc(datetime.fromisoformat(end_str))
    except ValueError:
        return jsonify({"error": "Tarih formatı hatalı (ISO 8601 kullanın)"}), 400

    if end <= start:
        return jsonify({"error": "end_time, start_time'dan sonra olmalı"}), 400

    # BUG FIX: naive UTC ile karşılaştır — aware/naive karışımı TypeError'a yol açıyordu
    if start < datetime.now(timezone.utc).replace(tzinfo=None):
        return jsonify({"error": "Geçmiş bir zaman için rezervasyon yapılamaz"}), 400

    area = db.get_or_404(StudyArea, study_area_id, description="Çalışma alanı bulunamadı")

    if seat_number < 1 or seat_number > area.total_seats:
        return jsonify({"error": f"Koltuk numarası 1-{area.total_seats} arasında olmalı"}), 400

    if _has_conflict(study_area_id, seat_number, start, end):
        return jsonify({"error": "Bu koltuk seçilen saatte zaten rezerve edilmiş"}), 409

    reservation = Reservation(
        user_id=user_id,
        study_area_id=study_area_id,
        seat_number=seat_number,
        start_time=start,
        end_time=end,
    )
    db.session.add(reservation)
    db.session.flush()
    active_count = Reservation.query.filter_by(study_area_id=study_area_id, status="active").count()
    area.available_seats = max(0, area.total_seats - active_count)

    db.session.commit()
    return jsonify({"message": "Rezervasyon oluşturuldu", "reservation": reservation.to_dict()}), 201


@reservations_bp.route("/user/<int:user_id>", methods=["GET"])
@jwt_required()
def get_user_reservations(user_id):
    """
    Kullanıcının aktif rezervasyonlarını listeler.
    ---
    tags:
      - Reservations
    security:
      - Bearer: []
    parameters:
      - name: user_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Rezervasyon listesi
      403:
        description: Başkasının rezervasyonlarına erişim yasak
    """
    current_user_id = int(get_jwt_identity())
    if current_user_id != user_id:
        return jsonify({"error": "Başkasının rezervasyonlarını görüntüleyemezsiniz"}), 403

    reservations = (
        Reservation.query
        .filter_by(user_id=user_id, status="active")
        .order_by(Reservation.start_time)
        .all()
    )
    return jsonify({
        "reservations": [r.to_dict() for r in reservations],
        "count": len(reservations),
    })


@reservations_bp.route("/<int:reservation_id>", methods=["DELETE"])
@jwt_required()
def cancel_reservation(reservation_id):
    """
    Rezervasyonu iptal eder.
    ---
    tags:
      - Reservations
    security:
      - Bearer: []
    parameters:
      - name: reservation_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Rezervasyon iptal edildi
      403:
        description: Bu rezervasyon size ait değil
      404:
        description: Rezervasyon bulunamadı
    """
    current_user_id = int(get_jwt_identity())
    reservation = db.get_or_404(Reservation, reservation_id, description="Rezervasyon bulunamadı")

    if reservation.user_id != current_user_id:
        return jsonify({"error": "Bu rezervasyon size ait değil"}), 403

    reservation.status = "cancelled"
    area = db.session.get(StudyArea, reservation.study_area_id)
    if area:
        db.session.flush()
        active_count = Reservation.query.filter_by(study_area_id=reservation.study_area_id, status="active").count()
        area.available_seats = max(0, area.total_seats - active_count)

    db.session.commit()
    return jsonify({"message": "Rezervasyon iptal edildi"})
