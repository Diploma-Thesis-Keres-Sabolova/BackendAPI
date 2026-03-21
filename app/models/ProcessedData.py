from sqlalchemy import Column, Integer, DateTime, ForeignKey, func, String, Index
from sqlalchemy.orm import relationship
from .Base import Base


class ProcessedData(Base):
    __tablename__ = "processed_data"
    __table_args__ = (
        Index('idx_processed_data_run_id', 'run_id'),
        {"schema": "processed_data"}
    )

    id = Column(Integer, primary_key=True)
    run_id = Column(Integer, ForeignKey("core.run.id"), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    name = Column(String, nullable=False)
    value = Column(String, nullable=True)
    unit = Column(String, nullable=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    run = relationship("Run", back_populates="proc_data")
