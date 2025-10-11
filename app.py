import pandas as pd
from datetime import date
from DataGathering.WeatherProvider import WeatherProvider

provider = WeatherProvider(
    name="test_provider",
    latitude=48.15,   # Bratislava
    longitude=17.11
)

target_date = date.today()

try:
    provider.run(target_date)
except Exception as e:
    print("Fetch failed:", e)
