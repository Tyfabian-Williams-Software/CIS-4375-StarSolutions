"""One-time data migration: copy every row from a MySQL DATABASE_URL into a
SQLite DATABASE_URL, preserving primary keys so foreign-key relationships
(orders -> products, order lines -> orders/products, etc.) stay intact.

Usage:
    SOURCE_DATABASE_URL="mysql+pymysql://user:pass@host:3306/db" \
    TARGET_DATABASE_URL="sqlite:////data/restaurant.db" \
    python scripts/migrate_mysql_to_sqlite.py

Safe to run more than once: rows whose primary key already exists in the
target are skipped rather than duplicated or overwritten.
"""
import os
import sys

script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(script_dir, "..")))

from sqlalchemy import create_engine, select, insert

from app.models import db, User, Customer, Product, Order, OrderLine

# Parents before children, so foreign keys always resolve on insert.
TABLES_IN_ORDER = [User.__table__, Customer.__table__, Product.__table__,
                    Order.__table__, OrderLine.__table__]


def main():
    source_url = os.environ["SOURCE_DATABASE_URL"]
    target_url = os.environ["TARGET_DATABASE_URL"]

    source = create_engine(source_url)
    target = create_engine(target_url)

    db.Model.metadata.create_all(target)

    with source.connect() as src_conn, target.connect() as dst_conn:
        for table in TABLES_IN_ORDER:
            pk_col = list(table.primary_key.columns)[0]
            rows = [dict(row._mapping) for row in src_conn.execute(select(table))]
            if not rows:
                print(f"{table.name}: nothing to copy")
                continue
            existing_ids = {r[0] for r in dst_conn.execute(select(pk_col))}
            new_rows = [r for r in rows if r[pk_col.name] not in existing_ids]
            if new_rows:
                dst_conn.execute(insert(table), new_rows)
                dst_conn.commit()
            skipped = len(rows) - len(new_rows)
            print(f"{table.name}: copied {len(new_rows)} of {len(rows)} rows"
                  + (f" ({skipped} already present, skipped)" if skipped else ""))

    print("done.")


if __name__ == "__main__":
    main()
