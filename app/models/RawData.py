from sqlalchemy import Column, Integer, DateTime, ForeignKey, func, String
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from .Base import Base


class RawData(Base):
    __tablename__ = "raw_data"
    __table_args__ = {"schema": "raw_data"}

    id = Column(Integer, primary_key=True)
    run_id = Column(Integer, ForeignKey("raw_data.run.id"), nullable=False)
    data = Column(JSONB, nullable=False)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    run = relationship("Run", back_populates="raw_data")