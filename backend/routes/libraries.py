from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Library, StudyArea, User, Reservation, Feedback, UsageStatistics
from database import db
from datetime import datetime, timezone, timedelta

libraries_bp = Blueprint("libraries", __name__)


@libraries_bp.route("/", methods=["GET"])
def get_libraries():
    """
    Tüm kütüphaneleri anlık doluluk bilgisiyle listeler.
    ---
    tags:
      - Libraries
    responses:
      200:
        description: Kütüphane listesi
        schema:
          type: object
          properties:
            libraries:
              type: array
            total:
              type: integer
            avg_occupancy_pct:
              type: number
    """
    libs = Library.query.filter_by(is_open=True).all()
    total_free = sum(l.total_capacity - l.current_occupancy for l in libs)
    avg_pct = round(
        sum(l.occupancy_percentage for l in libs) / len(libs), 1
    ) if libs else 0
    available_count = sum(1 for l in libs if l.occupancy_percentage < 80)

    two_hours_ago = datetime.now(timezone.utc) - timedelta(hours=2)
    busy_feedbacks = db.session.query(
        Feedback.library_id, db.func.count(Feedback.id)
    ).filter(
        Feedback.created_at >= two_hours_ago,
        Feedback.reported_occupancy >= 80
    ).group_by(Feedback.library_id).all()
    
    busy_library_ids = {lib_id for lib_id, count in busy_feedbacks if count >= 3}
    
    libs_data = []
    for l in libs:
        d = l.to_dict()
        d["is_busy_notice"] = l.id in busy_library_ids
        libs_data.append(d)

    return jsonify({
        "libraries": libs_data,
        "total": len(libs),
        "available_count": available_count,
        "avg_occupancy_pct": avg_pct,
        "total_free_seats": total_free,
    })


@libraries_bp.route("/<int:library_id>/occupancy", methods=["GET"])
def get_library_occupancy(library_id):
    """
    Belirli bir kütüphanenin anlık doluluk detayını döndürür.
    ---
    tags:
      - Libraries
    parameters:
      - name: library_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Doluluk detayı
      404:
        description: Kütüphane bulunamadı
    """
    lib = Library.query.get_or_404(library_id, description="Kütüphane bulunamadı")
    areas = StudyArea.query.filter_by(library_id=library_id).all()

    return jsonify({
        "library": lib.to_dict(),
        "study_areas": [a.to_dict() for a in areas],
        "total_available_seats": sum(a.available_seats for a in areas),
    })


@libraries_bp.route("/", methods=["POST"])
@jwt_required()
def create_library():
    """
    Sadece adminlerin yeni kütüphane eklemesi için.
    """
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user or not user.is_admin:
        return jsonify({"error": "Unauthorized"}), 403

    data = request.get_json() or {}
    name = data.get("name")
    location = data.get("location", "Bilinmiyor")
    try:
        capacity = int(data.get("total_capacity", 0))
    except (ValueError, TypeError):
        return jsonify({"error": "total_capacity geçerli bir sayı olmalı"}), 400

    if not name or capacity <= 0:
        return jsonify({"error": "Geçerli isim ve kapasite giriniz"}), 400

    lib = Library(name=name, location=location, total_capacity=capacity, current_occupancy=0, is_open=True)
    db.session.add(lib)
    db.session.commit()

    # Varsayılan çalışma alanları ekle (3 alan)
    area_types = ["general", "silent", "group"]
    base_seats = capacity // 3
    rem = capacity % 3
    for i, atype in enumerate(area_types, 1):
        seats = base_seats + (1 if i <= rem else 0)
        area = StudyArea(
            library_id=lib.id,
            name=f"{atype.capitalize()} Alan {i}",
            total_seats=seats,
            available_seats=seats,
            area_type=atype,
        )
        db.session.add(area)
    db.session.commit()

    return jsonify({"message": "Kütüphane oluşturuldu", "library": lib.to_dict()}), 201


@libraries_bp.route("/<int:library_id>", methods=["PUT"])
@jwt_required()
def update_library(library_id):
    """
    Sadece adminlerin kütüphane kapasite/doluluk güncellemesi için.
    """
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user or not user.is_admin:
        return jsonify({"error": "Unauthorized"}), 403

    lib = Library.query.get_or_404(library_id)
    data = request.get_json() or {}

    if "name" in data:
        lib.name = data["name"]
    if "location" in data:
        lib.location = data["location"]
    
    old_capacity = lib.total_capacity
    if "total_capacity" in data:
        try:
            lib.total_capacity = int(data["total_capacity"])
        except (ValueError, TypeError):
            return jsonify({"error": "total_capacity geçerli bir sayı olmalı"}), 400
    if "current_occupancy" in data:
        try:
            new_occ = int(data["current_occupancy"])
        except (ValueError, TypeError):
            return jsonify({"error": "current_occupancy geçerli bir sayı olmalı"}), 400
        if new_occ > lib.total_capacity:
            return jsonify({"error": "current_occupancy kapasitenin üzerinde olamaz"}), 400
        lib.current_occupancy = new_occ

    if lib.total_capacity != old_capacity:
        areas = StudyArea.query.filter_by(library_id=lib.id).all()
        if areas:
            new_seats_per_area = lib.total_capacity // len(areas)
            for area in areas:
                active_count = Reservation.query.filter_by(study_area_id=area.id, status="active").count()
                area.total_seats = new_seats_per_area
                area.available_seats = max(0, new_seats_per_area - active_count)

    db.session.commit()
    return jsonify({"message": "Kütüphane güncellendi", "library": lib.to_dict()})


@libraries_bp.route("/<int:library_id>", methods=["DELETE"])
@jwt_required()
def delete_library(library_id):
    """
    Sadece adminlerin kütüphane silmesi için. İlgili tüm kayıtlar silinir.
    """
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user or not user.is_admin:
        return jsonify({"error": "Unauthorized"}), 403

    lib = Library.query.get_or_404(library_id)
    
    # Cascade deletes
    Feedback.query.filter_by(library_id=lib.id).delete()
    UsageStatistics.query.filter_by(library_id=lib.id).delete()
    
    areas = StudyArea.query.filter_by(library_id=lib.id).all()
    for area in areas:
        Reservation.query.filter_by(study_area_id=area.id).delete()
        db.session.delete(area)
        
    db.session.delete(lib)
    db.session.commit()
    
    return jsonify({"message": "Kütüphane ve ilişkili tüm veriler silindi"})
