from functools import wraps
from flask import jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from database import db


def admin_required(fn):
    """JWT doğrulaması + admin yetkisi kontrolü birleşik decorator."""
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        from models import User
        user_id = int(get_jwt_identity())
        user = db.session.get(User, user_id)
        if not user or not user.is_admin:
            return jsonify({"error": "Yönetici yetkisi gerekli"}), 403
        return fn(*args, **kwargs)
    return wrapper
