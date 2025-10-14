from app import db, login_manager
from flask_login import UserMixin
from datetime import datetime


class User(UserMixin, db.Model):
    """Maps to the Employee table in the existing database.

    Database columns (examples from screenshots): Employee_ID, Username, Password_Hash, Employee_Role
    """
    __tablename__ = "Employee"
    id = db.Column("Employee_ID", db.Integer, primary_key=True)
    username = db.Column("Username", db.String(100), unique=True, nullable=False)
    password = db.Column("Password_Hash", db.String(255), nullable=False)
    role = db.Column("Employee_Role", db.String(50))
    first_name = db.Column("First_Name", db.String(100))
    last_name = db.Column("Last_Name", db.String(100))
    email = db.Column("Employee_Email", db.String(200))

    def get_id(self):
        return str(self.id)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "role": self.role,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
        }


@login_manager.user_loader
def load_user(user_id):
    try:
        return User.query.get(int(user_id))
    except Exception:
        return None


class Customer(db.Model):
    __tablename__ = "Customer"
    id = db.Column("Customer_ID", db.Integer, primary_key=True)
    first_name = db.Column("First_Name", db.String(100))
    last_name = db.Column("Last_Name", db.String(100))
    email = db.Column("Email", db.String(200))
    area_code = db.Column("Area_Code", db.String(10))
    phone_number = db.Column("Phone_Number", db.String(20))

    def to_dict(self):
        return {
            "customer_id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
        }


class Product(db.Model):
    __tablename__ = "Product"
    id = db.Column("Product_ID", db.Integer, primary_key=True)
    name = db.Column("Product_Name", db.String(100), nullable=False)
    price = db.Column("Product_Price", db.Numeric(10, 2))
    description = db.Column("Product_Description", db.Text)
    product_type = db.Column("Product_Type", db.String(50))

    def to_dict(self):
        return {
            "product_id": self.id,
            "product_name": self.name,
            "product_price": float(self.price) if self.price is not None else None,
        }


class Order(db.Model):
    __tablename__ = "Orders"
    id = db.Column("Order_ID", db.Integer, primary_key=True)
    customer_id = db.Column("Customer_ID", db.Integer, db.ForeignKey("Customer.Customer_ID"))
    order_date = db.Column("Order_Date", db.DateTime, default=datetime.utcnow)
    order_price = db.Column("Order_Price", db.Numeric(10, 2))
    order_type = db.Column("Order_Type", db.String(50))
    creation_date = db.Column("Creation_Date", db.DateTime)

    # Relationship to order lines
    lines = db.relationship("OrderLine", backref="order", cascade="all, delete-orphan", lazy="dynamic")

    def to_dict(self, include_lines=True):
        d = {
            "order_id": self.id,
            "customer_id": self.customer_id,
            "order_date": None if not self.order_date else self.order_date.isoformat(),
            "order_price": float(self.order_price) if self.order_price is not None else None,
            "order_type": self.order_type,
            "creation_date": None if not self.creation_date else self.creation_date.isoformat(),
        }
        if include_lines:
            d["lines"] = [l.to_dict() for l in self.lines.order_by(db.desc(OrderLine.id)).all()]
        return d


class OrderLine(db.Model):
    __tablename__ = "Order_Line"
    id = db.Column("Order_Line_ID", db.Integer, primary_key=True)
    order_id = db.Column("Order_ID", db.Integer, db.ForeignKey("Orders.Order_ID"))
    product_id = db.Column("Product_ID", db.Integer, db.ForeignKey("Product.Product_ID"))
    quantity = db.Column("Quantity", db.Integer)
    unit_price = db.Column("Unit_Price", db.Numeric(10, 2))
    special_instructions = db.Column("Special_Instructions", db.Text)
    order_status = db.Column("Order_Status", db.String(50))
    table_number = db.Column("Table_Number", db.Integer)

    def to_dict(self):
        return {
            "order_line_id": self.id,
            "order_id": self.order_id,
            "product_id": self.product_id,
            "quantity": self.quantity,
            "unit_price": float(self.unit_price) if self.unit_price is not None else None,
            "special_instructions": self.special_instructions,
            "order_status": self.order_status,
            "table_number": self.table_number,
        }