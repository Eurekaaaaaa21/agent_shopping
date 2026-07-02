from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from app.db.session import Base


class Address(Base):
    __tablename__ = "addresses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    receiver_name = Column(String(50), nullable=False, comment="收货人姓名")
    phone = Column(String(20), nullable=False, comment="收货人电话")
    province = Column(String(50), nullable=False, comment="省份")
    city = Column(String(50), nullable=False, comment="城市")
    district = Column(String(50), nullable=False, comment="区县")
    detail = Column(String(200), nullable=False, comment="详细地址")
    is_default = Column(Boolean, default=False, comment="是否默认地址")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")

    user = relationship("User", back_populates="addresses")
