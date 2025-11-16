import pandas as pd
from datetime import date
from Provider import Provider

def main():

    forecast_provider = Provider(
        name="OpenMeteo_Forecast",
        endpoint="https://api.open-meteo.com/v1/forecast",
        target_date=date.today(),
        params={
            "latitude": 48.15,
            "longitude": 17.11,
            "minutely_15": "temperature_2m,rain,snowfall,wind_speed_10m,dew_point_2m,precipitation",
        },
        timestamp_pth = "minutely_15.time",
        data_pth = "minutely_15",
        units_pth = "minutely_15_units"
    )

    historical_provider = Provider(
        name="OpenMeteo_History",
        endpoint="https://archive-api.open-meteo.com/v1/archive",
        target_date=date.today(),
        params={
            "latitude": 48.15,
            "longitude": 17.11,
            "start_date": date.today().strftime("%Y-%m-%d"),
            "end_date": date.today().strftime("%Y-%m-%d"),
            "hourly": "temperature_2m,dew_point_2m,rain,snowfall,wind_speed_10m,precipitation",
        },
        timestamp_pth="hourly.time",
        data_pth="hourly",
        units_pth="hourly_units"
    )

    okte_provider = Provider(
        name="OKTE_DAM",
        endpoint="https://isot.okte.sk/api/v1/dam/results",
        target_date=date.today(),
        params={
            "deliveryDayFrom": date.today().strftime("%Y-%m-%d"),
            "deliveryDayTo": date.today().strftime("%Y-%m-%d")
        },
        timestamp_pth="deliveryStart",
        data_pth="",
        units_pth=None
    )

    try:
        forecast_provider.run()
        historical_provider.run()
        okte_provider.run()
    except Exception as e:
        print("Fetch failed:", e)

if __name__ == "__main__":
    main()