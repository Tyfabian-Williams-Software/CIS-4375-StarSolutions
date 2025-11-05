from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Order, OrderLine, Product, Customer
from app.sockets import socketio
from app.utils import roles_required
from app.validators import validate_order_payload, validate_order_line_payload

routes_bp = Blueprint("routes", __name__)

@routes_bp.route("/front", methods=["GET", "POST"])
@login_required
@roles_required("front", "admin")
def front():

    if request.method == "POST":
        # Expect the front form to submit customer_id and a JSON string for items or simple text
        customer_id = request.form.get("customer_id") or request.form.get("customer_name")
        items_raw = request.form.get("items")

        # Create order header
        order = Order(customer_id=customer_id, order_type="dine_in", creation_date=None)
        db.session.add(order)
        db.session.commit()

        # Parse items: expect lines like product_id:quantity or a JSON array in the items form field
        # For simplicity, if items_raw looks like JSON list, try parse; otherwise store as a single line
        import json
        try:
            items_list = json.loads(items_raw)
        except Exception:
            items_list = None

        if items_list and isinstance(items_list, list):
            for it in items_list:
                prod_id = it.get("product_id")
                qty = it.get("quantity", 1)
                price = it.get("unit_price")
                # If unit_price not provided, attempt to pull current product price from Product table
                if price is None and prod_id:
                    prod = Product.query.get(prod_id)
                    price = prod.price if prod is not None else None
                ol = OrderLine(order_id=order.id, product_id=prod_id, quantity=qty, unit_price=price, order_status="pending")
                db.session.add(ol)
        else:
            # treat items_raw as a single note
            ol = OrderLine(order_id=order.id, product_id=None, quantity=1, unit_price=None, special_instructions=items_raw, order_status="pending")
            db.session.add(ol)

        db.session.commit()

        # Notify clients
        socketio.emit("order_new", order.to_dict())

        return redirect(url_for("routes.front"))

    orders = Order.query.order_by(Order.order_date.desc()).all()
    return render_template("front.html", orders=orders)

@routes_bp.route("/kitchen", methods=["GET", "POST"])
@login_required
@roles_required("kitchen", "admin")
def kitchen():

    if request.method == "POST":
        order_id = request.form["order_id"]
        status = request.form["status"]
        order = Order.query.get(order_id)
        if order is None:
            return "Order not found", 404
        # Kitchen updates should change order line statuses — if order line id passed, update that
        line_id = request.form.get("line_id")
        if line_id:
            line = OrderLine.query.get(line_id)
            if not line:
                return "Order line not found", 404
            line.order_status = status
            db.session.commit()
            socketio.emit("order_update", {"order_line_id": line.id, "order_id": line.order_id, "order_status": status})
            return redirect(url_for("routes.kitchen"))
        else:
            # If only order header provided, update all lines for that order
            for line in order.lines.all():
                line.order_status = status
            db.session.commit()
            socketio.emit("order_update", {"order_id": order.id, "status": status})
            return redirect(url_for("routes.kitchen"))

    orders = Order.query.all()
    return render_template("kitchen.html", orders=orders)


# JSON REST API for orders
@routes_bp.route("/api/orders", methods=["GET"])
@login_required
def api_list_orders():
    # All authenticated users can list orders
    orders = Order.query.order_by(Order.order_date.desc()).all()
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
        # If errors indicate missing referenced entities, return 404
        if any("not found" in e.lower() for e in errors):
            return jsonify({"error": "not found", "details": errors}), 404
        return jsonify({"error": "invalid payload", "details": errors}), 400

    order = Order(customer_id=cleaned["customer_id"], order_type=cleaned.get("order_type"))
    db.session.add(order)
    db.session.commit()

    for ln in cleaned["lines"]:
        unit_price = ln.get("unit_price")
        product_id = ln.get("product_id")
        # default unit_price to product price when missing
        if unit_price is None and product_id:
            prod = Product.query.get(product_id)
            unit_price = prod.price if prod is not None else None
        ol = OrderLine(order_id=order.id, product_id=product_id, quantity=ln.get("quantity", 1), unit_price=unit_price, special_instructions=ln.get("special_instructions"), order_status=ln.get("order_status", "pending"))
        db.session.add(ol)
    db.session.commit()

    socketio.emit("order_new", order.to_dict())
    return jsonify(order.to_dict()), 201


@routes_bp.route("/api/orders/<int:order_id>", methods=["PUT", "PATCH"])
@login_required
@roles_required("admin")
def api_update_order(order_id):
    order = Order.query.get(order_id)
    if not order:
        return jsonify({"error": "Order not found"}), 404

    data = request.get_json(silent=True) or {}
    # Allow updating order header fields (order_type, order_price) by admin
    if "order_type" in data:
        if current_user.role != "admin":
            return {"error": "Forbidden to change order header"}, 403
        order.order_type = data.get("order_type")
    if "order_price" in data:
        if current_user.role != "admin":
            return {"error": "Forbidden to change order header"}, 403
        order.order_price = data.get("order_price")

    db.session.commit()
    return jsonify(order.to_dict()), 200



# Order line specific endpoints (kitchen updates go here)
@routes_bp.route("/api/order_lines/<int:line_id>/status", methods=["PATCH"])
@login_required
@roles_required("kitchen", "admin")
def api_update_order_line_status(line_id):
    line = OrderLine.query.get(line_id)
    if not line:
        return jsonify({"error": "Order line not found"}), 404
    data = request.get_json(silent=True) or {}
    status = data.get("order_status")
    if not status:
        return jsonify({"error": "order_status required"}), 400
    line.order_status = status
    db.session.commit()
    socketio.emit("order_update", {"order_line_id": line.id, "order_id": line.order_id, "order_status": status})
    return jsonify(line.to_dict()), 200


@routes_bp.route("/api/order_lines", methods=["POST"])
@login_required
@roles_required("front", "admin")
def api_create_order_line():
    data = request.get_json(silent=True) or {}
    valid, errors, cleaned = validate_order_line_payload(data)
    if not valid:
        # Map existence errors to 404 so clients can distinguish validation vs missing resources
        if any("not found" in e.lower() for e in errors):
            return jsonify({"error": "not found", "details": errors}), 404
        return jsonify({"error": "invalid payload", "details": errors}), 400

    order_id = cleaned["order_id"]
    product_id = cleaned["product_id"]
    quantity = cleaned["quantity"]
    unit_price = cleaned.get("unit_price")
    # If unit_price not provided, fetch product price
    if unit_price is None and product_id:
        prod = Product.query.get(product_id)
        unit_price = prod.price if prod is not None else None
    ol = OrderLine(order_id=order_id, product_id=product_id, quantity=quantity, unit_price=unit_price, order_status=cleaned.get("order_status", "pending"))
    db.session.add(ol)
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