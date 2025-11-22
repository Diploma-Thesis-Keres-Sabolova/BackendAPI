from sqlalchemy import Column, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from .Base import Base

class Provider(Base):
    __tablename__ = "provider"
    __table_args__ = (
        UniqueConstraint("name", "endpoint", name="uq_provider_unique"),
        {"schema": "raw_data"}
    )

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    endpoint = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    runs = relationship("Run", back_populates="provider")
