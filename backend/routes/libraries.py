from flask import Blueprint, jsonify
from models import Library, StudyArea
from database import db

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

    return jsonify({
        "libraries": [l.to_dict() for l in libs],
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
