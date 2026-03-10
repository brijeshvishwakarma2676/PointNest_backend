from sqlalchemy import Column, Integer, ForeignKey
from app.config.database import Base


class Purchase(Base):
    __tablename__ = "purchases"

    id = Column(Integer, primary_key=True)
    shop_id = Column(Integer, ForeignKey("users.id"))
    customer_id = Column(Integer, ForeignKey("customers.id"))
    amount = Column(Integer)
    points_earned = Column(Integer)