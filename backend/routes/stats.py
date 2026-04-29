from flask import Blueprint, jsonify, request
from sqlalchemy import extract, cast, Date
from models import UsageStatistics, Library
from database import db
from datetime import datetime, timezone, timedelta
from routes.utils import admin_required

stats_bp = Blueprint("stats", __name__)


@stats_bp.route("/peak-hours", methods=["GET"])
@admin_required
def get_peak_hours():
    """
    Kütüphane başına günlük zirve saatlerini döndürür.
    ---
    tags:
      - Statistics
    security:
      - Bearer: []
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
      403:
        description: Yönetici yetkisi gerekli
    """
    library_id = request.args.get("library_id", type=int)
    days = request.args.get("days", default=7, type=int)

    # BUG FIX: datetime.utcnow() kullan — aware datetime SQLite naive UTC ile uyumsuz
    since = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days)

    # BUG FIX: func.strftime SQLite'a özgüydü; extract() tüm DB'lerde çalışır
    query = db.session.query(
        UsageStatistics.library_id,
        extract("hour", UsageStatistics.recorded_at).label("hour"),
        db.func.avg(UsageStatistics.occupancy_percentage).label("avg_pct"),
        db.func.max(UsageStatistics.occupancy_percentage).label("max_pct"),
    ).filter(UsageStatistics.recorded_at >= since)

    if library_id:
        query = query.filter(UsageStatistics.library_id == library_id)

    rows = query.group_by(
        UsageStatistics.library_id,
        extract("hour", UsageStatistics.recorded_at),
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

    peak_summary = []
    for lib_id, hours in result.items():
        lib = db.session.get(Library, lib_id)
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
@admin_required
def get_daily_usage():
    """
    Günlük ortalama doluluk istatistiklerini döndürür.
    ---
    tags:
      - Statistics
    security:
      - Bearer: []
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
      403:
        description: Yönetici yetkisi gerekli
    """
    library_id = request.args.get("library_id", type=int)
    days = request.args.get("days", default=7, type=int)

    # BUG FIX: datetime.utcnow() kullan — tutarlı naive UTC karşılaştırması
    since = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days)

    # BUG FIX: func.date() SQLite'a özgüydü; cast(..., Date) tüm DB'lerde çalışır
    day_col = cast(UsageStatistics.recorded_at, Date).label("day")

    query = db.session.query(
        UsageStatistics.library_id,
        day_col,
        db.func.avg(UsageStatistics.occupancy_percentage).label("avg_pct"),
        db.func.max(UsageStatistics.occupancy_percentage).label("max_pct"),
        db.func.min(UsageStatistics.occupancy_percentage).label("min_pct"),
    ).filter(UsageStatistics.recorded_at >= since)

    if library_id:
        query = query.filter(UsageStatistics.library_id == library_id)

    rows = query.group_by(
        UsageStatistics.library_id,
        day_col,
    ).order_by(day_col).all()

    result = {}
    for row in rows:
        lib_id = row.library_id
        if lib_id not in result:
            lib = db.session.get(Library, lib_id)
            result[lib_id] = {
                "library_id": lib_id,
                "library_name": lib.name if lib else str(lib_id),
                "daily_data": [],
            }
        result[lib_id]["daily_data"].append({
            "date": str(row.day),
            "avg_pct": round(row.avg_pct, 1),
            "max_pct": round(row.max_pct, 1),
            "min_pct": round(row.min_pct, 1),
        })

    return jsonify({
        "daily_usage": list(result.values()),
        "days_analyzed": days,
    })
