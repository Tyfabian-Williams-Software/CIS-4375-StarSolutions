from decimal import Decimal, InvalidOperation

from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy.orm import selectinload

from app import db
from app.models import Order, OrderLine, Product
from app.sockets import socketio
from app.utils import roles_required
from app.validators import validate_order_payload, validate_order_line_payload, ALLOWED_ORDER_STATUSES

routes_bp = Blueprint("routes", __name__)

ACTIVE_STATUSES = ("pending", "in_progress", "ready")


def _recalc_order_price(order):
    """Recompute the order header total from its non-cancelled lines."""
    total = Decimal("0")
    for line in list(order.lines):
        if line.order_status == "cancelled":
            continue
        if line.unit_price is not None and line.quantity:
            total += Decimal(str(line.unit_price)) * line.quantity
    order.order_price = total
    return total


def _active_orders():
    """Orders that still have at least one line the kitchen needs to see, oldest first."""
    return (
        Order.query
        .join(OrderLine)
        .filter(OrderLine.order_status.in_(ACTIVE_STATUSES))
        .options(selectinload(Order.lines))
        .order_by(Order.order_date.asc())
        .distinct()
        .all()
    )


# ---------------------------------------------------------------------------
# Page routes (order entry + kitchen display). All mutations go through the
# JSON API below; these routes only render the shells.
# ---------------------------------------------------------------------------

@routes_bp.route("/front")
@login_required
@roles_required("front", "admin")
def front():
    products = Product.query.order_by(Product.product_type, Product.name).all()
    categories = []
    for p in products:
        cat = p.product_type or "Other"
        if cat not in categories:
            categories.append(cat)
    recent_orders = (
        Order.query.options(selectinload(Order.lines))
        .order_by(Order.order_date.desc())
        .limit(8)
        .all()
    )
    return render_template(
        "front.html",
        products=[p.to_dict() for p in products],
        categories=categories,
        recent_orders=recent_orders,
    )


@routes_bp.route("/kitchen")
@login_required
@roles_required("kitchen", "admin")
def kitchen():
    return render_template("kitchen.html", orders=_active_orders())


# ---------------------------------------------------------------------------
# JSON REST API
# ---------------------------------------------------------------------------

@routes_bp.route("/api/products", methods=["GET"])
@login_required
def api_list_products():
    products = Product.query.order_by(Product.product_type, Product.name).all()
    return jsonify({"products": [p.to_dict() for p in products]}), 200


@routes_bp.route("/api/orders", methods=["GET"])
@login_required
def api_list_orders():
    # ?active=1 returns only orders with lines still in the kitchen pipeline
    if request.args.get("active"):
        orders = _active_orders()
    else:
        orders = Order.query.order_by(Order.order_date.desc()).limit(100).all()
    return jsonify({"orders": [o.to_dict() for o in orders]}), 200


@routes_bp.route("/api/orders/<int:order_id>", methods=["GET"])
@login_required
def api_get_order(order_id):
    order = Order.query.get(order_id)
    if not order:
        return jsonify({"error": "Order not found"}), 404
    return jsonify(order.to_dict()), 200


@routes_bp.route("/api/orders", methods=["POST"])
@login_required
@roles_required("front", "admin")
def api_create_order():
    data = request.get_json(silent=True) or {}
    valid, errors, cleaned = validate_order_payload(data)
    if not valid:
        if any("not found" in e.lower() for e in errors):
            return jsonify({"error": "not found", "details": errors}), 404
        return jsonify({"error": "invalid payload", "details": errors}), 400

    order = Order(customer_id=cleaned.get("customer_id"), order_type=cleaned.get("order_type"))
    db.session.add(order)
    db.session.flush()  # get order.id without a full commit

    table_number = cleaned.get("table_number")
    for ln in cleaned["lines"]:
        unit_price = ln.get("unit_price")
        product_id = ln.get("product_id")
        if unit_price is None and ln.get("product") is not None:
            unit_price = ln["product"].price
        ol = OrderLine(
            order_id=order.id,
            product_id=product_id,
            quantity=ln.get("quantity", 1),
            unit_price=unit_price,
            special_instructions=ln.get("special_instructions"),
            order_status=ln.get("order_status", "pending"),
            table_number=table_number,
        )
        db.session.add(ol)

    _recalc_order_price(order)
    db.session.commit()

    payload = order.to_dict()
    socketio.emit("order_new", payload)
    return jsonify(payload), 201


@routes_bp.route("/api/orders/<int:order_id>", methods=["PUT", "PATCH"])
@login_required
@roles_required("admin")
def api_update_order(order_id):
    order = Order.query.get(order_id)
    if not order:
        return jsonify({"error": "Order not found"}), 404

    data = request.get_json(silent=True) or {}
    if "order_type" in data:
        order.order_type = data.get("order_type")
    if "order_price" in data:
        try:
            order_price = Decimal(str(data.get("order_price")))
        except (InvalidOperation, TypeError, ValueError):
            return jsonify({"error": "order_price must be numeric"}), 400
        if order_price < 0:
            return jsonify({"error": "order_price must not be negative"}), 400
        order.order_price = order_price

    db.session.commit()
    return jsonify(order.to_dict()), 200


@routes_bp.route("/api/orders/<int:order_id>/lines", methods=["PUT"])
@login_required
@roles_required("front", "admin")
def api_replace_order_lines(order_id):
    """Atomically replace all lines on an order (edit-ticket flow)."""
    order = Order.query.get(order_id)
    if not order:
        return jsonify({"error": "Order not found"}), 404

    data = request.get_json(silent=True) or {}
    valid, errors, cleaned = validate_order_payload({
        "customer_id": order.customer_id,
        "order_type": order.order_type,
        "lines": data.get("lines"),
        "table_number": data.get("table_number"),
    })
    if not valid:
        if any("not found" in e.lower() for e in errors):
            return jsonify({"error": "not found", "details": errors}), 404
        return jsonify({"error": "invalid payload", "details": errors}), 400

    # Delete existing lines, then insert the replacement set in one transaction.
    for line in list(order.lines):
        db.session.delete(line)

    table_number = cleaned.get("table_number")
    for ln in cleaned["lines"]:
        unit_price = ln.get("unit_price")
        product_id = ln.get("product_id")
        if unit_price is None and ln.get("product") is not None:
            unit_price = ln["product"].price
        db.session.add(OrderLine(
            order_id=order.id,
            product_id=product_id,
            quantity=ln.get("quantity", 1),
            unit_price=unit_price,
            special_instructions=ln.get("special_instructions"),
            order_status=ln.get("order_status", "pending"),
            table_number=table_number,
        ))

    _recalc_order_price(order)
    db.session.commit()

    payload = order.to_dict()
    socketio.emit("order_replaced", payload)
    return jsonify(payload), 200


@routes_bp.route("/api/order_lines/<int:line_id>/status", methods=["PATCH"])
@login_required
@roles_required("kitchen", "front", "admin")
def api_update_order_line_status(line_id):
    line = OrderLine.query.get(line_id)
    if not line:
        return jsonify({"error": "Order line not found"}), 404
    data = request.get_json(silent=True) or {}
    status = data.get("order_status")
    if not status:
        return jsonify({"error": "order_status required"}), 400
    if status not in ALLOWED_ORDER_STATUSES:
        return jsonify({"error": f"order_status must be one of {sorted(ALLOWED_ORDER_STATUSES)}"}), 400
    line.order_status = status
    order = db.session.get(Order, line.order_id)
    if order:
        _recalc_order_price(order)
    db.session.commit()
    socketio.emit("order_update", {
        "order_line_id": line.id,
        "order_id": line.order_id,
        "order_status": status,
    })
    return jsonify(line.to_dict()), 200


@routes_bp.route("/api/order_lines", methods=["POST"])
@login_required
@roles_required("front", "admin")
def api_create_order_line():
    data = request.get_json(silent=True) or {}
    valid, errors, cleaned = validate_order_line_payload(data)
    if not valid:
        if any("not found" in e.lower() for e in errors):
            return jsonify({"error": "not found", "details": errors}), 404
        return jsonify({"error": "invalid payload", "details": errors}), 400

    order_id = cleaned["order_id"]
    product_id = cleaned["product_id"]
    quantity = cleaned["quantity"]
    unit_price = cleaned.get("unit_price")
    if unit_price is None and cleaned.get("product") is not None:
        unit_price = cleaned["product"].price

    order = db.session.get(Order, order_id)
    table_number = cleaned.get("table_number")
    if table_number is None and order is not None and order.lines:
        # Inherit the table from existing sibling lines so a line added later
        # (e.g. via "add item" on an open ticket) stays associated with the
        # same table as the rest of the order.
        table_number = order.lines[0].table_number

    ol = OrderLine(
        order_id=order_id,
        product_id=product_id,
        quantity=quantity,
        unit_price=unit_price,
        order_status=cleaned.get("order_status", "pending"),
        table_number=table_number,
    )
    db.session.add(ol)

    if order:
        _recalc_order_price(order)
    db.session.commit()
    socketio.emit("order_update", ol.to_dict())
    return jsonify(ol.to_dict()), 201


@routes_bp.route("/api/orders/<int:order_id>", methods=["DELETE"])
@login_required
@roles_required("admin")
def api_delete_order(order_id):
    order = Order.query.get(order_id)
    if not order:
        return jsonify({"error": "Order not found"}), 404

    db.session.delete(order)
    db.session.commit()

    socketio.emit("order_delete", {"id": order_id})
    return ("", 204)
