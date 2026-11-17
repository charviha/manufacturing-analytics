
import uuid
import random
import math

from bisect import bisect_left
from collections import defaultdict
from datetime import datetime, date, time, timedelta

from sqlalchemy import text

from database.connection import get_engine


random.seed(42)

BATCH_SIZE = 1000

# Product category to suitable production-line mapping
CATEGORY_LINE_MAPPING = {
    "Mechanical Components": [
        "Machining Line A",
        "Welding Line A",
        "Assembly Line A",
        "Assembly Line B",
        "Packaging Line A"
    ],

    "Electrical Components": [
        "Assembly Line A",
        "Assembly Line B",
        "Machining Line A",
        "Packaging Line A",
        "Welding Line A"
    ],

    "Automotive Parts": [
        "Assembly Line A",
        "Assembly Line B",
        "Machining Line A",
        "Welding Line A"
    ],

    "Metal Components": [
        "Machining Line A",
        "Welding Line A",
        "Painting Line A",
        "Packaging Line A"
    ]
}


def get_business_dates(connection):
    """Fetch working dates excluding weekends and holidays."""

    dates = connection.execute(
        text("""
            SELECT calendar_date
            FROM calendar
            WHERE is_weekend = 0
              AND is_holiday = 0
            ORDER BY calendar_date
        """)
    ).scalars().all()

    return dates


def get_orders(connection):
    """Fetch orders eligible for production."""

    orders = connection.execute(
        text("""
            SELECT
                o.order_id,
                o.order_date,
                o.quantity_ordered,
                o.order_status,
                p.category
            FROM orders o
            JOIN products p
                ON o.product_id = p.product_id
            WHERE o.order_status IN (
                'Delivered',
                'In Production'
            )
            ORDER BY o.order_date
        """)
    ).mappings().all()

    return orders


def get_available_lines(connection):
    """
    Fetch active production lines having at least one
    active production-capable assigned machine.
    """

    rows = connection.execute(
        text("""
            SELECT
                pl.line_id,
                pl.line_name,
                pl.line_capacity_per_hour,
                MIN(le.assigned_from) AS available_from
            FROM production_lines pl

            JOIN line_equipment le
                ON pl.line_id = le.line_id

            JOIN equipment e
                ON le.equipment_id = e.equipment_id

            WHERE pl.is_active = 1
              AND e.equipment_status = 'Active'
              AND e.equipment_type <> 'Quality Control'
              AND (
                    le.assigned_to IS NULL
                    OR le.assigned_to >= le.assigned_from
                  )

            GROUP BY
                pl.line_id,
                pl.line_name,
                pl.line_capacity_per_hour

            HAVING COUNT(*) > 0
        """)
    ).mappings().all()

    return list(rows)



def choose_production_line(category, order_date, available_lines,
                           business_dates):

    preferred_lines = CATEGORY_LINE_MAPPING.get(category)

    if not preferred_lines:
        return None, None, None

    candidates = []

    for line in available_lines:

        if line["line_name"] not in preferred_lines:
            continue

        if not line["line_capacity_per_hour"]:
            continue

        earliest_date = max(
            order_date,
            line["available_from"]
        )

        date_index = bisect_left(
            business_dates,
            earliest_date
        )

        if date_index >= len(business_dates):
            continue

        production_date = business_dates[date_index]

        candidates.append({
            "line": line,
            "production_date": production_date,
            "date_index": date_index
        })

    if not candidates:
        return None, None, None

    # Select the earliest feasible production date
    earliest_date = min(
        candidate["production_date"]
        for candidate in candidates
    )

    earliest_candidates = [
        candidate
        for candidate in candidates
        if candidate["production_date"] == earliest_date
    ]

    # Randomly distribute work among equally eligible lines
    selected = random.choice(earliest_candidates)

    return (
        selected["line"],
        selected["production_date"],
        selected["date_index"]
    )



def calculate_production_quantity(order):
    """
    Calculate the good quantity required from the order.

    Delivered orders: full quantity.
    In Production orders: partially completed quantity.
    """

    ordered_quantity = int(order["quantity_ordered"])

    if order["order_status"] == "Delivered":
        return ordered_quantity

    # An order still in production has partial output
    completion_percentage = random.uniform(0.35, 0.85)

    return max(
        1,
        int(ordered_quantity * completion_percentage)
    )


def split_into_batches(good_quantity, line_capacity):
    """Split production into manageable daily batches."""

    maximum_good_quantity = max(
        1,
        int(line_capacity * 5.5)
    )

    batches = []

    remaining = good_quantity

    while remaining > 0:

        batch_quantity = min(
            remaining,
            maximum_good_quantity
        )

        batches.append(batch_quantity)

        remaining -= batch_quantity

    return batches


def generate_run_records(order, line, first_date_index,
                         business_dates):
    """Generate one or more production runs for an order."""

    good_quantity = calculate_production_quantity(order)

    line_capacity = int(
        line["line_capacity_per_hour"]
    )

    batches = split_into_batches(
        good_quantity,
        line_capacity
    )

    ideal_cycle_time = 3600 / line_capacity

    records = []

    for batch_number, good_batch_quantity in enumerate(batches):

        date_index = first_date_index + batch_number

        if date_index >= len(business_dates):
            break

        run_date = business_dates[date_index]

        # Scrap is a percentage of gross production
        scrap_rate = random.uniform(0.005, 0.03)

        gross_quantity = math.ceil(
            good_batch_quantity / (1 - scrap_rate)
        )

        scrap_quantity = (
            gross_quantity - good_batch_quantity
        )

        # Performance varies between production runs
        performance_factor = random.uniform(0.88, 1.05)

        planned_minutes = (
            ideal_cycle_time
            * gross_quantity
            / 60
            / performance_factor
        )

        planned_minutes = round(planned_minutes, 2)

        # Production shift starts between 8 AM and 9 AM
        start_time = datetime.combine(
            run_date,
            time(8, 0)
        ) + timedelta(
            minutes=random.randint(0, 60)
        )

        end_time = start_time + timedelta(
            minutes=planned_minutes
        )

        records.append({
            "run_id": str(uuid.uuid4()),
            "order_id": order["order_id"],
            "line_id": line["line_id"],
            "run_date": run_date,
            "start_time": start_time,
            "end_time": end_time,
            "quantity_produced": gross_quantity,
            "scrap_quantity": scrap_quantity,
            "planned_production_minutes": planned_minutes,
            "ideal_cycle_time_seconds": round(
                ideal_cycle_time,
                4
            ),
            "run_status": "Completed"
        })

    return records


def generate_production_runs():

    engine = get_engine()

    print("Starting production-run generation...")

    with engine.connect() as connection:

        # Prevent duplicate generation
        existing_count = connection.execute(
            text("SELECT COUNT(*) FROM production_runs")
        ).scalar()

        if existing_count > 0:
            print(
                f"Production runs already exist: {existing_count}"
            )
            print("Skipping to prevent duplicate records.")
            return

        orders = get_orders(connection)

        available_lines = get_available_lines(connection)

        business_dates = get_business_dates(connection)

    if not orders:
        raise ValueError(
            "No eligible orders found. Generate orders first."
        )

    if not available_lines:
        raise ValueError(
            "No production lines with available equipment found."
        )

    if not business_dates:
        raise ValueError(
            "No working calendar dates found."
        )

    print(f"Eligible orders: {len(orders)}")
    print(f"Available production lines: {len(available_lines)}")

    print("\nAvailable production lines:")

    for line in available_lines:
        print(
            f"{line['line_name']} | "
            f"Capacity: {line['line_capacity_per_hour']} units/hour | "
            f"Available from: {line['available_from']}"
        )

    all_records = []

    skipped_orders = 0

    order_status_counts = defaultdict(int)

    for order in orders:

        line, production_date, date_index = choose_production_line(
            order["category"],
            order["order_date"],
            available_lines,
            business_dates
        )

        if line is None:
            skipped_orders += 1
            continue

        records = generate_run_records(
            order,
            line,
            date_index,
            business_dates
        )

        if not records:
            skipped_orders += 1
            continue

        all_records.extend(records)

        order_status_counts[order["order_status"]] += 1

    if not all_records:
        raise ValueError(
            "No production runs could be generated."
        )

    insert_query = text("""
        INSERT INTO production_runs (
            run_id,
            order_id,
            line_id,
            run_date,
            start_time,
            end_time,
            quantity_produced,
            scrap_quantity,
            planned_production_minutes,
            ideal_cycle_time_seconds,
            run_status
        )
        VALUES (
            :run_id,
            :order_id,
            :line_id,
            :run_date,
            :start_time,
            :end_time,
            :quantity_produced,
            :scrap_quantity,
            :planned_production_minutes,
            :ideal_cycle_time_seconds,
            :run_status
        )
    """)

    print("\nInserting production runs...")

    # Single transaction: either all records are inserted or none
    with engine.begin() as connection:

        for start in range(0, len(all_records), BATCH_SIZE):

            batch = all_records[
                start:start + BATCH_SIZE
            ]

            connection.execute(
                insert_query,
                batch
            )

            print(
                f"Inserted {min(start + BATCH_SIZE, len(all_records))}"
                f" / {len(all_records)} production runs"
            )

    print("\nProduction runs generated successfully!")

    print(f"Eligible orders processed: {sum(order_status_counts.values())}")
    print(f"Production runs inserted: {len(all_records)}")
    print(f"Orders skipped: {skipped_orders}")

    print("\nProcessed order status counts:")

    for status, count in order_status_counts.items():
        print(f"{status}: {count}")


if __name__ == "__main__":
    generate_production_runs()
