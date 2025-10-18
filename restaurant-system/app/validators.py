from app import db
from app.models import Customer, Product

# Allowed enums
ALLOWED_ORDER_TYPES = {"dine_in", "takeout", "delivery"}
ALLOWED_ORDER_STATUSES = {"pending", "in_progress", "ready", "served", "cancelled"}
MAX_QUANTITY = 100


def validate_order_payload(data):
    errors = []
    cleaned = {}
    if not isinstance(data, dict):
        return False, ["payload must be a JSON object"], {}

    # Detect unknown top-level fields
    allowed_keys = {"customer_id", "order_type", "lines"}
    extra = set(data.keys()) - allowed_keys
    if extra:
        errors.append(f"unknown fields at top-level: {sorted(list(extra))}")

    customer_id = data.get("customer_id")
    if customer_id is None:
        errors.append("customer_id is required")
    else:
        try:
            customer_id = int(customer_id)
            # existence check
            if Customer.query.get(customer_id) is None:
                errors.append("customer not found")
            cleaned["customer_id"] = customer_id
        except Exception:
            errors.append("customer_id must be an integer")

    order_type = data.get("order_type")
    if order_type:
        if order_type not in ALLOWED_ORDER_TYPES:
            errors.append(f"order_type must be one of {sorted(ALLOWED_ORDER_TYPES)}")
        else:
            cleaned["order_type"] = order_type

    lines = data.get("lines")
    if not isinstance(lines, list) or len(lines) == 0:
        errors.append("lines must be a non-empty array")
    else:
        cleaned_lines = []
        for i, ln in enumerate(lines):
            if not isinstance(ln, dict):
                errors.append(f"line[{i}] must be an object")
                continue
            prod = ln.get("product_id")
            if prod is None:
                errors.append(f"line[{i}].product_id is required")
                prod_obj = None
            else:
                try:
                    prod = int(prod)
                    prod_obj = Product.query.get(prod)
                    if prod_obj is None:
                        errors.append(f"product {prod} not found")
                except Exception:
                    errors.append(f"line[{i}].product_id must be an integer")
                    prod_obj = None

            qty = ln.get("quantity", 1)
            try:
                qty = int(qty)
                if qty <= 0 or qty > MAX_QUANTITY:
                    errors.append(f"line[{i}].quantity must be between 1 and {MAX_QUANTITY}")
            except Exception:
                errors.append(f"line[{i}].quantity must be an integer")

            unit_price = ln.get("unit_price")
            if unit_price is not None:
                try:
                    # accept numeric strings too
                    unit_price = float(unit_price)
                except Exception:
                    errors.append(f"line[{i}].unit_price must be numeric if provided")

            status = ln.get("order_status", "pending")
            if status not in ALLOWED_ORDER_STATUSES:
                errors.append(f"line[{i}].order_status must be one of {sorted(ALLOWED_ORDER_STATUSES)}")

            cleaned_lines.append({
                "product_id": prod,
                "quantity": qty,
                "unit_price": unit_price,
                "special_instructions": ln.get("special_instructions"),
                "order_status": status,
            })
        cleaned["lines"] = cleaned_lines

    return (len(errors) == 0), errors, cleaned


def validate_order_line_payload(data):
    errors = []
    cleaned = {}
    if not isinstance(data, dict):
        return False, ["payload must be a JSON object"], {}
    order_id = data.get("order_id")
    product_id = data.get("product_id")
    if order_id is None:
        errors.append("order_id is required")
    else:
        try:
            order_id = int(order_id)
            # existence check for order
            if db.session.execute("SELECT 1 FROM Orders WHERE Order_ID = :id", {"id": order_id}).fetchone() is None:
                errors.append("order not found")
            cleaned["order_id"] = order_id
        except Exception:
            errors.append("order_id must be an integer")
    if product_id is None:
        errors.append("product_id is required")
    else:
        try:
            product_id = int(product_id)
            if Product.query.get(product_id) is None:
                errors.append("product not found")
            cleaned["product_id"] = product_id
        except Exception:
            errors.append("product_id must be an integer")

    qty = data.get("quantity", 1)
    try:
        qty = int(qty)
        if qty <= 0 or qty > MAX_QUANTITY:
            errors.append(f"quantity must be between 1 and {MAX_QUANTITY}")
        cleaned["quantity"] = qty
    except Exception:
        errors.append("quantity must be an integer")

    unit_price = data.get("unit_price")
    if unit_price is not None:
        try:
            unit_price = float(unit_price)
            cleaned["unit_price"] = unit_price
        except Exception:
            errors.append("unit_price must be numeric if provided")
    else:
        cleaned["unit_price"] = None

    status = data.get("order_status", "pending")
    if status not in ALLOWED_ORDER_STATUSES:
        errors.append(f"order_status must be one of {sorted(ALLOWED_ORDER_STATUSES)}")
    cleaned["order_status"] = status

    return (len(errors) == 0), errors, cleaned
