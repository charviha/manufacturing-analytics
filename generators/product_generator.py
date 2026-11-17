
import uuid
import random

from database.connection import get_engine
from database.schema import Product


random.seed(42)


PRODUCTS = [
    {
        "product_name": "Industrial Electric Motor",
        "category": "Electrical Components",
        "unit_of_measure": "Units",
        "standard_price": 12500.00
    },
    {
        "product_name": "Hydraulic Pump",
        "category": "Mechanical Components",
        "unit_of_measure": "Units",
        "standard_price": 18500.00
    },
    {
        "product_name": "Steel Gear Assembly",
        "category": "Mechanical Components",
        "unit_of_measure": "Units",
        "standard_price": 4200.00
    },
    {
        "product_name": "Automotive Brake Disc",
        "category": "Automotive Parts",
        "unit_of_measure": "Units",
        "standard_price": 1800.00
    },
    {
        "product_name": "Aluminium Housing",
        "category": "Automotive Parts",
        "unit_of_measure": "Units",
        "standard_price": 950.00
    },
    {
        "product_name": "Industrial Control Panel",
        "category": "Electrical Components",
        "unit_of_measure": "Units",
        "standard_price": 22000.00
    },
    {
        "product_name": "Stainless Steel Valve",
        "category": "Mechanical Components",
        "unit_of_measure": "Units",
        "standard_price": 3200.00
    },
    {
        "product_name": "Automotive Transmission Shaft",
        "category": "Automotive Parts",
        "unit_of_measure": "Units",
        "standard_price": 5600.00
    },
    {
        "product_name": "Industrial Bearing",
        "category": "Mechanical Components",
        "unit_of_measure": "Units",
        "standard_price": 750.00
    },
    {
        "product_name": "Copper Electrical Connector",
        "category": "Electrical Components",
        "unit_of_measure": "Units",
        "standard_price": 180.00
    },
    {
        "product_name": "Steel Mounting Bracket",
        "category": "Metal Components",
        "unit_of_measure": "Units",
        "standard_price": 450.00
    },
    {
        "product_name": "Precision Metal Shaft",
        "category": "Metal Components",
        "unit_of_measure": "Units",
        "standard_price": 1250.00
    },
    {
        "product_name": "Industrial Fan Assembly",
        "category": "Electrical Components",
        "unit_of_measure": "Units",
        "standard_price": 6800.00
    },
    {
        "product_name": "Automotive Clutch Plate",
        "category": "Automotive Parts",
        "unit_of_measure": "Units",
        "standard_price": 2100.00
    },
    {
        "product_name": "Precision Gearbox",
        "category": "Mechanical Components",
        "unit_of_measure": "Units",
        "standard_price": 14500.00
    },
    {
        "product_name": "Steel Sheet Panel",
        "category": "Metal Components",
        "unit_of_measure": "Kilograms",
        "standard_price": 95.00
    },
    {
        "product_name": "Aluminium Rod",
        "category": "Metal Components",
        "unit_of_measure": "Kilograms",
        "standard_price": 280.00
    },
    {
        "product_name": "Industrial Sensor Module",
        "category": "Electrical Components",
        "unit_of_measure": "Units",
        "standard_price": 3500.00
    },
    {
        "product_name": "Automotive Suspension Arm",
        "category": "Automotive Parts",
        "unit_of_measure": "Units",
        "standard_price": 2900.00
    },
    {
        "product_name": "Hydraulic Cylinder",
        "category": "Mechanical Components",
        "unit_of_measure": "Units",
        "standard_price": 7800.00
    }
]


def generate_products():
    engine = get_engine()

    product_records = []

    for product in PRODUCTS:
        record = product.copy()

        record["product_id"] = str(uuid.uuid4())
        record["is_active"] = random.choices(
            [True, False],
            weights=[95, 5]
        )[0]

        product_records.append(record)

    with engine.begin() as connection:
        connection.execute(
            Product.__table__.insert(),
            product_records
        )

    print("Product data generated successfully!")
    print(f"New products inserted: {len(product_records)}")


if __name__ == "__main__":
    generate_products()
