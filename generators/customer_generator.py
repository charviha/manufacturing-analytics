
import uuid
import random

from faker import Faker

from database.connection import get_engine
from database.schema import Customer


fake = Faker("en_IN")
random.seed(42)
Faker.seed(42)


LOCATIONS = [
    "Bengaluru",
    "Chennai",
    "Hyderabad",
    "Pune",
    "Mumbai",
    "Coimbatore",
    "Ahmedabad",
    "Delhi",
    "Gurugram",
    "Noida"
]

INDUSTRIES = [
    "Automotive",
    "Electronics",
    "Aerospace",
    "Industrial Machinery",
    "Consumer Goods",
    "Electrical Equipment",
    "Construction",
    "Medical Equipment",
    "Metal Fabrication",
    "Telecommunications"
]

CUSTOMER_TYPES = [
    "Enterprise",
    "SME",
    "Small Business"
]


def generate_customers():
    engine = get_engine()

    customer_records = []

    for _ in range(500):
        customer_records.append({
            "customer_id": str(uuid.uuid4()),
            "customer_name": fake.company(),
            "location": random.choice(LOCATIONS),
            "industry": random.choice(INDUSTRIES),
            "customer_type": random.choices(
                CUSTOMER_TYPES,
                weights=[20, 50, 30]
            )[0]
        })

    with engine.begin() as connection:
        connection.execute(
            Customer.__table__.insert(),
            customer_records
        )

    print("Customer data generated successfully!")
    print(f"New customers inserted: {len(customer_records)}")


if __name__ == "__main__":
    generate_customers()
