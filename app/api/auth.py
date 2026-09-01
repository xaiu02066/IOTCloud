"""F1 用户管理：注册 / 登录 / 当前用户（JWT）。

说明：
- 密码使用 werkzeug 加盐哈希，不存明文。
- 登录成功签发 access_token（2h）与 refresh_token（7d），前端后续请求在
  Authorization 头携带 `Bearer <access_token>`。
- /me 演示 @jwt_required() 受保护接口，作为 F9 RBAC 的接入点。
"""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    jwt_required,
)

from app.extensions import db
from app.models import User

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.route("/register", methods=["POST"])
def register():
    """用户注册。"""
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    email = (data.get("email") or "").strip() or None
    role = (data.get("role") or "user").strip()

    if not username or not password:
        return jsonify({"msg": "用户名和密码不能为空"}), 400
    if len(password) < 6:
        return jsonify({"msg": "密码长度至少 6 位"}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({"msg": "用户名已存在"}), 409

    user = User(username=username, email=email, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return jsonify({"msg": "注册成功", "user": user.to_dict()}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    """用户登录，返回 JWT。"""
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify({"msg": "用户名或密码错误"}), 401

    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))
    return jsonify({
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "Bearer",
        "user": user.to_dict(),
    }), 200


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    """获取当前登录用户信息（受保护接口）。"""
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    if not user:
        return jsonify({"msg": "用户不存在"}), 404
    return jsonify(user.to_dict()), 200
