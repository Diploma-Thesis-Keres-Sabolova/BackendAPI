import pandas as pd
from datetime import date
from DataGathering.WeatherProvider import WeatherProvider

forecast_provider = WeatherProvider(
    name="OpenMeteo_Forecast",
    endpoint="https://api.open-meteo.com/v1/forecast",
    params={
        "latitude": 48.15,
        "longitude": 17.11,
        "minutely_15": "temperature_2m,rain,snowfall,wind_speed_10m,dew_point_2m,precipitation",
    }
)

# Historical provider (hodinové dáta)
historical_provider = WeatherProvider(
    name="OpenMeteo_History",
    endpoint="https://archive-api.open-meteo.com/v1/archive",
    params={
        "latitude": 48.15,
        "longitude": 17.11,
        "start_date": "2025-01-01",
        "end_date": "2025-10-12",
        "hourly": "temperature_2m,dew_point_2m,rain,snowfall,wind_speed_10m,precipitation",
    }
)

try:
    forecast_provider.run(date.today())
    historical_provider.run(date.today())
except Exception as e:
    print("Fetch failed:", e)
