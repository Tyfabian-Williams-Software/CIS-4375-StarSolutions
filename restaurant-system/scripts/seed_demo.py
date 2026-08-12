"""Seed the database with staff accounts and a starter menu.

Usage:
    python scripts/seed_demo.py            # uses DATABASE_URL from .env (or sqlite dev.db)

Safe to run more than once: existing usernames/products are skipped.
Edit MENU below to match the restaurant's real menu before first deploy.
"""
import os
import sys

script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(script_dir, "..")))

from werkzeug.security import generate_password_hash

from app import create_app, db
from app.models import User, Product

STAFF = [
    # (username, password, role) — CHANGE THESE PASSWORDS before real use.
    ("admin",   "ChangeMe-Admin1!",   "admin"),
    ("front1",  "ChangeMe-Front1!",   "front"),
    ("kitchen1","ChangeMe-Kitchen1!", "kitchen"),
]

MENU = [
    # (name, price, type, description)
    ("Beef Crowich",        5.50, "Entree",         "Slow-braised beef in a toasted roll"),
    ("Pate Kode",           3.75, "Appetizer",      "Crispy Haitian street-style patty"),
    ("Griot with Pikliz",  14.95, "Entree",         "Fried pork shoulder, spicy slaw"),
    ("Fried Fish Platter", 16.50, "Fried Platter",  "Whole snapper, plantains, rice"),
    ("Diri ak Djon Djon",   8.00, "Sides",          "Black mushroom rice"),
    ("Fried Plantains",     4.25, "Sides",          "Sweet, twice-fried"),
    ("Mango Juice",         3.50, "Juice",          "Fresh-squeezed"),
    ("Cola Couronne",       2.75, "Soft Drink",     "Haitian fruit champagne soda"),
    ("Prestige Beer",       5.00, "Beer",           "Haitian lager"),
    ("Rum Punch",           9.00, "Alcoholic Drink","House Barbancourt blend"),
]


def main():
    app = create_app()
    with app.app_context():
        db.create_all()

        for username, password, role in STAFF:
            if User.query.filter_by(username=username).first():
                print(f"user exists, skipping: {username}")
                continue
            db.session.add(User(username=username,
                                password=generate_password_hash(password),
                                role=role))
            print(f"created user: {username} ({role})")

        for name, price, ptype, desc in MENU:
            if Product.query.filter_by(name=name).first():
                print(f"product exists, skipping: {name}")
                continue
            db.session.add(Product(name=name, price=price,
                                   product_type=ptype, description=desc))
            print(f"created product: {name}")

        db.session.commit()
        print("done.")


if __name__ == "__main__":
    main()
