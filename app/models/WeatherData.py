from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, func, String
from sqlalchemy.orm import relationship
from .Base import Base


class WeatherData(Base):
    __tablename__ = "weather_data"
    __table_args__ = {"schema": "raw_data"}

    id = Column(Integer, primary_key=True)
    run_id = Column(Integer, ForeignKey("raw_data.run.id"), nullable=False)
    timestamp = Column(DateTime, nullable=False)

    temperature = Column(Float, nullable=True)
    dew_point = Column(Float, nullable=True)
    precipitation = Column(Float, nullable=True)
    rain = Column(Float, nullable=True)
    snowfall = Column(Float, nullable=True)
    wind_speed = Column(Float, nullable=True)
    global_tilted_irradiance = Column(Float, nullable=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    run = relationship("Run", back_populates="weather_data")
