from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Feedback, Library, User
from database import db
from datetime import datetime, timezone, timedelta

feedback_bp = Blueprint("feedback", __name__)

RATE_LIMIT_MINUTES = 30


def _check_rate_limit(user_id: int, library_id: int) -> bool:
    """True döndürürse kullanıcı rate limit aşmış — feedback gönderilemez."""
    since = datetime.now(timezone.utc) - timedelta(minutes=RATE_LIMIT_MINUTES)
    recent = Feedback.query.filter(
        Feedback.user_id == user_id,
        Feedback.library_id == library_id,
        Feedback.created_at >= since,
    ).first()
    return recent is not None


@feedback_bp.route("/", methods=["POST"])
@jwt_required()
def submit_feedback():
    """
    Kütüphane için doluluk geri bildirimi gönderir.
    Aynı kullanıcı aynı kütüphane için 30 dakikada 1 feedback gönderebilir.
    ---
    tags:
      - Feedback
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [library_id, reported_occupancy]
          properties:
            library_id:
              type: integer
            reported_occupancy:
              type: integer
              description: 0-100 arası doluluk yüzdesi
            comment:
              type: string
    responses:
      201:
        description: Geri bildirim kaydedildi
      400:
        description: Geçersiz veri
      429:
        description: Rate limit aşıldı
    """
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}

    library_id = data.get("library_id")
    reported_occupancy = data.get("reported_occupancy")
    comment = (data.get("comment") or "").strip()

    if library_id is None or reported_occupancy is None:
        return jsonify({"error": "library_id ve reported_occupancy zorunludur"}), 400

    if not (0 <= int(reported_occupancy) <= 100):
        return jsonify({"error": "reported_occupancy 0-100 arasında olmalı"}), 400

    Library.query.get_or_404(library_id, description="Kütüphane bulunamadı")

    if _check_rate_limit(user_id, library_id):
        return jsonify({
            "error": f"Aynı kütüphane için {RATE_LIMIT_MINUTES} dakikada 1 feedback gönderilebilir"
        }), 429

    ip = request.remote_addr
    feedback = Feedback(
        user_id=user_id,
        library_id=library_id,
        reported_occupancy=int(reported_occupancy),
        comment=comment or None,
        ip_address=ip,
    )
    db.session.add(feedback)
    db.session.commit()

    return jsonify({"message": "Geri bildirim kaydedildi", "feedback": feedback.to_dict()}), 201


@feedback_bp.route("/<int:library_id>", methods=["GET"])
def get_library_feedback(library_id):
    """
    Belirli bir kütüphanenin son feedback'lerini döndürür.
    ---
    tags:
      - Feedback
    parameters:
      - name: library_id
        in: path
        type: integer
        required: true
      - name: limit
        in: query
        type: integer
        required: false
        description: Kaç kayıt (varsayılan 20)
    responses:
      200:
        description: Feedback listesi
      404:
        description: Kütüphane bulunamadı
    """
    Library.query.get_or_404(library_id, description="Kütüphane bulunamadı")
    limit = request.args.get("limit", default=20, type=int)

    feedbacks = (
        Feedback.query
        .filter_by(library_id=library_id)
        .order_by(Feedback.created_at.desc())
        .limit(limit)
        .all()
    )

    result = []
    for fb in feedbacks:
        d = fb.to_dict()
        user = User.query.get(fb.user_id)
        d["user_name"] = user.name if user else "Anonim"
        result.append(d)

    return jsonify({"feedbacks": result, "count": len(result)})
