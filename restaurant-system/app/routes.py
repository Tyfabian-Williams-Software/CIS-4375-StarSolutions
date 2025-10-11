from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required, current_user
from app.models import db, Order
from app.sockets import socketio

routes_bp = Blueprint("routes", __name__)

@routes_bp.route("/front", methods=["GET", "POST"])
@login_required
def front():
    if current_user.role != "front":
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        customer = request.form["customer_name"]
        items = request.form["items"]
        new_order = Order(customer_name=customer, items=items)
        db.session.add(new_order)
        db.session.commit()

        # Notify all clients about new order
        socketio.emit("order_new", {"id": new_order.id, "customer": customer, "items": items, "status": new_order.status}, broadcast=True)

        return redirect(url_for("routes.front"))

    orders = Order.query.all()
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
        order.status = status
        db.session.commit()

        # Notify all clients about status change
        socketio.emit("order_update", {"id": order.id, "status": status}, broadcast=True)

        return redirect(url_for("routes.kitchen"))

    orders = Order.query.all()
    return render_template("kitchen.html", orders=orders)