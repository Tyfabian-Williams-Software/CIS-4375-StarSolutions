import os
import logging
from sqlalchemy import create_engine

logger = logging.getLogger(__name__)

# Read DB URI from environment when available for safety
DB_URI = os.environ.get("DATABASE_URL") or "mysql+pymysql://admin:abc123g13!@restaurant-db13.cvqmcqgeki2y.us-east-1.rds.amazonaws.com:3306/restaurant_db"

try:
    engine = create_engine(DB_URI)
    connection = engine.connect()
    logger.info("Database connection successful")
    connection.close()
except Exception:
    logger.exception("Database connection failed")