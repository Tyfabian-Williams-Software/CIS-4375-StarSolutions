import pymysql
from sqlalchemy import create_engine

DB_URI = "mysql+pymysql://admin:abc123g13!@restaurant-db13.cvqmcqgeki2y.us-east-1.rds.amazonaws.com:3306/restaurant_db"

try:
    engine = create_engine(DB_URI)
    connection = engine.connect()
    print("✅ Database connection successful!")
    connection.close()
except Exception as e:
    print("❌ Database connection failed:")
    print(e)