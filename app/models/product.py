"""产品与物模型 SQLAlchemy 模型 (F2 产品管理 / F3 物模型)。

表结构对应 db/init_iotcloud.sql：
- products（含 thing_model JSON 完整物模型快照）
- product_properties / product_services / product_events（关系表）
"""
from app.extensions import db
from sqlalchemy import JSON


class Product(db.Model):
    """产品（含完整物模型 JSON 快照）。"""

    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    product_key = db.Column(db.String(64), unique=True, nullable=False, index=True)
    product_name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.String(255))
    protocol = db.Column(db.String(32), default="MQTT")
    thing_model = db.Column(JSON)  # 完整物模型快照，前端一次加载
    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())
    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp(),
    )

    properties = db.relationship(
        "ProductProperty", backref="product", cascade="all, delete-orphan"
    )
    services = db.relationship(
        "ProductService", backref="product", cascade="all, delete-orphan"
    )
    events = db.relationship(
        "ProductEvent", backref="product", cascade="all, delete-orphan"
    )

    def to_dict(self, with_model: bool = False) -> dict:
        data = {
            "id": self.id,
            "product_key": self.product_key,
            "product_name": self.product_name,
            "description": self.description,
            "protocol": self.protocol,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if with_model:
            data["thing_model"] = self.thing_model
            data["properties"] = [p.to_dict() for p in self.properties]
            data["services"] = [s.to_dict() for s in self.services]
            data["events"] = [e.to_dict() for e in self.events]
        return data


class ProductProperty(db.Model):
    """物模型-属性定义。"""

    __tablename__ = "product_properties"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False, index=True)
    property_name = db.Column(db.String(128), nullable=False)
    identifier = db.Column(db.String(64), nullable=False)
    data_type = db.Column(db.String(32), nullable=False)
    unit = db.Column(db.String(16))
    access_mode = db.Column(db.String(8), default="r")  # r=只读, rw=读写
    description = db.Column(db.String(255))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "product_id": self.product_id,
            "property_name": self.property_name,
            "identifier": self.identifier,
            "data_type": self.data_type,
            "unit": self.unit,
            "access_mode": self.access_mode,
            "description": self.description,
        }


class ProductService(db.Model):
    """物模型-服务定义。"""

    __tablename__ = "product_services"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False, index=True)
    service_name = db.Column(db.String(128), nullable=False)
    identifier = db.Column(db.String(64), nullable=False)
    input_params = db.Column(JSON)    # 输入参数定义
    output_params = db.Column(JSON)   # 输出参数定义
    description = db.Column(db.String(255))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "product_id": self.product_id,
            "service_name": self.service_name,
            "identifier": self.identifier,
            "input_params": self.input_params,
            "output_params": self.output_params,
            "description": self.description,
        }


class ProductEvent(db.Model):
    """物模型-事件定义。"""

    __tablename__ = "product_events"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False, index=True)
    event_name = db.Column(db.String(128), nullable=False)
    identifier = db.Column(db.String(64), nullable=False)
    trigger_position = db.Column(db.String(16))    # 设备端 / 平台
    output_params = db.Column(JSON)                # 输出参数定义
    trigger_condition = db.Column(db.String(255))  # 触发条件
    description = db.Column(db.String(255))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "product_id": self.product_id,
            "event_name": self.event_name,
            "identifier": self.identifier,
            "trigger_position": self.trigger_position,
            "output_params": self.output_params,
            "trigger_condition": self.trigger_condition,
            "description": self.description,
        }
