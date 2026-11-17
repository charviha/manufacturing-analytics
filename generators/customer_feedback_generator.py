
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

FEEDBACK_RATE = 0.35
BATCH_SIZE = 1000


# --------------------------------------------------
# FEEDBACK TEXT
# --------------------------------------------------

FEEDBACK_TEXTS = {
    1: [
        "Very poor product quality. Not satisfied.",
        "The product did not meet our expectations.",
        "We experienced serious quality issues.",
        "Unhappy with the overall product quality."
    ],
    2: [
        "Product quality needs improvement.",
        "Delivery and product quality were disappointing.",
        "Some issues were found during inspection.",
        "The product was below our expectations."
    ],
    3: [
        "The product was acceptable but could improve.",
        "Average experience. Some improvements are needed.",
        "Quality was satisfactory, but not exceptional.",
        "The order met basic requirements."
    ],
    4: [
        "Good product quality and overall experience.",
        "Satisfied with the product.",
        "The product met our requirements.",
        "Good quality. We would consider ordering again."
    ],
    5: [
        "Excellent product quality and service.",
        "Very satisfied with the product.",
        "Outstanding quality. Highly recommended.",
        "Excellent experience. Looking forward to ordering again."
    ]
}


# --------------------------------------------------
# GENERATE CUSTOMER FEEDBACK
# --------------------------------------------------

def generate_customer_feedback():

    engine = get_engine()

    # Check whether feedback has already been generated
    with engine.connect() as connection:

        existing_count = connection.execute(
            text("SELECT COUNT(*) FROM customer_feedback")
        ).scalar()

        if existing_count > 0:
            print(
                f"Customer feedback already exists: "
                f"{existing_count} records."
            )
            print("Skipping generation.")
            return

        # Only delivered orders are eligible for feedback
        orders = connection.execute(
            text("""
                SELECT
                    order_id,
                    customer_id,
                    order_date
                FROM orders
                WHERE order_status = 'Delivered'
                  AND order_date <= :end_date
                ORDER BY order_date, order_id
            """),
            {"end_date": DATA_END_DATE}
        ).mappings().all()

    if not orders:
        print("No eligible delivered orders found.")
        return

    # Select a subset of delivered orders to simulate
    # customers who actually submitted feedback.
    feedback_count = round(len(orders) * FEEDBACK_RATE)

    selected_orders = random.sample(
        list(orders),
        feedback_count
    )

    feedback_records = []

    for order in selected_orders:

        order_date = order["order_date"]

        # Feedback can be submitted between the order date
        # and 14 days later, without exceeding the data end date.
        maximum_days = min(
            14,
            (DATA_END_DATE - order_date).days
        )

        feedback_days = random.randint(
            0,
            max(0, maximum_days)
        )

        feedback_date = order_date + timedelta(
            days=feedback_days
        )

        # Generate a rating from 1 to 5.
        # Higher ratings are more common in this synthetic dataset.
        rating = random.choices(
            population=[1, 2, 3, 4, 5],
            weights=[5, 10, 20, 30, 35],
            k=1
        )[0]

        is_positive = 1 if rating >= 4 else 0

        feedback_text = random.choice(
            FEEDBACK_TEXTS[rating]
        )

        feedback_records.append({
            "feedback_id": str(uuid.uuid4()),
            "customer_id": order["customer_id"],
            "order_id": order["order_id"],
            "feedback_date": feedback_date,
            "rating": rating,
            "feedback_text": feedback_text,
            "is_positive": is_positive
        })

    # --------------------------------------------------
    # INSERT INTO MYSQL
    # --------------------------------------------------

    insert_query = text("""
        INSERT INTO customer_feedback (
            feedback_id,
            customer_id,
            order_id,
            feedback_date,
            rating,
            feedback_text,
            is_positive
        )
        VALUES (
            :feedback_id,
            :customer_id,
            :order_id,
            :feedback_date,
            :rating,
            :feedback_text,
            :is_positive
        )
    """)

    with engine.begin() as connection:

        for start in range(
            0,
            len(feedback_records),
            BATCH_SIZE
        ):

            batch = feedback_records[
                start:start + BATCH_SIZE
            ]

            connection.execute(
                insert_query,
                batch
            )

    print("\nCustomer feedback generation completed.")
    print(f"Eligible delivered orders: {len(orders)}")
    print(f"Feedback response rate: {FEEDBACK_RATE * 100:.0f}%")
    print(f"Feedback records inserted: {len(feedback_records)}")


# --------------------------------------------------
# MAIN
# --------------------------------------------------

if __name__ == "__main__":
    generate_customer_feedback()
