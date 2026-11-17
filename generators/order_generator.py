
import uuid
import random
from datetime import date, datetime, timedelta

from sqlalchemy import text

from database.connection import get_engine


random.seed(42)

# Five-year order volume with annual business growth
YEARLY_ORDER_COUNTS = {
    2022: 3200,
    2023: 3600,
    2024: 4000,
    2025: 4400,
    2026: 4800
}

# Monthly demand variation
# Higher demand during selected procurement and festive periods
MONTHLY_DEMAND_WEIGHTS = {
    1: 1.15,
    2: 1.10,
    3: 1.20,
    4: 0.85,
    5: 0.90,
    6: 0.95,
    7: 1.00,
    8: 1.05,
    9: 1.20,
    10: 1.35,
    11: 1.30,
    12: 1.10
}

BATCH_SIZE = 1000


def get_quantity_range(category):
    """Return realistic order quantity ranges by product category."""

    quantity_ranges = {
        "Automotive Parts": (50, 500),
        "Electrical Components": (20, 250),
        "Mechanical Components": (30, 300),
        "Metal Components": (100, 1000)
    }

    return quantity_ranges.get(category, (20, 200))


def get_order_status(order_date):
    """Assign order status based on order date."""

    # Future orders cannot already be delivered
    if order_date > date.today():
        return "Pending"

    return random.choices(
        ["Delivered", "In Production", "Pending", "Cancelled"],
        weights=[82, 8, 4, 6]
    )[0]


def generate_order_dates(calendar_records, year, count):
    """Generate order dates using seasonal and calendar patterns."""

    dates = []
    weights = []

    for record in calendar_records:
        current_date = record["calendar_date"]

        if current_date.year != year:
            continue

        weight = MONTHLY_DEMAND_WEIGHTS[current_date.month]

        # Weekend orders are less frequent
        if record["is_weekend"]:
            weight *= 0.65

        # Holiday shutdowns reduce order activity
        if record["is_holiday"]:
            weight *= 0.15

        dates.append(current_date)
        weights.append(weight)

    if not dates:
        raise ValueError(f"No calendar records found for {year}")

    return random.choices(
        dates,
        weights=weights,
        k=count
    )


def generate_orders():
    engine = get_engine()

    with engine.connect() as connection:

        # Prevent accidental duplicate generation
        existing_count = connection.execute(
            text("SELECT COUNT(*) FROM orders")
        ).scalar()

        if existing_count > 0:
            print(
                f"Orders table already contains {existing_count} records."
            )
            print("Skipping generation to avoid duplicates.")
            return

        # Fetch customers
        customers = connection.execute(
            text("SELECT customer_id FROM customers")
        ).scalars().all()

        # Fetch products and prices
        products = connection.execute(
            text("""
                SELECT
                    product_id,
                    category,
                    standard_price
                FROM products
                WHERE is_active = 1
            """)
        ).mappings().all()

        # Fetch calendar
        calendar_records = connection.execute(
            text("""
                SELECT
                    calendar_date,
                    is_weekend,
                    is_holiday
                FROM calendar
                WHERE calendar_date BETWEEN
                    '2022-01-01' AND '2026-12-31'
            """)
        ).mappings().all()

    if not customers:
        raise ValueError("No customers found. Generate customers first.")

    if not products:
        raise ValueError("No active products found.")

    if not calendar_records:
        raise ValueError("Calendar table is empty.")

    # Generate orders year by year
    all_orders = []

    for year, order_count in YEARLY_ORDER_COUNTS.items():

        selected_dates = generate_order_dates(
            calendar_records,
            year,
            order_count
        )

        for order_date in selected_dates:

            customer_id = random.choice(customers)
            product = random.choice(products)

            min_qty, max_qty = get_quantity_range(
                product["category"]
            )

            quantity = random.randint(min_qty, max_qty)

            # Small price variation around standard product price
            unit_price = round(
                float(product["standard_price"])
                * random.uniform(0.95, 1.05),
                2
            )

            # Delivery lead time between 3 and 30 days
            delivery_days = random.randint(3, 30)

            requested_delivery_date = (
                order_date + timedelta(days=delivery_days)
            )

            order_status = get_order_status(order_date)

            created_at = datetime.combine(
                order_date,
                datetime.min.time()
            ) + timedelta(
                hours=random.randint(8, 17),
                minutes=random.randint(0, 59)
            )

            all_orders.append({
                "order_id": str(uuid.uuid4()),
                "customer_id": customer_id,
                "product_id": product["product_id"],
                "order_date": order_date,
                "requested_delivery_date": requested_delivery_date,
                "quantity_ordered": quantity,
                "order_status": order_status,
                "unit_price": unit_price,
                "created_at": created_at
            })

    # Insert orders in batches
    insert_query = text("""
        INSERT INTO orders (
            order_id,
            customer_id,
            product_id,
            order_date,
            requested_delivery_date,
            quantity_ordered,
            order_status,
            unit_price,
            created_at
        )
        VALUES (
            :order_id,
            :customer_id,
            :product_id,
            :order_date,
            :requested_delivery_date,
            :quantity_ordered,
            :order_status,
            :unit_price,
            :created_at
        )
    """)

    with engine.begin() as connection:

        for start in range(0, len(all_orders), BATCH_SIZE):

            batch = all_orders[
                start:start + BATCH_SIZE
            ]

            connection.execute(insert_query, batch)

            print(
                f"Inserted {min(start + BATCH_SIZE, len(all_orders))}"
                f" / {len(all_orders)} orders"
            )

    print("\nOrder data generated successfully!")
    print(f"Total orders inserted: {len(all_orders)}")


if __name__ == "__main__":
    generate_orders()
