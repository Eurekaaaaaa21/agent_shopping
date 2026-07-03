from sqlalchemy import Column, Integer, String, Numeric, Text, DateTime, ForeignKey
from app.db.session import Base
from datetime import datetime, timezone


def utc_now_naive():
    return datetime.now(timezone.utc).replace(tzinfo=None)



class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Numeric(10, 2), nullable=False)
    image_url = Column(String(500), nullable=True)
    stock = Column(Integer, nullable=False, default=0)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    status = Column(String(20), nullable=False, default="on_sale")  # on_sale / off_sale
    created_at = Column(DateTime, default=utc_now_naive)
    updated_at = Column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)
