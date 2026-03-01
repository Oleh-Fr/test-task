from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base


class Lot(Base):
    __tablename__ = "lots"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    start_price = Column(Float, nullable=False)
    current_price = Column(Float, nullable=False)
    status = Column(String, default="running")
    end_time = Column(DateTime)

    bids = relationship("Bid", back_populates="lot")


class Bid(Base):
    __tablename__ = "bids"

    id = Column(Integer, primary_key=True)
    lot_id = Column(Integer, ForeignKey("lots.id"))
    bidder = Column(String)
    amount = Column(Float)
    created_at = Column(DateTime, default=datetime.now)

    lot = relationship("Lot", back_populates="bids")
