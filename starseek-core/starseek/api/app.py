from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from starseek.api.routes import charts, geocode, health, synastry
from starseek.services.geocoding import GeocodingError


def create_app() -> FastAPI:
    app = FastAPI(
        title="StarSeek",
        description="Astrological birth chart generator API. "
                    "Generate natal charts, look up cities, and manage saved charts.",
        version="0.2.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(GeocodingError)
    async def geocoding_error_handler(request: Request, exc: GeocodingError):
        return JSONResponse(
            status_code=502,
            content={"detail": f"Geocoding service error: {exc}"},
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        return JSONResponse(
            status_code=400,
            content={"detail": str(exc)},
        )

    app.include_router(charts.router)
    app.include_router(synastry.router)
    app.include_router(geocode.router)
    app.include_router(health.router)

    return app


app = create_app()
