
import uuid
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
from sqlalchemy import (
    Column,
    String,
    Integer,
    BigInteger,
    Boolean,
    Date,
    DateTime,
    DECIMAL,
    Text,
    ForeignKey,
    UniqueConstraint,
    CheckConstraint,
    Index,
    text
)
from sqlalchemy.orm import declarative_base

from database.connection import get_engine

Base = declarative_base()


def generate_uuid():
    return str(uuid.uuid4())


# =====================================================
# 1. PRODUCTION LINES
# =====================================================

class ProductionLine(Base):
    __tablename__ = "production_lines"

    line_id = Column(String(36), primary_key=True, default=generate_uuid)
    line_name = Column(String(100), nullable=False)
    location = Column(String(150))
    line_capacity_per_hour = Column(Integer)
    is_active = Column(Boolean, server_default=text("1"))
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))


# =====================================================
# 2. EQUIPMENT
# =====================================================

class Equipment(Base):
    __tablename__ = "equipment"

    equipment_id = Column(String(36), primary_key=True, default=generate_uuid)
    equipment_name = Column(String(150), nullable=False)
    equipment_type = Column(String(100))
    manufacturer = Column(String(100))
    installation_date = Column(Date)
    equipment_status = Column(String(30), server_default=text("'Active'"))
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))


# =====================================================
# 3. PRODUCTS
# =====================================================

class Product(Base):
    __tablename__ = "products"

    product_id = Column(String(36), primary_key=True, default=generate_uuid)
    product_name = Column(String(150), nullable=False)
    category = Column(String(100))
    unit_of_measure = Column(String(30), server_default=text("'Pieces'"))
    standard_price = Column(DECIMAL(12, 2))
    is_active = Column(Boolean, server_default=text("1"))
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))


# =====================================================
# 4. CUSTOMERS
# =====================================================

class Customer(Base):
    __tablename__ = "customers"

    customer_id = Column(String(36), primary_key=True, default=generate_uuid)
    customer_name = Column(String(150), nullable=False)
    location = Column(String(150))
    industry = Column(String(100))
    customer_type = Column(String(50))
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))


# =====================================================
# 5. CALENDAR
# =====================================================

class Calendar(Base):
    __tablename__ = "calendar"

    calendar_date = Column(Date, primary_key=True)
    day_number = Column(Integer)
    day_name = Column(String(20))
    week_number = Column(Integer)
    month_number = Column(Integer)
    month_name = Column(String(20))
    quarter_number = Column(Integer)
    year_number = Column(Integer)
    season = Column(String(30))
    is_weekend = Column(Boolean, server_default=text("0"))
    is_holiday = Column(Boolean, server_default=text("0"))


# =====================================================
# 6. LINE EQUIPMENT
# =====================================================

class LineEquipment(Base):
    __tablename__ = "line_equipment"

    line_equipment_id = Column(String(36), primary_key=True, default=generate_uuid)
    line_id = Column(String(36), ForeignKey("production_lines.line_id"), nullable=False)
    equipment_id = Column(String(36), ForeignKey("equipment.equipment_id"), nullable=False)
    assigned_from = Column(Date, nullable=False)
    assigned_to = Column(Date)

    __table_args__ = (
        UniqueConstraint(
            "line_id", "equipment_id", "assigned_from",
            name="uq_line_equipment_assignment"
        ),
    )


# =====================================================
# 7. CUSTOMER ORDERS
# =====================================================

class Order(Base):
    __tablename__ = "orders"

    order_id = Column(String(36), primary_key=True, default=generate_uuid)
    customer_id = Column(String(36), ForeignKey("customers.customer_id"), nullable=False)
    product_id = Column(String(36), ForeignKey("products.product_id"), nullable=False)

    order_date = Column(Date, nullable=False)
    requested_delivery_date = Column(Date)
    quantity_ordered = Column(BigInteger, nullable=False)
    order_status = Column(String(30), server_default=text("'Pending'"))
    unit_price = Column(DECIMAL(12, 2))

    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))

    __table_args__ = (
        CheckConstraint("quantity_ordered > 0", name="chk_order_quantity"),
        Index("idx_orders_customer", "customer_id"),
        Index("idx_orders_product", "product_id"),
        Index("idx_orders_date", "order_date"),
    )


# =====================================================
# 8. PRODUCTION RUNS
# =====================================================

class ProductionRun(Base):
    __tablename__ = "production_runs"

    run_id = Column(String(36), primary_key=True, default=generate_uuid)
    order_id = Column(String(36), ForeignKey("orders.order_id"), nullable=False)
    line_id = Column(String(36), ForeignKey("production_lines.line_id"), nullable=False)

    run_date = Column(Date, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)

    quantity_produced = Column(BigInteger, server_default=text("0"))
    scrap_quantity = Column(BigInteger, server_default=text("0"))

    planned_production_minutes = Column(DECIMAL(12, 2))
    ideal_cycle_time_seconds = Column(DECIMAL(12, 4))

    run_status = Column(String(30), server_default=text("'Completed'"))
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))

    __table_args__ = (
        CheckConstraint("quantity_produced >= 0", name="chk_run_quantity"),
        CheckConstraint("scrap_quantity >= 0", name="chk_run_scrap"),
        CheckConstraint(
            "scrap_quantity <= quantity_produced",
            name="chk_run_scrap_limit"
        ),
        Index("idx_runs_order", "order_id"),
        Index("idx_runs_line", "line_id"),
        Index("idx_runs_date", "run_date"),
    )


# =====================================================
# 9. RUN EQUIPMENT
# =====================================================

class RunEquipment(Base):
    __tablename__ = "run_equipment"

    run_equipment_id = Column(String(36), primary_key=True, default=generate_uuid)
    run_id = Column(String(36), ForeignKey("production_runs.run_id"), nullable=False)
    equipment_id = Column(String(36), ForeignKey("equipment.equipment_id"), nullable=False)

    __table_args__ = (
        UniqueConstraint("run_id", "equipment_id", name="uq_run_equipment"),
    )


# =====================================================
# 10. DOWNTIME EVENTS
# =====================================================

class DowntimeEvent(Base):
    __tablename__ = "downtime_events"

    downtime_id = Column(String(36), primary_key=True, default=generate_uuid)
    equipment_id = Column(String(36), ForeignKey("equipment.equipment_id"), nullable=False)
    run_id = Column(String(36), ForeignKey("production_runs.run_id"))

    downtime_start = Column(DateTime, nullable=False)
    downtime_end = Column(DateTime)

    downtime_type = Column(String(50))
    downtime_reason = Column(String(255))
    is_planned = Column(Boolean, server_default=text("0"))

    __table_args__ = (
        Index("idx_downtime_equipment", "equipment_id"),
        Index("idx_downtime_run", "run_id"),
        Index("idx_downtime_start", "downtime_start"),
    )


# =====================================================
# 11. QUALITY INSPECTIONS
# =====================================================

class QualityInspection(Base):
    __tablename__ = "quality_inspections"

    inspection_id = Column(String(36), primary_key=True, default=generate_uuid)
    run_id = Column(String(36), ForeignKey("production_runs.run_id"), nullable=False)

    inspection_date = Column(DateTime, nullable=False)
    inspected_quantity = Column(BigInteger, nullable=False)
    passed_quantity = Column(BigInteger, nullable=False)
    failed_quantity = Column(BigInteger, nullable=False)

    defect_type = Column(String(100))
    inspection_status = Column(String(30))

    __table_args__ = (
        CheckConstraint("inspected_quantity >= 0", name="chk_inspected_qty"),
        CheckConstraint("passed_quantity >= 0", name="chk_passed_qty"),
        CheckConstraint("failed_quantity >= 0", name="chk_failed_qty"),
        CheckConstraint(
            "passed_quantity + failed_quantity = inspected_quantity",
            name="chk_quality_total"
        ),
        Index("idx_quality_run", "run_id"),
        Index("idx_quality_date", "inspection_date"),
    )


# =====================================================
# 12. CUSTOMER FEEDBACK
# =====================================================

class CustomerFeedback(Base):
    __tablename__ = "customer_feedback"

    feedback_id = Column(String(36), primary_key=True, default=generate_uuid)
    customer_id = Column(String(36), ForeignKey("customers.customer_id"), nullable=False)
    order_id = Column(String(36), ForeignKey("orders.order_id"))

    feedback_date = Column(Date, nullable=False)
    rating = Column(Integer, nullable=False)
    feedback_text = Column(Text)
    is_positive = Column(Boolean)

    __table_args__ = (
        CheckConstraint("rating BETWEEN 1 AND 5", name="chk_feedback_rating"),
        Index("idx_feedback_customer", "customer_id"),
        Index("idx_feedback_date", "feedback_date"),
    )


# =====================================================
# 13. STAFFING
# =====================================================

class Staffing(Base):
    __tablename__ = "staffing"

    staffing_id = Column(String(36), primary_key=True, default=generate_uuid)
    line_id = Column(String(36), ForeignKey("production_lines.line_id"), nullable=False)

    shift_date = Column(Date, nullable=False)
    shift_name = Column(String(30))
    planned_workers = Column(Integer)
    actual_workers = Column(Integer)
    overtime_hours = Column(DECIMAL(8, 2), server_default=text("0"))

    __table_args__ = (
        CheckConstraint("planned_workers >= 0", name="chk_planned_workers"),
        CheckConstraint("actual_workers >= 0", name="chk_actual_workers"),
        Index("idx_staffing_line_date", "line_id", "shift_date"),
    )


# =====================================================
# 14. SUPPLY CHAIN EVENTS
# =====================================================

class SupplyChainEvent(Base):
    __tablename__ = "supply_chain_events"

    event_id = Column(String(36), primary_key=True, default=generate_uuid)

    product_id = Column(String(36), ForeignKey("products.product_id"))
    line_id = Column(String(36), ForeignKey("production_lines.line_id"))

    event_start = Column(Date, nullable=False)
    event_end = Column(Date)

    event_type = Column(String(100))
    event_description = Column(Text)

    shortage_quantity = Column(BigInteger, server_default=text("0"))
    severity = Column(String(30))

    __table_args__ = (
        Index("idx_supply_event_date", "event_start"),
    )


# =====================================================
# 15. EQUIPMENT RUN METRICS
# =====================================================

class EquipmentRunMetric(Base):
    __tablename__ = "equipment_run_metrics"

    equipment_metric_id = Column(String(36), primary_key=True, default=generate_uuid)

    run_equipment_id = Column(
        String(36),
        ForeignKey("run_equipment.run_equipment_id"),
        nullable=False,
        unique=True
    )

    planned_production_minutes = Column(DECIMAL(12, 2), nullable=False)
    ideal_cycle_time_seconds = Column(DECIMAL(12, 4), nullable=False)

    quantity_produced = Column(BigInteger, server_default=text("0"))
    scrap_quantity = Column(BigInteger, server_default=text("0"))

    __table_args__ = (
        CheckConstraint(
            "planned_production_minutes >= 0",
            name="chk_equipment_planned_minutes"
        ),
        CheckConstraint(
            "ideal_cycle_time_seconds > 0",
            name="chk_equipment_ideal_cycle"
        ),
        CheckConstraint("quantity_produced >= 0", name="chk_equipment_quantity"),
        CheckConstraint("scrap_quantity >= 0", name="chk_equipment_scrap"),
        CheckConstraint(
            "scrap_quantity <= quantity_produced",
            name="chk_equipment_scrap_limit"
        ),
    )


# =====================================================
# DATABASE TABLE CREATION
# =====================================================

def create_tables():
    engine = get_engine()

    try:
        Base.metadata.create_all(engine)

        print("\nAll database tables created successfully!")

        print("\nTables created:")

        for table_name in Base.metadata.tables:
            print(f"- {table_name}")

        print(f"\nTotal tables: {len(Base.metadata.tables)}")

    finally:
        engine.dispose()


if __name__ == "__main__":
    create_tables()
