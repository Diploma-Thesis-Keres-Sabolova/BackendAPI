from sqlalchemy import Column, Integer, ForeignKey, Date, String, DateTime, func, Text
from sqlalchemy.orm import relationship
from .Base import Base


class Run(Base):
    __tablename__ = "run"
    __table_args__ = {"schema": "core"}

    id = Column(Integer, primary_key=True)
    provider_id = Column(Integer, ForeignKey("core.provider.id"), nullable=False)
    run_timestamp = Column(DateTime, server_default=func.now(), nullable=False)
    params = Column(Text, nullable=True)
    data_type = Column(String, nullable=False)
    target_date = Column(Date, nullable=False)
    status = Column(String, nullable=False)
    message = Column(String, nullable=False)

    provider = relationship("Provider", back_populates="runs")
    proc_data = relationship("ProcessedData", back_populates="run", cascade="all, delete-orphan")
    raw_data = relationship("RawData", back_populates="run", cascade="all, delete-orphan")
