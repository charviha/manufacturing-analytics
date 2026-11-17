
import random
import uuid
from datetime import date, timedelta

from sqlalchemy import text
from database.connection import get_engine


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

random.seed(42)

DATA_START_DATE = date(2022, 1, 1)
DATA_END_DATE = date(2026, 11, 16)

TOTAL_EVENTS = 200
BATCH_SIZE = 500


# --------------------------------------------------
# EVENT CONFIGURATION
# --------------------------------------------------

EVENT_TYPES = {
    "Raw Material Shortage": [
        "Insufficient raw material inventory affected production.",
        "Required raw materials were unavailable in sufficient quantities.",
        "Material replenishment was delayed due to low supplier stock."
    ],

    "Supplier Delay": [
        "Supplier shipment arrived later than the scheduled delivery date.",
        "Supplier production delays affected material availability.",
        "Delayed supplier dispatch disrupted the procurement schedule."
    ],

    "Transportation Delay": [
        "Transportation disruption delayed the arrival of materials.",
        "Logistics delays affected the planned material delivery.",
        "Shipment movement was delayed due to transportation constraints."
    ],

    "Material Quality Issue": [
        "Incoming material failed quality inspection.",
        "Defective raw materials required additional inspection and replacement.",
        "Material quality issues delayed production readiness."
    ],

    "Inventory Shortage": [
        "Available inventory was insufficient to meet production requirements.",
        "Stock levels fell below the required production quantity.",
        "Inventory replenishment was required to avoid production delays."
    ],

    "Supplier Capacity Constraint": [
        "Supplier capacity was insufficient to meet the requested quantity.",
        "Supplier production constraints delayed material availability.",
        "Supplier could not fulfil the complete material requirement."
    ]
}


SEVERITY_WEIGHTS = {
    "Low": 30,
    "Medium": 40,
    "High": 22,
    "Critical": 8
}


SHORTAGE_RANGES = {
    "Low": (20, 100),
    "Medium": (101, 300),
    "High": (301, 700),
    "Critical": (701, 1500)
}


DURATION_RANGES = {
    "Low": (1, 2),
    "Medium": (2, 5),
    "High": (4, 9),
    "Critical": (7, 14)
}


# --------------------------------------------------
# RANDOM DATE GENERATION
# --------------------------------------------------

def random_event_date():

    total_days = (
        DATA_END_DATE - DATA_START_DATE
    ).days

    random_days = random.randint(0, total_days)

    return DATA_START_DATE + timedelta(
        days=random_days
    )


# --------------------------------------------------
# GENERATE SUPPLY CHAIN EVENTS
# --------------------------------------------------

def generate_supply_chain_events():

    engine = get_engine()

    # --------------------------------------------------
    # FETCH EXISTING PRODUCTS AND OPERATIONAL LINES
    # --------------------------------------------------

    with engine.connect() as connection:

        existing_count = connection.execute(
            text("SELECT COUNT(*) FROM supply_chain_events")
        ).scalar()

        if existing_count > 0:
            print(
                f"Supply-chain events already exist: "
                f"{existing_count}"
            )
            print("Skipping generation.")
            return

        products = connection.execute(
            text("""
                SELECT product_id
                FROM products
                WHERE is_active = 1
            """)
        ).scalars().all()

        # A line becomes eligible from its first production run.
        lines = connection.execute(
            text("""
                SELECT
                    line_id,
                    MIN(run_date) AS operational_start
                FROM production_runs
                GROUP BY line_id
            """)
        ).mappings().all()

    if not products:
        print("No active products found.")
        return

    if not lines:
        print("No operational production lines found.")
        return

    event_records = []

    severity_names = list(SEVERITY_WEIGHTS.keys())
    severity_weights = list(SEVERITY_WEIGHTS.values())

    event_type_names = list(EVENT_TYPES.keys())

    # --------------------------------------------------
    # CREATE EVENTS
    # --------------------------------------------------

    for _ in range(TOTAL_EVENTS):

        event_start = random_event_date()

        event_type = random.choice(event_type_names)

        severity = random.choices(
            severity_names,
            weights=severity_weights,
            k=1
        )[0]

        # Duration depends on event severity.
        minimum_duration, maximum_duration = (
            DURATION_RANGES[severity]
        )

        duration_days = random.randint(
            minimum_duration,
            maximum_duration
        )

        event_end = min(
            event_start + timedelta(days=duration_days),
            DATA_END_DATE
        )

        # Shortage quantity depends on severity.
        minimum_shortage, maximum_shortage = (
            SHORTAGE_RANGES[severity]
        )

        shortage_quantity = random.randint(
            minimum_shortage,
            maximum_shortage
        )

        # Every event affects a product.
        product_id = random.choice(products)

        # Some events affect a specific production line.
        eligible_lines = [
            line for line in lines
            if line["operational_start"] <= event_start
        ]

        if eligible_lines and random.random() < 0.65:
            selected_line = random.choice(eligible_lines)
            line_id = selected_line["line_id"]
        else:
            line_id = None

        # Some events may affect the broader supply chain
        # without a specific product or line being identified.
        if random.random() < 0.15:
            product_id = None
            line_id = None

        event_description = random.choice(
            EVENT_TYPES[event_type]
        )

        event_records.append({
            "event_id": str(uuid.uuid4()),
            "product_id": product_id,
            "line_id": line_id,
            "event_start": event_start,
            "event_end": event_end,
            "event_type": event_type,
            "event_description": event_description,
            "shortage_quantity": shortage_quantity,
            "severity": severity
        })

    # --------------------------------------------------
    # INSERT INTO MYSQL
    # --------------------------------------------------

    insert_query = text("""
        INSERT INTO supply_chain_events (
            event_id,
            product_id,
            line_id,
            event_start,
            event_end,
            event_type,
            event_description,
            shortage_quantity,
            severity
        )
        VALUES (
            :event_id,
            :product_id,
            :line_id,
            :event_start,
            :event_end,
            :event_type,
            :event_description,
            :shortage_quantity,
            :severity
        )
    """)

    with engine.begin() as connection:

        for start in range(
            0,
            len(event_records),
            BATCH_SIZE
        ):

            batch = event_records[
                start:start + BATCH_SIZE
            ]

            connection.execute(
                insert_query,
                batch
            )

    print("\nSupply-chain event generation completed.")

    print(f"Total events generated: {len(event_records)}")

    print(
        f"Events with product references: "
        f"{sum(1 for e in event_records if e['product_id'])}"
    )

    print(
        f"Events with line references: "
        f"{sum(1 for e in event_records if e['line_id'])}"
    )


# --------------------------------------------------
# MAIN
# --------------------------------------------------

if __name__ == "__main__":
    generate_supply_chain_events()
