from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from datetime import datetime, timezone
from app.db.session import Base


class LogisticsRecord(Base):
    __tablename__ = "logistics_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, unique=True)
    status = Column(String(30), nullable=False, default="picked_up")
    # picked_up / in_transit / out_for_delivery / delivered
    tracking_info = Column(Text, nullable=True)  # JSON 格式的节点时间线
    estimated_delivery = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
