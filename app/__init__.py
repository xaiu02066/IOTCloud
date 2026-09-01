"""应用工厂：创建并初始化 Flask 应用。

注意：本文件仅做项目骨架搭建，F1~F9 的业务逻辑后续在各子包中实现。
"""
from flask import Flask, jsonify

from app.config import config_map
from app.extensions import cache, cors, db, jwt, socketio


def create_app(config_name: str = "development") -> Flask:
    """应用工厂函数。

    Args:
        config_name: 配置环境名，对应 app.config.config_map 中的 key。
    """
    app = Flask(__name__)
    config_class = config_map.get(config_name, config_map["default"])
    app.config.from_object(config_class)

    # 初始化扩展（不连接外部服务，仅完成绑定）
    db.init_app(app)
    jwt.init_app(app)
    cors.init_app(app)
    cache.init_app(app)
    socketio.init_app(app)

    # ---- 健康检查 / 根路由（骨架占位，便于启动验证） ----
    @app.route("/health")
    def health():
        return jsonify({"status": "ok", "service": "iotcloud"}), 200

    @app.route("/")
    def index():
        return jsonify({
            "message": "IOTCloud 智慧农业环境监控平台 API",
            "docs": "见 docs/需求清单初稿.md",
        }), 200

    # ---- 注册蓝图 ----
    # F1 用户管理（注册 / 登录 / 当前用户）
    from app.api.auth import auth_bp

    app.register_blueprint(auth_bp)
    # TODO: 后续在此注册其它蓝图
    #   from app.api import product_bp, device_bp, thing_model_bp, ...
    #   app.register_blueprint(product_bp)
    return app
