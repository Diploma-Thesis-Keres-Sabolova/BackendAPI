from fastapi import FastAPI
from api import weather, providers, runs
import os
from dotenv import load_dotenv


load_dotenv()
ENV = os.getenv("ENV", "development")

app = FastAPI(
    openapi_url="/openapi.json" if ENV != "production" else None,
    docs_url="/docs" if ENV != "production" else None,
    redoc_url="/redoc" if ENV != "production" else None,
)


app.include_router(providers.router, prefix="/providers", tags=["Providers"])
app.include_router(runs.router, prefix="/runs", tags=["Runs"])
app.include_router(weather.router, prefix="/weather", tags=["Weather"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
