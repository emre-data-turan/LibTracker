from flask import Blueprint, jsonify, request
from sqlalchemy import func
from models import UsageStatistics, Library, Reservation, User, Feedback
from database import db
from datetime import datetime, timezone, timedelta
from flask_jwt_extended import jwt_required, get_jwt_identity

stats_bp = Blueprint("stats", __name__)

@stats_bp.route("/overview", methods=["GET"])
@jwt_required()
def get_overview():
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)
    if not user or not user.is_admin:
        return jsonify({"error": "Yetkisiz erişim"}), 403

    current_occupants = db.session.query(func.sum(Library.current_occupancy)).scalar() or 0
    active_reservations = Reservation.query.filter_by(status="active").count()
    total_feedbacks = db.session.query(func.count(Feedback.id)).scalar() or 0

    return jsonify({
        "current_occupants": int(current_occupants),
        "active_reservations": active_reservations,
        "total_feedbacks": total_feedbacks
    })


@stats_bp.route("/peak-hours", methods=["GET"])
def get_peak_hours():
    """
    Kütüphane başına günlük zirve saatlerini döndürür.
    ---
    tags:
      - Statistics
    parameters:
      - name: library_id
        in: query
        type: integer
        required: false
        description: Belirli bir kütüphane için filtrele (boşsa hepsi)
      - name: days
        in: query
        type: integer
        required: false
        description: Kaç günlük veri (varsayılan 7)
    responses:
      200:
        description: Saat bazında ortalama doluluk yüzdeleri
    """
    library_id = request.args.get("library_id", type=int)
    days = request.args.get("days", default=7, type=int)

    since = datetime.now(timezone.utc) - timedelta(days=days)

    query = db.session.query(
        UsageStatistics.library_id,
        func.strftime("%H", UsageStatistics.recorded_at).label("hour"),
        func.avg(UsageStatistics.occupancy_percentage).label("avg_pct"),
        func.max(UsageStatistics.occupancy_percentage).label("max_pct"),
    ).filter(UsageStatistics.recorded_at >= since)

    if library_id:
        query = query.filter(UsageStatistics.library_id == library_id)

    rows = query.group_by(
        UsageStatistics.library_id,
        func.strftime("%H", UsageStatistics.recorded_at),
    ).all()

    result = {}
    for row in rows:
        lib_id = row.library_id
        if lib_id not in result:
            result[lib_id] = []
        result[lib_id].append({
            "hour": int(row.hour),
            "avg_occupancy_pct": round(row.avg_pct, 1),
            "max_occupancy_pct": round(row.max_pct, 1),
        })

    # Her kütüphane için zirvesaatini hesapla
    peak_summary = []
    for lib_id, hours in result.items():
        lib = Library.query.get(lib_id)
        if not lib:
            continue
        peak = max(hours, key=lambda h: h["avg_occupancy_pct"])
        peak_summary.append({
            "library_id": lib_id,
            "library_name": lib.name,
            "peak_hour": peak["hour"],
            "peak_avg_pct": peak["avg_occupancy_pct"],
            "hourly_data": sorted(hours, key=lambda h: h["hour"]),
        })

    return jsonify({"peak_hours": peak_summary, "days_analyzed": days})


@stats_bp.route("/daily-usage", methods=["GET"])
def get_daily_usage():
    """
    Günlük ortalama doluluk istatistiklerini döndürür.
    ---
    tags:
      - Statistics
    parameters:
      - name: library_id
        in: query
        type: integer
        required: false
      - name: days
        in: query
        type: integer
        required: false
        description: Kaç günlük veri (varsayılan 7)
    responses:
      200:
        description: Gün bazında doluluk istatistikleri
    """
    library_id = request.args.get("library_id", type=int)
    days = request.args.get("days", default=7, type=int)

    since = datetime.now(timezone.utc) - timedelta(days=days)

    query = db.session.query(
        UsageStatistics.library_id,
        func.date(UsageStatistics.recorded_at).label("day"),
        func.avg(UsageStatistics.occupancy_percentage).label("avg_pct"),
        func.max(UsageStatistics.occupancy_percentage).label("max_pct"),
        func.min(UsageStatistics.occupancy_percentage).label("min_pct"),
    ).filter(UsageStatistics.recorded_at >= since)

    if library_id:
        query = query.filter(UsageStatistics.library_id == library_id)

    rows = query.group_by(
        UsageStatistics.library_id,
        func.date(UsageStatistics.recorded_at),
    ).order_by(func.date(UsageStatistics.recorded_at)).all()

    result = {}
    for row in rows:
        lib_id = row.library_id
        if lib_id not in result:
            lib = Library.query.get(lib_id)
            result[lib_id] = {
                "library_id": lib_id,
                "library_name": lib.name if lib else str(lib_id),
                "daily_data": [],
            }
        result[lib_id]["daily_data"].append({
            "date": row.day,
            "avg_pct": round(row.avg_pct, 1),
            "max_pct": round(row.max_pct, 1),
            "min_pct": round(row.min_pct, 1),
        })

    return jsonify({
        "daily_usage": list(result.values()),
        "days_analyzed": days,
    })
