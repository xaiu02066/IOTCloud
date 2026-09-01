"""User 模型（F1 用户管理 / F9 RBAC 角色）。

仅定义数据模型与密码处理方法，注册/登录逻辑在 app.api.auth 中。
"""
from datetime import datetime

from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db


class User(db.Model):
    """平台用户。"""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    # F9 RBAC：角色（admin / user 等），默认普通用户
    role = db.Column(db.String(32), nullable=False, default="user")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password: str) -> None:
        """对明文密码加盐哈希后存储。"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """校验明文密码是否匹配。"""
        return check_password_hash(self.password_hash, password)

    def to_dict(self) -> dict:
        """序列化为字典（不暴露密码）。"""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
