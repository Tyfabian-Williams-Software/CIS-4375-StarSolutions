from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.models import Order, OrderLine, Product, Customer
from app.sockets import socketio

routes_bp = Blueprint("routes", __name__)

@routes_bp.route("/front", methods=["GET", "POST"])
@login_required
def front():
    if current_user.role != "front":
        return redirect(url_for("auth.login"))

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
def kitchen():
    if current_user.role != "kitchen":
        return redirect(url_for("auth.login"))

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
    # All logged-in users can list orders
    orders = Order.query.order_by(Order.order_date.desc()).all()
    return {"orders": [o.to_dict() for o in orders]}, 200


@routes_bp.route("/api/orders/<int:order_id>", methods=["GET"])
@login_required
def api_get_order(order_id):
    order = Order.query.get(order_id)
    if not order:
        return {"error": "Order not found"}, 404
    return order.to_dict(), 200


@routes_bp.route("/api/orders", methods=["POST"])
@login_required
def api_create_order():
    # Only front or admin may create orders
    if current_user.role not in ("front", "admin"):
        return {"error": "Forbidden"}, 403

    data = request.get_json(silent=True) or {}
    # Expect payload: { "customer_id": 1, "order_type": "dine_in", "lines": [ {"product_id": 1, "quantity": 2, "unit_price": 9.99 }, ... ] }
    customer_id = data.get("customer_id")
    order_type = data.get("order_type")
    lines = data.get("lines") or []
    if not customer_id or not isinstance(lines, list) or len(lines) == 0:
        return {"error": "customer_id and non-empty lines array required"}, 400

    order = Order(customer_id=customer_id, order_type=order_type)
    db.session.add(order)
    db.session.commit()

    for ln in lines:
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
    return order.to_dict(), 201


@routes_bp.route("/api/orders/<int:order_id>", methods=["PUT", "PATCH"])
@login_required
def api_update_order(order_id):
    order = Order.query.get(order_id)
    if not order:
        return {"error": "Order not found"}, 404

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
    return order.to_dict(), 200



# Order line specific endpoints (kitchen updates go here)
@routes_bp.route("/api/order_lines/<int:line_id>/status", methods=["PATCH"])
@login_required
def api_update_order_line_status(line_id):
    # Only kitchen or admin can update order line status
    if current_user.role not in ("kitchen", "admin"):
        return {"error": "Forbidden"}, 403
    line = OrderLine.query.get(line_id)
    if not line:
        return {"error": "Order line not found"}, 404
    data = request.get_json(silent=True) or {}
    status = data.get("order_status")
    if not status:
        return {"error": "order_status required"}, 400
    line.order_status = status
    db.session.commit()
    socketio.emit("order_update", {"order_line_id": line.id, "order_id": line.order_id, "order_status": status})
    return line.to_dict(), 200


@routes_bp.route("/api/order_lines", methods=["POST"])
@login_required
def api_create_order_line():
    # Creating order lines: allowed for front (when creating an order) or admin
    if current_user.role not in ("front", "admin"):
        return {"error": "Forbidden"}, 403
    data = request.get_json(silent=True) or {}
    order_id = data.get("order_id")
    product_id = data.get("product_id")
    quantity = data.get("quantity", 1)
    unit_price = data.get("unit_price")
    if not order_id or not product_id:
        return {"error": "order_id and product_id required"}, 400
    # If unit_price not provided, fetch product price
    if unit_price is None and product_id:
        prod = Product.query.get(product_id)
        unit_price = prod.price if prod is not None else None
    ol = OrderLine(order_id=order_id, product_id=product_id, quantity=quantity, unit_price=unit_price, order_status=data.get("order_status", "pending"))
    db.session.add(ol)
    db.session.commit()
    socketio.emit("order_update", ol.to_dict())
    return ol.to_dict(), 201


@routes_bp.route("/api/orders/<int:order_id>", methods=["DELETE"])
@login_required
def api_delete_order(order_id):
    # Only admin can delete orders
    if current_user.role != "admin":
        return {"error": "Forbidden"}, 403

    order = Order.query.get(order_id)
    if not order:
        return {"error": "Order not found"}, 404

    db.session.delete(order)
    db.session.commit()

    socketio.emit("order_delete", {"id": order_id})
    return {}, 204