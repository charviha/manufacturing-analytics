
import uuid
import random
from datetime import date, timedelta

from faker import Faker

from database.connection import get_engine
from database.schema import Equipment

fake = Faker("en_IN")
random.seed(42)
Faker.seed(42)


EQUIPMENT_TYPES = {
    "CNC Machine": ["CNC Lathe", "CNC Milling Machine"],
    "Assembly": ["Robotic Arm", "Assembly Robot"],
    "Welding": ["Arc Welding Machine", "Spot Welding Machine"],
    "Painting": ["Spray Painting Machine", "Powder Coating Machine"],
    "Packaging": ["Automatic Packaging Machine", "Labeling Machine"],
    "Quality Control": ["Inspection Machine", "Coordinate Measuring Machine"]
}

MANUFACTURERS = [
    "Siemens",
    "Bosch",
    "ABB",
    "Fanuc",
    "Mitsubishi Electric",
    "Yaskawa",
    "KUKA",
    "Danfoss"
]

STATUSES = ["Operational", "Operational", "Operational",
            "Under Maintenance", "Inactive"]


def generate_equipment():
    engine = get_engine()

    equipment_records = []

    for i in range(1, 31):
        equipment_type = random.choice(list(EQUIPMENT_TYPES.keys()))

        equipment_name = random.choice(
            EQUIPMENT_TYPES[equipment_type]
        ) + f" {i:02d}"

        installation_date = fake.date_between(
            start_date=date(2018, 1, 1),
            end_date=date(2025, 12, 31)
        )

        equipment_records.append({
            "equipment_id": str(uuid.uuid4()),
            "equipment_name": equipment_name,
            "equipment_type": equipment_type,
            "manufacturer": random.choice(MANUFACTURERS),
            "installation_date": installation_date,
            "equipment_status": random.choice(STATUSES),
        })

    with engine.begin() as connection:
        connection.execute(
            Equipment.__table__.insert(),
            equipment_records
        )

    print("Equipment data generated successfully!")
    print(f"New equipment records inserted: {len(equipment_records)}")


if __name__ == "__main__":
    generate_equipment()
