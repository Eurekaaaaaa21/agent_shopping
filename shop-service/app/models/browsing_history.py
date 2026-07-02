from sqlalchemy import Column, Integer, ForeignKey, DateTime, UniqueConstraint, func
from sqlalchemy.orm import relationship
from app.db.session import Base


class BrowsingHistory(Base):
    __tablename__ = "browsing_history"
    __table_args__ = (
        UniqueConstraint("user_id", "product_id", name="uq_user_product"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    viewed_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="最近浏览时间")

    user = relationship("User", back_populates="browsing_history")
    product = relationship("Product")
