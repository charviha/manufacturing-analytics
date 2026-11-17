
import random
import uuid

import pandas as pd
from sqlalchemy import text

from database.connection import get_engine


random.seed(42)


def get_production_runs(engine):
    """Fetch all production runs."""

    query = """
        SELECT
            run_id,
            line_id,
            run_date
        FROM production_runs
        ORDER BY run_date, run_id
    """

    return pd.read_sql_query(query, engine)


def get_eligible_equipment(engine):
    """
    Fetch active production equipment assigned to the same line
    and available on the production run date.
    """

    query = """
        SELECT
            pr.run_id,
            e.equipment_id,
            e.equipment_name,
            e.equipment_type,
            pl.line_name
        FROM production_runs pr
        JOIN production_lines pl
            ON pr.line_id = pl.line_id
        JOIN line_equipment le
            ON le.line_id = pr.line_id
        JOIN equipment e
            ON e.equipment_id = le.equipment_id
        WHERE e.equipment_status = 'Active'
          AND e.equipment_type <> 'Quality Control'
          AND le.assigned_from <= pr.run_date
          AND (
              le.assigned_to IS NULL
              OR le.assigned_to >= pr.run_date
          )
        ORDER BY pr.run_id
    """

    return pd.read_sql_query(query, engine)


def generate_run_equipment(engine):
    """Assign one eligible machine to every production run."""

    print("Fetching production runs...")

    runs = get_production_runs(engine)

    if runs.empty:
        raise ValueError("No production runs found.")

    print(f"Total production runs: {len(runs):,}")

    # Prevent accidental duplicate insertion.
    with engine.connect() as connection:
        existing_count = connection.execute(
            text("SELECT COUNT(*) FROM run_equipment")
        ).scalar()

    if existing_count > 0:
        raise ValueError(
            f"run_equipment already contains {existing_count:,} records. "
            "Skipping generation to prevent duplicates."
        )

    print("Fetching eligible equipment...")

    eligible_equipment = get_eligible_equipment(engine)

    # Group eligible machines by production run.
    equipment_by_run = (
        eligible_equipment
        .groupby("run_id")["equipment_id"]
        .apply(list)
        .to_dict()
    )

    records = []
    missing_runs = []

    for _, run in runs.iterrows():

        run_id = run["run_id"]

        available_equipment = equipment_by_run.get(run_id, [])

        if not available_equipment:
            missing_runs.append(run_id)
            continue

        # Select exactly one eligible production machine.
        selected_equipment = random.choice(available_equipment)

        records.append({
            "run_equipment_id": str(uuid.uuid4()),
            "run_id": run_id,
            "equipment_id": selected_equipment
        })

    if missing_runs:
        raise ValueError(
            f"{len(missing_runs)} production runs have no eligible "
            "active equipment. No records were inserted. "
            f"Sample run IDs: {missing_runs[:5]}"
        )

    print(f"Equipment assignments prepared: {len(records):,}")

    # Insert in batches.
    insert_query = text("""
        INSERT INTO run_equipment (
            run_equipment_id,
            run_id,
            equipment_id
        )
        VALUES (
            :run_equipment_id,
            :run_id,
            :equipment_id
        )
    """)

    batch_size = 1000

    with engine.begin() as connection:

        for start in range(0, len(records), batch_size):

            batch = records[start:start + batch_size]

            connection.execute(insert_query, batch)

            print(
                f"Inserted {min(start + batch_size, len(records)):,}"
                f" / {len(records):,} assignments"
            )

    print("\nRun-equipment generation completed successfully.")


def main():

    engine = get_engine()

    try:
        generate_run_equipment(engine)

    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
