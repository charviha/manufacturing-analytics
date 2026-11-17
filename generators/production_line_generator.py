
import uuid
from datetime import datetime

import pandas as pd
from sqlalchemy import text

from database.connection import get_engine
from database.schema import ProductionLine


def generate_production_lines():
    engine = get_engine()

    # Sample production line master data
    production_lines = [
        {
            "line_name": "Assembly Line A",
            "location": "Bengaluru",
            "line_capacity_per_hour": 120,
            "is_active": True
        },
        {
            "line_name": "Assembly Line B",
            "location": "Chennai",
            "line_capacity_per_hour": 100,
            "is_active": True
        },
        {
            "line_name": "Packaging Line A",
            "location": "Pune",
            "line_capacity_per_hour": 200,
            "is_active": True
        },
        {
            "line_name": "Packaging Line B",
            "location": "Hyderabad",
            "line_capacity_per_hour": 180,
            "is_active": True
        },
        {
            "line_name": "Machining Line A",
            "location": "Bengaluru",
            "line_capacity_per_hour": 80,
            "is_active": True
        },
        {
            "line_name": "Welding Line A",
            "location": "Chennai",
            "line_capacity_per_hour": 90,
            "is_active": True
        },
        {
            "line_name": "Painting Line A",
            "location": "Pune",
            "line_capacity_per_hour": 110,
            "is_active": True
        },
        {
            "line_name": "Assembly Line C",
            "location": "Hyderabad",
            "line_capacity_per_hour": 95,
            "is_active": False
        }
    ]

    # Convert the records into a Pandas DataFrame
    df = pd.DataFrame(production_lines)

    # Add UUID and creation timestamp
    df["line_id"] = [str(uuid.uuid4()) for _ in range(len(df))]
    df["created_at"] = datetime.now()

    # Check existing production lines to avoid duplicates
    with engine.connect() as connection:
        existing_df = pd.read_sql(
            text("SELECT line_name FROM production_lines"),
            connection
        )

    existing_names = set(existing_df["line_name"].tolist())

    # Keep only new production lines
    df = df[~df["line_name"].isin(existing_names)]

    if df.empty:
        print("Production lines already exist. No new records inserted.")
        return

    # Insert records into MySQL
    records = df.to_dict(orient="records")

    with engine.begin() as connection:
        connection.execute(
            ProductionLine.__table__.insert(),
            records
        )

    print("Production line data generated successfully!")
    print(f"New production lines inserted: {len(records)}")


if __name__ == "__main__":
    generate_production_lines()
