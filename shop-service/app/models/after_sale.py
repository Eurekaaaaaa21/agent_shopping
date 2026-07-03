from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from datetime import datetime, timezone
from app.db.session import Base


def utc_now_naive():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class AfterSaleRequest(Base):
    __tablename__ = "after_sale_requests"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    type = Column(String(20), nullable=False)  # refund / return / exchange
    reason = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="pending")
    # pending / approved / rejected / completed
    admin_note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now_naive)
    updated_at = Column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)
