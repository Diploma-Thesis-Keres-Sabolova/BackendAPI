from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship
from .Base import Base

class Provider(Base):
    __tablename__ = "provider"
    __table_args__ = {"schema": "raw_data"}

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    endpoint = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    params = Column(Text, nullable=True)

    runs = relationship("Run", back_populates="provider")
