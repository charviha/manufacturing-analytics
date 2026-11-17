
import random
import uuid
from datetime import date, timedelta

from sqlalchemy import text
from database.connection import get_engine


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

random.seed(42)

DATA_END_DATE = date(2026, 11, 16)

SHIFTS = ["Morning", "Evening", "Night"]

BATCH_SIZE = 1000


# --------------------------------------------------
# WORKFORCE CONFIGURATION
# --------------------------------------------------

def get_planned_workers(capacity):
    """
    Estimate planned workers based on line capacity.
    """

    if capacity >= 180:
        return random.randint(12, 16)

    elif capacity >= 110:
        return random.randint(10, 14)

    elif capacity >= 90:
        return random.randint(8, 12)

    else:
        return random.randint(6, 10)


# --------------------------------------------------
# GENERATE STAFFING DATA
# --------------------------------------------------

def generate_staffing():

    engine = get_engine()

    with engine.connect() as connection:

        existing_count = connection.execute(
            text("SELECT COUNT(*) FROM staffing")
        ).scalar()

        if existing_count > 0:
            print(
                f"Staffing records already exist: "
                f"{existing_count}"
            )
            print("Skipping generation.")
            return

        # Get active production lines with active,
        # non-quality-control equipment assignments.
        lines = connection.execute(
            text("""
                SELECT
                    pl.line_id,
                    pl.line_name,
                    pl.line_capacity_per_hour,
                    MIN(le.assigned_from) AS operational_start
                FROM production_lines pl
                JOIN line_equipment le
                    ON pl.line_id = le.line_id
                JOIN equipment e
                    ON le.equipment_id = e.equipment_id
                WHERE pl.is_active = 1
                  AND e.equipment_status = 'Active'
                  AND e.equipment_type <> 'Quality Control'
                  AND le.assigned_from <= :end_date
                  AND (
                      le.assigned_to IS NULL
                      OR le.assigned_to >= :end_date
                  )
                GROUP BY
                    pl.line_id,
                    pl.line_name,
                    pl.line_capacity_per_hour
                ORDER BY pl.line_name
            """),
            {"end_date": DATA_END_DATE}
        ).mappings().all()

        # Get calendar information.
        calendar_rows = connection.execute(
            text("""
                SELECT
                    calendar_date,
                    is_weekend,
                    is_holiday
                FROM calendar
                WHERE calendar_date <= :end_date
                ORDER BY calendar_date
            """),
            {"end_date": DATA_END_DATE}
        ).mappings().all()

    if not lines:
        print("No eligible production lines found.")
        return

    staffing_records = []

    for line in lines:

        line_start = line["operational_start"]
        capacity = line["line_capacity_per_hour"]

        if line_start > DATA_END_DATE:
            continue

        current_date = line_start

        while current_date <= DATA_END_DATE:

            # Find calendar details for this date.
            calendar_info = next(
                (
                    item for item in calendar_rows
                    if item["calendar_date"] == current_date
                ),
                None
            )

            if calendar_info is None:
                current_date += timedelta(days=1)
                continue

            is_weekend = bool(calendar_info["is_weekend"])
            is_holiday = bool(calendar_info["is_holiday"])

            for shift in SHIFTS:

                planned_workers = get_planned_workers(capacity)

                # Reduce workforce on weekends.
                if is_weekend:
                    planned_workers = max(
                        2,
                        round(planned_workers * 0.65)
                    )

                # Holidays represent scheduled shutdowns.
                if is_holiday:
                    planned_workers = 0

                # Actual attendance varies around planned staffing.
                if planned_workers == 0:
                    actual_workers = 0
                    overtime_hours = 0.0

                else:

                    attendance_factor = random.uniform(
                        0.85,
                        1.05
                    )

                    actual_workers = max(
                        0,
                        round(planned_workers * attendance_factor)
                    )

                    # Overtime is more likely when staffing
                    # is below the planned requirement.
                    if actual_workers < planned_workers:
                        overtime_hours = random.choices(
                            [0, 1, 2, 3],
                            weights=[30, 35, 25, 10],
                            k=1
                        )[0]

                    else:
                        overtime_hours = random.choices(
                            [0, 1, 2],
                            weights=[75, 20, 5],
                            k=1
                        )[0]

                staffing_records.append({
                    "staffing_id": str(uuid.uuid4()),
                    "line_id": line["line_id"],
                    "shift_date": current_date,
                    "shift_name": shift,
                    "planned_workers": planned_workers,
                    "actual_workers": actual_workers,
                    "overtime_hours": overtime_hours
                })

            current_date += timedelta(days=1)

    # --------------------------------------------------
    # INSERT RECORDS
    # --------------------------------------------------

    insert_query = text("""
        INSERT INTO staffing (
            staffing_id,
            line_id,
            shift_date,
            shift_name,
            planned_workers,
            actual_workers,
            overtime_hours
        )
        VALUES (
            :staffing_id,
            :line_id,
            :shift_date,
            :shift_name,
            :planned_workers,
            :actual_workers,
            :overtime_hours
        )
    """)

    with engine.begin() as connection:

        for start in range(
            0,
            len(staffing_records),
            BATCH_SIZE
        ):

            batch = staffing_records[
                start:start + BATCH_SIZE
            ]

            connection.execute(
                insert_query,
                batch
            )

    print("\nStaffing generation completed.")

    print(f"Eligible production lines: {len(lines)}")

    print(
        f"Staffing records generated: "
        f"{len(staffing_records)}"
    )

    print(f"Shifts per day: {len(SHIFTS)}")


# --------------------------------------------------
# MAIN
# --------------------------------------------------

if __name__ == "__main__":
    generate_staffing()
