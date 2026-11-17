
import uuid
import random
from datetime import date, timedelta

from sqlalchemy import select

from database.connection import get_engine
from database.schema import ProductionLine, Equipment, LineEquipment


random.seed(42)

END_DATE = date(2026, 11, 16)


def generate_line_equipment():
    engine = get_engine()

    # Fetch production lines
    with engine.connect() as connection:
        lines = connection.execute(
            select(ProductionLine.line_id)
        ).scalars().all()

        # Fetch equipment and installation dates
        equipment = connection.execute(
            select(
                Equipment.equipment_id,
                Equipment.installation_date
            )
        ).all()

        # Fetch equipment already assigned
        existing_equipment_ids = set(
            connection.execute(
                select(LineEquipment.equipment_id)
            ).scalars().all()
        )

    if not lines:
        print("No production lines found. Generate production lines first.")
        return

    if not equipment:
        print("No equipment found. Generate equipment first.")
        return

    # Avoid duplicate assignments
    unassigned_equipment = [
        item for item in equipment
        if item.equipment_id not in existing_equipment_ids
    ]

    if not unassigned_equipment:
        print("All equipment is already assigned to production lines.")
        return

    random.shuffle(unassigned_equipment)

    assignment_records = []

    # Distribute equipment across production lines
    for index, item in enumerate(unassigned_equipment):

        line_id = lines[index % len(lines)]

        installation_date = item.installation_date or date(2022, 1, 1)

        # Assignment cannot happen before equipment installation
        earliest_date = max(installation_date, date(2022, 1, 1))

        available_days = (END_DATE - earliest_date).days

        if available_days < 0:
            print(
                f"Invalid installation date for equipment "
                f"{item.equipment_id}"
            )
            continue

        assigned_from = earliest_date + timedelta(
            days=random.randint(0, available_days)
        )

        assignment_records.append({
            "line_equipment_id": str(uuid.uuid4()),
            "line_id": line_id,
            "equipment_id": item.equipment_id,
            "assigned_from": assigned_from,
            "assigned_to": None
        })

    if not assignment_records:
        print("No valid equipment assignments generated.")
        return

    with engine.begin() as connection:
        connection.execute(
            LineEquipment.__table__.insert(),
            assignment_records
        )

    print("Line-equipment assignments generated successfully!")
    print(f"New assignments inserted: {len(assignment_records)}")


if __name__ == "__main__":
    generate_line_equipment()
