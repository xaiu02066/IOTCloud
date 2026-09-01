"""数据模型包。

在此集中导入各模型，确保 app 启动时它们被 SQLAlchemy 元数据登记，
便于后续 db.create_all() / 迁移工具发现。
"""
from app.models.user import User

__all__ = ["User"]
