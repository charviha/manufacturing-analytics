
import uuid

from sqlalchemy import text

from database.connection import get_engine


def generate_equipment_run_metrics():
    engine = get_engine()

    # Check whether metrics have already been generated.
    with engine.connect() as connection:
        existing_count = connection.execute(
            text("SELECT COUNT(*) FROM equipment_run_metrics")
        ).scalar()

        if existing_count > 0:
            print(
                f"Metrics already exist: {existing_count} records."
            )
            print("Skipping generation to avoid duplicates.")
            return

        expected_count = connection.execute(
            text("SELECT COUNT(*) FROM run_equipment")
        ).scalar()

    if expected_count == 0:
        print("No run-equipment assignments found.")
        return

    # Retrieve production metrics for each equipment assignment.
    fetch_query = text("""
        SELECT
            re.run_equipment_id,
            pr.planned_production_minutes,
            pr.ideal_cycle_time_seconds,
            pr.quantity_produced,
            pr.scrap_quantity
        FROM run_equipment re
        JOIN production_runs pr
            ON re.run_id = pr.run_id
        ORDER BY re.run_equipment_id
    """)

    insert_query = text("""
        INSERT INTO equipment_run_metrics (
            equipment_metric_id,
            run_equipment_id,
            planned_production_minutes,
            ideal_cycle_time_seconds,
            quantity_produced,
            scrap_quantity
        )
        VALUES (
            :equipment_metric_id,
            :run_equipment_id,
            :planned_production_minutes,
            :ideal_cycle_time_seconds,
            :quantity_produced,
            :scrap_quantity
        )
    """)

    batch_size = 1000
    total_inserted = 0
    batch = []

    with engine.begin() as connection:
        result = connection.execute(fetch_query)
        
        for record in result.mappings():
            metric = {
                "equipment_metric_id": str(uuid.uuid4()),
                "run_equipment_id": record["run_equipment_id"],
                "planned_production_minutes":
                    record["planned_production_minutes"],
                "ideal_cycle_time_seconds":
                    record["ideal_cycle_time_seconds"],
                "quantity_produced": record["quantity_produced"],
                "scrap_quantity": record["scrap_quantity"]
            }

            batch.append(metric)

            if len(batch) >= batch_size:
                connection.execute(insert_query, batch)
                total_inserted += len(batch)
                print(f"Inserted {total_inserted} records...")
                batch.clear()

        # Insert remaining records.
        if batch:
            connection.execute(insert_query, batch)
            total_inserted += len(batch)

    print("\nEquipment metrics generation completed.")
    print(f"Expected records: {expected_count}")
    print(f"Inserted records: {total_inserted}")


if __name__ == "__main__":
    generate_equipment_run_metrics()
