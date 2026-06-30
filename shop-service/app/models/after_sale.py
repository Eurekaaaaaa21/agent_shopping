from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from app.db.session import Base


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
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
