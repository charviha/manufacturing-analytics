
import random
import uuid

from sqlalchemy import text

from database.connection import get_engine


random.seed(42)


DEFECT_TYPES = [
    "Dimensional Defect",
    "Surface Defect",
    "Assembly Defect",
    "Material Defect",
    "Functional Defect",
    "Packaging Defect",
    "Welding Defect",
    "Paint Defect"
]


def generate_quality_inspections():

    engine = get_engine()

    # Prevent duplicate generation.
    with engine.connect() as connection:

        existing_count = connection.execute(
            text("""
                SELECT COUNT(*)
                FROM quality_inspections
            """)
        ).scalar()

        expected_count = connection.execute(
            text("""
                SELECT COUNT(*)
                FROM production_runs
                WHERE run_status = 'Completed'
            """)
        ).scalar()

    if existing_count > 0:
        print(
            f"Quality inspections already exist: {existing_count}"
        )
        print("Skipping generation to avoid duplicates.")
        return

    if expected_count == 0:
        print("No completed production runs found.")
        return

    # Fetch completed production runs.
    fetch_query = text("""
        SELECT
            run_id,
            end_time,
            quantity_produced,
            scrap_quantity
        FROM production_runs
        WHERE run_status = 'Completed'
        ORDER BY end_time, run_id
    """)

    # Insert inspection records.
    insert_query = text("""
        INSERT INTO quality_inspections (
            inspection_id,
            run_id,
            inspection_date,
            inspected_quantity,
            passed_quantity,
            failed_quantity,
            defect_type,
            inspection_status
        )
        VALUES (
            :inspection_id,
            :run_id,
            :inspection_date,
            :inspected_quantity,
            :passed_quantity,
            :failed_quantity,
            :defect_type,
            :inspection_status
        )
    """)

    batch_size = 1000
    total_inserted = 0
    batch = []

    with engine.begin() as connection:

        result = connection.execute(fetch_query)

        for record in result.mappings():

            produced = int(record["quantity_produced"])
            failed = int(record["scrap_quantity"])

            # Every produced unit is accounted for.
            inspected = produced
            passed = inspected - failed

            # Assign a defect category only when failures exist.
            if failed > 0:
                defect_type = random.choice(DEFECT_TYPES)
                inspection_status = "Failed"
            else:
                defect_type = None
                inspection_status = "Passed"

            inspection = {
                "inspection_id": str(uuid.uuid4()),
                "run_id": record["run_id"],
                "inspection_date": record["end_time"],
                "inspected_quantity": inspected,
                "passed_quantity": passed,
                "failed_quantity": failed,
                "defect_type": defect_type,
                "inspection_status": inspection_status
            }

            batch.append(inspection)

            if len(batch) >= batch_size:

                connection.execute(
                    insert_query,
                    batch
                )

                total_inserted += len(batch)
                print(
                    f"Inserted {total_inserted} inspection records..."
                )

                batch.clear()

        # Insert the remaining records.
        if batch:

            connection.execute(
                insert_query,
                batch
            )

            total_inserted += len(batch)

    print("\nQuality inspection generation completed.")
    print(f"Expected records: {expected_count}")
    print(f"Inserted records: {total_inserted}")


if __name__ == "__main__":
    generate_quality_inspections()
