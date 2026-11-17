
import pandas as pd
from sqlalchemy import text

from database.connection import get_engine
from database.schema import Calendar


# Generate calendar dates for five years
START_DATE = "2022-01-01"
END_DATE = "2026-12-31"


# India-oriented sample holidays.
# This is a synthetic calendar and can be adjusted for the factory location.
HOLIDAYS = {
    "2022-01-26", "2022-03-18", "2022-08-15",
    "2022-10-02", "2022-10-24", "2022-12-25",

    "2023-01-26", "2023-03-08", "2023-08-15",
    "2023-10-02", "2023-11-12", "2023-12-25",

    "2024-01-26", "2024-03-25", "2024-08-15",
    "2024-10-02", "2024-11-01", "2024-12-25",

    "2025-01-26", "2025-03-14", "2025-08-15",
    "2025-10-02", "2025-10-20", "2025-12-25",

    "2026-01-26", "2026-03-04", "2026-08-15",
    "2026-10-02", "2026-11-08", "2026-12-25"
}


def get_season(month):
    """Assign an India-oriented season based on the month."""

    if month in [12, 1, 2]:
        return "Winter"
    elif month in [3, 4, 5]:
        return "Summer"
    elif month in [6, 7, 8, 9]:
        return "Monsoon"
    else:
        return "Post-Monsoon"


def generate_calendar():
    engine = get_engine()

    dates = pd.date_range(
        start=START_DATE,
        end=END_DATE,
        freq="D"
    )

    calendar_df = pd.DataFrame({
        "calendar_date": dates,
        "day_number": dates.day,
        "day_name": dates.day_name(),
        "week_number": dates.isocalendar().week.astype(int),
        "month_number": dates.month,
        "month_name": dates.month_name(),
        "quarter_number": dates.quarter,
        "year_number": dates.year,
        "season": [get_season(month) for month in dates.month],
        "is_weekend": dates.dayofweek >= 5,
        "is_holiday": [
            date.strftime("%Y-%m-%d") in HOLIDAYS
            for date in dates
        ]
    })

    # Avoid inserting dates that already exist
    with engine.connect() as connection:
        existing_dates = pd.read_sql(
            text("SELECT calendar_date FROM calendar"),
            connection
        )

    if not existing_dates.empty:
        existing_dates["calendar_date"] = pd.to_datetime(
            existing_dates["calendar_date"]
        ).dt.date

        calendar_df["calendar_date"] = pd.to_datetime(
            calendar_df["calendar_date"]
        ).dt.date

        calendar_df = calendar_df[
            ~calendar_df["calendar_date"].isin(
                existing_dates["calendar_date"]
            )
        ]

    if calendar_df.empty:
        print("Calendar table already contains all dates.")
        return

    records = calendar_df.to_dict(orient="records")

    with engine.begin() as connection:
        connection.execute(
            Calendar.__table__.insert(),
            records
        )

    print("Calendar data generated successfully!")
    print(f"New records inserted: {len(records)}")


if __name__ == "__main__":
    generate_calendar()
