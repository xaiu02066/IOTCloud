"""扩展实例集中管理。

所有 Flask 扩展在这里实例化，在 create_app 中通过 init_app 绑定到应用，
避免循环导入，并便于后续各模块共享同一实例。
"""
from flask_caching import Cache
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
jwt = JWTManager()
cors = CORS()
cache = Cache()
socketio = SocketIO(cors_allowed_origins="*")
