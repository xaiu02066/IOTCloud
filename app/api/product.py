"""F2 产品管理 / F3 物模型：产品与物模型 CRUD API。

路由设计：
- 产品本身：/api/products  (列表/创建) , /api/products/<id> (详情/更新/删除)
- 物模型（属性/服务/事件）作为产品的子资源：/api/products/<id>/properties|services|events
- 物模型聚合快照：/api/products/<id>/thing-model （前端一次加载用）

所有接口均需 JWT（Authorization: Bearer <token>），F9 RBAC 后续可在本层叠加角色校验。
"""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from app.extensions import db
from app.models import (
    Product,
    ProductProperty,
    ProductService,
    ProductEvent,
)

product_bp = Blueprint("product", __name__, url_prefix="/api/products")


# ============================================================
# 产品 CRUD
# ============================================================
@product_bp.route("", methods=["GET"])
@jwt_required()
def list_products():
    """产品列表（分页 + 关键字搜索）。"""
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 20, type=int), 100)
    keyword = (request.args.get("keyword") or "").strip()

    q = Product.query
    if keyword:
        like = f"%{keyword}%"
        q = q.filter(
            db.or_(
                Product.product_name.like(like),
                Product.product_key.like(like),
            )
        )
    pagination = q.paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        "items": [p.to_dict() for p in pagination.items],
        "total": pagination.total,
        "page": page,
        "per_page": per_page,
        "pages": pagination.pages,
    }), 200


@product_bp.route("", methods=["POST"])
@jwt_required()
def create_product():
    """创建产品。"""
    data = request.get_json(silent=True) or {}
    product_key = (data.get("product_key") or "").strip()
    product_name = (data.get("product_name") or "").strip()
    if not product_key or not product_name:
        return jsonify({"msg": "product_key 和 product_name 不能为空"}), 400
    if Product.query.filter_by(product_key=product_key).first():
        return jsonify({"msg": "产品标识已存在"}), 409

    product = Product(
        product_key=product_key,
        product_name=product_name,
        description=data.get("description"),
        protocol=data.get("protocol", "MQTT"),
        thing_model=data.get("thing_model"),
    )
    db.session.add(product)
    db.session.commit()
    return jsonify({"msg": "创建成功", "product": product.to_dict()}), 201


@product_bp.route("/<int:pid>", methods=["GET"])
@jwt_required()
def get_product(pid):
    """产品详情（含完整物模型与子资源）。"""
    product = Product.query.get_or_404(pid)
    return jsonify(product.to_dict(with_model=True)), 200


@product_bp.route("/<int:pid>", methods=["PUT"])
@jwt_required()
def update_product(pid):
    """更新产品。"""
    product = Product.query.get_or_404(pid)
    data = request.get_json(silent=True) or {}

    if "product_key" in data and data["product_key"] != product.product_key:
        if Product.query.filter_by(product_key=data["product_key"]).first():
            return jsonify({"msg": "产品标识已存在"}), 409
        product.product_key = data["product_key"]
    for field in ("product_name", "description", "protocol", "thing_model"):
        if field in data:
            setattr(product, field, data[field])

    db.session.commit()
    return jsonify({"msg": "更新成功", "product": product.to_dict()}), 200


@product_bp.route("/<int:pid>", methods=["DELETE"])
@jwt_required()
def delete_product(pid):
    """删除产品（级联删除其属性/服务/事件）。"""
    product = Product.query.get_or_404(pid)
    db.session.delete(product)
    db.session.commit()
    return jsonify({"msg": "删除成功"}), 200


@product_bp.route("/<int:pid>/thing-model", methods=["GET"])
@jwt_required()
def thing_model(pid):
    """物模型聚合快照（前端一次加载）。"""
    product = Product.query.get_or_404(pid)
    return jsonify({
        "product_key": product.product_key,
        "product_name": product.product_name,
        "thing_model": product.thing_model,
        "properties": [p.to_dict() for p in product.properties],
        "services": [s.to_dict() for s in product.services],
        "events": [e.to_dict() for e in product.events],
    }), 200


# ============================================================
# 物模型-属性 CRUD
# ============================================================
@product_bp.route("/<int:pid>/properties", methods=["GET"])
@jwt_required()
def list_properties(pid):
    product = Product.query.get_or_404(pid)
    return jsonify([p.to_dict() for p in product.properties]), 200


@product_bp.route("/<int:pid>/properties", methods=["POST"])
@jwt_required()
def create_property(pid):
    product = Product.query.get_or_404(pid)
    data = request.get_json(silent=True) or {}
    name = (data.get("property_name") or "").strip()
    identifier = (data.get("identifier") or "").strip()
    data_type = (data.get("data_type") or "").strip()
    if not name or not identifier or not data_type:
        return jsonify({"msg": "property_name, identifier, data_type 不能为空"}), 400
    if ProductProperty.query.filter_by(product_id=pid, identifier=identifier).first():
        return jsonify({"msg": "该属性标识符已存在"}), 409

    prop = ProductProperty(
        product_id=pid,
        property_name=name,
        identifier=identifier,
        data_type=data_type,
        unit=data.get("unit"),
        access_mode=data.get("access_mode", "r"),
        description=data.get("description"),
    )
    db.session.add(prop)
    db.session.commit()
    return jsonify({"msg": "创建成功", "property": prop.to_dict()}), 201


@product_bp.route("/<int:pid>/properties/<int:tid>", methods=["PUT"])
@jwt_required()
def update_property(pid, tid):
    prop = ProductProperty.query.get_or_404(tid)
    if prop.product_id != pid:
        return jsonify({"msg": "属性不属于该产品"}), 404
    data = request.get_json(silent=True) or {}
    if "identifier" in data and data["identifier"] != prop.identifier:
        if ProductProperty.query.filter_by(product_id=pid, identifier=data["identifier"]).first():
            return jsonify({"msg": "标识符已存在"}), 409
        prop.identifier = data["identifier"]
    for field in ("property_name", "data_type", "unit", "access_mode", "description"):
        if field in data:
            setattr(prop, field, data[field])
    db.session.commit()
    return jsonify({"msg": "更新成功", "property": prop.to_dict()}), 200


@product_bp.route("/<int:pid>/properties/<int:tid>", methods=["DELETE"])
@jwt_required()
def delete_property(pid, tid):
    prop = ProductProperty.query.get_or_404(tid)
    if prop.product_id != pid:
        return jsonify({"msg": "属性不属于该产品"}), 404
    db.session.delete(prop)
    db.session.commit()
    return jsonify({"msg": "删除成功"}), 200


# ============================================================
# 物模型-服务 CRUD
# ============================================================
@product_bp.route("/<int:pid>/services", methods=["GET"])
@jwt_required()
def list_services(pid):
    product = Product.query.get_or_404(pid)
    return jsonify([s.to_dict() for s in product.services]), 200


@product_bp.route("/<int:pid>/services", methods=["POST"])
@jwt_required()
def create_service(pid):
    product = Product.query.get_or_404(pid)
    data = request.get_json(silent=True) or {}
    name = (data.get("service_name") or "").strip()
    identifier = (data.get("identifier") or "").strip()
    if not name or not identifier:
        return jsonify({"msg": "service_name, identifier 不能为空"}), 400
    if ProductService.query.filter_by(product_id=pid, identifier=identifier).first():
        return jsonify({"msg": "该服务标识符已存在"}), 409

    svc = ProductService(
        product_id=pid,
        service_name=name,
        identifier=identifier,
        input_params=data.get("input_params"),
        output_params=data.get("output_params"),
        description=data.get("description"),
    )
    db.session.add(svc)
    db.session.commit()
    return jsonify({"msg": "创建成功", "service": svc.to_dict()}), 201


@product_bp.route("/<int:pid>/services/<int:tid>", methods=["PUT"])
@jwt_required()
def update_service(pid, tid):
    svc = ProductService.query.get_or_404(tid)
    if svc.product_id != pid:
        return jsonify({"msg": "服务不属于该产品"}), 404
    data = request.get_json(silent=True) or {}
    if "identifier" in data and data["identifier"] != svc.identifier:
        if ProductService.query.filter_by(product_id=pid, identifier=data["identifier"]).first():
            return jsonify({"msg": "标识符已存在"}), 409
        svc.identifier = data["identifier"]
    for field in ("service_name", "input_params", "output_params", "description"):
        if field in data:
            setattr(svc, field, data[field])
    db.session.commit()
    return jsonify({"msg": "更新成功", "service": svc.to_dict()}), 200


@product_bp.route("/<int:pid>/services/<int:tid>", methods=["DELETE"])
@jwt_required()
def delete_service(pid, tid):
    svc = ProductService.query.get_or_404(tid)
    if svc.product_id != pid:
        return jsonify({"msg": "服务不属于该产品"}), 404
    db.session.delete(svc)
    db.session.commit()
    return jsonify({"msg": "删除成功"}), 200


# ============================================================
# 物模型-事件 CRUD
# ============================================================
@product_bp.route("/<int:pid>/events", methods=["GET"])
@jwt_required()
def list_events(pid):
    product = Product.query.get_or_404(pid)
    return jsonify([e.to_dict() for e in product.events]), 200


@product_bp.route("/<int:pid>/events", methods=["POST"])
@jwt_required()
def create_event(pid):
    product = Product.query.get_or_404(pid)
    data = request.get_json(silent=True) or {}
    name = (data.get("event_name") or "").strip()
    identifier = (data.get("identifier") or "").strip()
    if not name or not identifier:
        return jsonify({"msg": "event_name, identifier 不能为空"}), 400
    if ProductEvent.query.filter_by(product_id=pid, identifier=identifier).first():
        return jsonify({"msg": "该事件标识符已存在"}), 409

    evt = ProductEvent(
        product_id=pid,
        event_name=name,
        identifier=identifier,
        trigger_position=data.get("trigger_position"),
        output_params=data.get("output_params"),
        trigger_condition=data.get("trigger_condition"),
        description=data.get("description"),
    )
    db.session.add(evt)
    db.session.commit()
    return jsonify({"msg": "创建成功", "event": evt.to_dict()}), 201


@product_bp.route("/<int:pid>/events/<int:tid>", methods=["PUT"])
@jwt_required()
def update_event(pid, tid):
    evt = ProductEvent.query.get_or_404(tid)
    if evt.product_id != pid:
        return jsonify({"msg": "事件不属于该产品"}), 404
    data = request.get_json(silent=True) or {}
    if "identifier" in data and data["identifier"] != evt.identifier:
        if ProductEvent.query.filter_by(product_id=pid, identifier=data["identifier"]).first():
            return jsonify({"msg": "标识符已存在"}), 409
        evt.identifier = data["identifier"]
    for field in ("event_name", "trigger_position", "output_params", "trigger_condition", "description"):
        if field in data:
            setattr(evt, field, data[field])
    db.session.commit()
    return jsonify({"msg": "更新成功", "event": evt.to_dict()}), 200


@product_bp.route("/<int:pid>/events/<int:tid>", methods=["DELETE"])
@jwt_required()
def delete_event(pid, tid):
    evt = ProductEvent.query.get_or_404(tid)
    if evt.product_id != pid:
        return jsonify({"msg": "事件不属于该产品"}), 404
    db.session.delete(evt)
    db.session.commit()
    return jsonify({"msg": "删除成功"}), 200
