from flask import Blueprint, jsonify, request
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt,
    get_jwt_identity,
)
from werkzeug.security import generate_password_hash, check_password_hash
from models import User, Reservation, Feedback, TokenBlocklist
from database import db
import re

auth_bp = Blueprint("auth", __name__)

UNIVERSITY_EMAIL_PATTERN = re.compile(
    r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.(edu\.tr|edu|ac\.uk|uni\.[a-z]+)$"
)


def _is_university_email(email: str) -> bool:
    return bool(UNIVERSITY_EMAIL_PATTERN.match(email))


@auth_bp.route("/register", methods=["POST"])
def register():
    """
    Yeni öğrenci kaydı. Yalnızca üniversite e-postası kabul edilir.
    ---
    tags:
      - Auth
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [name, email, password]
          properties:
            name:
              type: string
            email:
              type: string
              example: student@university.edu.tr
            password:
              type: string
    responses:
      201:
        description: Kayıt başarılı
      400:
        description: Geçersiz veri veya e-posta
      409:
        description: E-posta zaten kayıtlı
    """
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not name or not email or not password:
        return jsonify({"error": "name, email ve password zorunludur"}), 400

    if len(password) < 6:
        return jsonify({"error": "Şifre en az 6 karakter olmalı"}), 400

    if not _is_university_email(email):
        return jsonify({
            "error": "Yalnızca üniversite e-postası kabul edilir (.edu.tr, .edu, .ac.uk)"
        }), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Bu e-posta zaten kayıtlı"}), 409

    user = User(
        name=name,
        email=email,
        password_hash=generate_password_hash(password),
        is_verified=True,
    )
    db.session.add(user)
    db.session.commit()

    token = create_access_token(identity=str(user.id))
    return jsonify({"message": "Kayıt başarılı", "token": token, "user": user.to_dict()}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    """
    Kullanıcı girişi. JWT token döndürür.
    ---
    tags:
      - Auth
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [email, password]
          properties:
            email:
              type: string
            password:
              type: string
    responses:
      200:
        description: Giriş başarılı, JWT token
      401:
        description: Geçersiz kimlik bilgileri
    """
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"error": "E-posta veya şifre hatalı"}), 401

    token = create_access_token(identity=str(user.id))
    return jsonify({"token": token, "user": user.to_dict()})


@auth_bp.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    """
    Oturumu kapatır. Token blocklist'e eklenir.
    ---
    tags:
      - Auth
    security:
      - Bearer: []
    responses:
      200:
        description: Oturum kapatıldı
      401:
        description: Token geçersiz
    """
    jti = get_jwt()["jti"]
    db.session.add(TokenBlocklist(jti=jti))
    db.session.commit()
    return jsonify({"message": "Oturum kapatıldı"})


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    """
    Mevcut kullanıcı bilgilerini döndürür.
    ---
    tags:
      - Auth
    security:
      - Bearer: []
    responses:
      200:
        description: Kullanıcı bilgisi
    """
    user_id = int(get_jwt_identity())
    # BUG FIX: Query.get_or_404() deprecated — db.get_or_404() kullan
    user = db.get_or_404(User, user_id)
    return jsonify({"user": user.to_dict()})


@auth_bp.route("/me/password", methods=["PUT"])
@jwt_required()
def update_password():
    """
    Kullanıcı şifresini günceller.
    ---
    tags:
      - Auth
    security:
      - Bearer: []
    """
    user_id = int(get_jwt_identity())
    user = db.get_or_404(User, user_id)

    data = request.get_json() or {}
    old_password = data.get("old_password")
    new_password = data.get("new_password")
    
    if not old_password or not new_password:
        return jsonify({"error": "old_password ve new_password zorunludur"}), 400
        
    if not check_password_hash(user.password_hash, old_password):
        return jsonify({"error": "Eski şifre hatalı"}), 401
        
    if len(new_password) < 6:
        return jsonify({"error": "Yeni şifre en az 6 karakter olmalı"}), 400
        
    user.password_hash = generate_password_hash(new_password)
    db.session.commit()
    return jsonify({"message": "Şifre başarıyla güncellendi"})


@auth_bp.route("/me", methods=["DELETE"])
@jwt_required()
def delete_account():
    """
    Kullanıcı hesabını ve ilişkili tüm verilerini siler.
    ---
    tags:
      - Auth
    security:
      - Bearer: []
    """
    user_id = int(get_jwt_identity())
    user = db.get_or_404(User, user_id)

    # Cascade deletes
    Reservation.query.filter_by(user_id=user.id).delete()
    Feedback.query.filter_by(user_id=user.id).delete()
    
    db.session.delete(user)
    db.session.commit()
    
    jti = get_jwt()["jti"]
    db.session.add(TokenBlocklist(jti=jti))
    db.session.commit()
    
    return jsonify({"message": "Hesap ve ilişkili tüm veriler başarıyla silindi"})


def is_token_revoked(jwt_header, jwt_payload) -> bool:
    """Flask-JWT-Extended token_in_blocklist_loader için callback."""
    jti = jwt_payload.get("jti")
    return TokenBlocklist.query.filter_by(jti=jti).first() is not None
