
import random
import uuid
from datetime import date, datetime, time, timedelta

from sqlalchemy import text

from database.connection import get_engine


random.seed(42)

# Dataset ends on the current project date.
DATA_END_DATE = date(2026, 11, 16)

# Number of downtime events per machine per year.
EVENTS_PER_YEAR = {
    "Active": (2, 4),
    "Under Maintenance": (3, 5),
    "Inactive": (1, 2)
}

PLANNED_EVENTS = [
    (
        "Preventive Maintenance",
        "Scheduled preventive maintenance"
    ),
    (
        "Calibration",
        "Routine equipment calibration"
    ),
    (
        "Cleaning",
        "Scheduled equipment cleaning"
    )
]

UNPLANNED_EVENTS = [
    (
        "Breakdown",
        "Unexpected mechanical breakdown"
    ),
    (
        "Electrical Failure",
        "Electrical component failure"
    ),
    (
        "Mechanical Failure",
        "Unexpected mechanical component failure"
    ),
    (
        "Sensor Failure",
        "Equipment sensor malfunction"
    )
]


def get_equipment():
    """
    Retrieve equipment and its eligible assignment dates.
    """

    query = text("""
        SELECT
            e.equipment_id,
            e.equipment_name,
            e.equipment_status,
            e.installation_date,
            MIN(le.assigned_from) AS first_assigned_date
        FROM equipment e
        LEFT JOIN line_equipment le
            ON e.equipment_id = le.equipment_id
        GROUP BY
            e.equipment_id,
            e.equipment_name,
            e.equipment_status,
            e.installation_date
        ORDER BY e.equipment_name
    """)

    engine = get_engine()

    with engine.connect() as connection:
        records = connection.execute(query).mappings().all()

    return records


def generate_events_for_equipment(equipment):
    """
    Generate downtime events for one equipment item.
    """

    installation_date = equipment["installation_date"]
    assigned_date = equipment["first_assigned_date"]

    if installation_date is None:
        return []

    # Equipment must be installed and assigned before
    # its downtime events are generated.
    eligible_start = installation_date

    if assigned_date is not None:
        eligible_start = max(
            installation_date,
            assigned_date
        )

    if eligible_start > DATA_END_DATE:
        return []

    status = equipment["equipment_status"]

    min_events, max_events = EVENTS_PER_YEAR.get(
        status,
        (2, 3)
    )

    events = []

    # Generate events separately for each calendar year.
    for year in range(
        eligible_start.year,
        DATA_END_DATE.year + 1
    ):

        year_start = date(year, 1, 1)
        year_end = date(year, 12, 31)

        period_start = max(
            eligible_start,
            year_start
        )

        period_end = min(
            DATA_END_DATE,
            year_end
        )

        if period_start > period_end:
            continue

        available_days = (
            period_end - period_start
        ).days + 1

        event_count = random.randint(
            min_events,
            max_events
        )

        event_count = min(
            event_count,
            available_days
        )

        # Unique dates prevent two generated events from
        # overlapping on the same equipment and date.
        selected_days = sorted(
            random.sample(
                range(available_days),
                event_count
            )
        )

        for day_offset in selected_days:

            event_date = (
                period_start + timedelta(days=day_offset)
            )

            is_planned = random.random() < 0.35

            if is_planned:
                downtime_type, reason = random.choice(
                    PLANNED_EVENTS
                )
            else:
                downtime_type, reason = random.choice(
                    UNPLANNED_EVENTS
                )

            # Generate a start time between 7 AM and 3 PM.
            start_hour = random.randint(7, 15)
            start_minute = random.choice([0, 15, 30, 45])

            downtime_start = datetime.combine(
                event_date,
                time(start_hour, start_minute)
            )

            # Downtime duration between 1 and 5 hours.
            duration_minutes = random.randint(
                60,
                300
            )

            downtime_end = (
                downtime_start
                + timedelta(minutes=duration_minutes)
            )

            events.append({
                "downtime_id": str(uuid.uuid4()),
                "equipment_id": equipment["equipment_id"],
                "run_id": None,
                "downtime_start": downtime_start,
                "downtime_end": downtime_end,
                "downtime_type": downtime_type,
                "downtime_reason": reason,
                "is_planned": is_planned
            })

    return events


def generate_downtime_events():

    engine = get_engine()

    # Prevent accidental duplicate generation.
    with engine.connect() as connection:

        existing_count = connection.execute(
            text("""
                SELECT COUNT(*)
                FROM downtime_events
            """)
        ).scalar()

    if existing_count > 0:
        print(
            f"Downtime events already exist: {existing_count}"
        )
        print("Skipping generation to avoid duplicates.")
        return

    equipment_records = get_equipment()

    if not equipment_records:
        print("No equipment records found.")
        return

    all_events = []

    print(
        f"Generating downtime for "
        f"{len(equipment_records)} equipment items..."
    )

    for equipment in equipment_records:

        events = generate_events_for_equipment(
            equipment
        )

        all_events.extend(events)

        print(
            f"{equipment['equipment_name']}: "
            f"{len(events)} events"
        )

    if not all_events:
        print("No eligible downtime events generated.")
        return

    insert_query = text("""
        INSERT INTO downtime_events (
            downtime_id,
            equipment_id,
            run_id,
            downtime_start,
            downtime_end,
            downtime_type,
            downtime_reason,
            is_planned
        )
        VALUES (
            :downtime_id,
            :equipment_id,
            :run_id,
            :downtime_start,
            :downtime_end,
            :downtime_type,
            :downtime_reason,
            :is_planned
        )
    """)

    batch_size = 500
    total_inserted = 0

    with engine.begin() as connection:

        for start_index in range(
            0,
            len(all_events),
            batch_size
        ):

            batch = all_events[
                start_index:start_index + batch_size
            ]

            connection.execute(
                insert_query,
                batch
            )

            total_inserted += len(batch)

            print(
                f"Inserted {total_inserted} "
                f"/ {len(all_events)} events"
            )

    print("\nDowntime generation completed.")
    print(f"Equipment processed: {len(equipment_records)}")
    print(f"Total events generated: {total_inserted}")


if __name__ == "__main__":
    generate_downtime_events()
