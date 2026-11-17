
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

# Locate project root
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables
load_dotenv(BASE_DIR / "config" / ".env")

# Database configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME", "manufacturing_analytics")


def create_database():
    """Create the MySQL database if it does not exist."""

    if not DB_USER or DB_PASSWORD is None:
        raise ValueError(
            "Please configure DB_USER and DB_PASSWORD in config/.env"
        )

    # Connect to MySQL server without selecting a database
    server_url = URL.create(
        drivername="mysql+pymysql",
        username=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )

    engine = create_engine(server_url, pool_pre_ping=True)

    try:
        with engine.connect() as connection:
            connection.execute(
                text(
                    f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` "
                    "CHARACTER SET utf8mb4 "
                    "COLLATE utf8mb4_unicode_ci"
                )
            )

        print(f"Database '{DB_NAME}' created successfully.")

    finally:
        engine.dispose()


def get_engine():
    """Return SQLAlchemy engine for the manufacturing database."""

    database_url = URL.create(
        drivername="mysql+pymysql",
        username=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME
    )

    return create_engine(
        database_url,
        pool_pre_ping=True,
        pool_recycle=3600
    )


def test_connection():
    """Check whether Python can connect to MySQL."""

    engine = get_engine()

    try:
        with engine.connect() as connection:
            result = connection.execute(
                text("SELECT VERSION()")
            )

            version = result.scalar()

            print("MySQL connection successful!")
            print(f"MySQL Version: {version}")
            print(f"Database: {DB_NAME}")

    except Exception as error:
        print("Database connection failed!")
        print(f"Error: {error}")
        raise

    finally:
        engine.dispose()


if __name__ == "__main__":
    create_database()
    test_connection()
