"""应用配置。

所有敏感信息均通过环境变量读取，并提供本地开发默认值。
正式部署时请通过 .env 或系统环境变量覆盖。
"""
import os
from datetime import timedelta


class Config:
    """基础配置。"""

    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")

    # ---- Flask ----
    DEBUG = False

    # ---- MySQL（业务数据：用户 / 产品 / 设备 / 权限 / 告警） ----
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://root:root@localhost:3306/iotcloud?charset=utf8mb4",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True, "pool_recycle": 3600}

    # ---- JWT（F1 注册/登录，F9 RBAC） ----
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret-change-me")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=2)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)
    JWT_TOKEN_LOCATION = ["headers"]
    JWT_HEADER_NAME = "Authorization"
    JWT_HEADER_TYPE = "Bearer"

    # ---- InfluxDB（F5 时序数据） ----
    INFLUXDB_URL = os.getenv("INFLUXDB_URL", "http://localhost:8086")
    INFLUXDB_TOKEN = os.getenv("INFLUXDB_TOKEN", "")
    INFLUXDB_ORG = os.getenv("INFLUXDB_ORG", "iotcloud")
    INFLUXDB_BUCKET = os.getenv("INFLUXDB_BUCKET", "telemetry")

    # ---- Redis（缓存 / 限流 / F8 告警去重） ----
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CACHE_TYPE = "RedisCache"
    CACHE_REDIS_URL = REDIS_URL
    CACHE_DEFAULT_TIMEOUT = 300

    # ---- MQTT（EMQX，F5 上报 / F6 指令下发） ----
    MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
    MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
    MQTT_CLIENT_ID = os.getenv("MQTT_CLIENT_ID", "iotcloud-backend")

    # ---- SocketIO（F7 实时推送） ----
    SOCKETIO_ASYNC_MODE = "threading"
    SOCKETIO_CORS_ALLOWED_ORIGINS = os.getenv("CORS_ORIGINS", "*")


class DevelopmentConfig(Config):
    """开发环境配置。"""

    DEBUG = True


class ProductionConfig(Config):
    """生产环境配置。"""

    DEBUG = False


config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
