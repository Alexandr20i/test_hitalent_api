from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.config import logger, settings
from app.exceptions import ConflictError, NotFoundError, ValidationError
from app.routers import departments_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Запуск приложения | env=%s", settings.app_env)
    yield
    logger.info("Остановка приложения")


app = FastAPI(
    title="HiTalent Org API",
    description="API организационной структуры — подразделения и сотрудники",
    version="1.0.0",
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# Обработчики исключений
# ---------------------------------------------------------------------------

@app.exception_handler(NotFoundError)
async def not_found_handler(request: Request, exc: NotFoundError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": str(exc)},
    )


@app.exception_handler(ConflictError)
async def conflict_handler(request: Request, exc: ConflictError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": exc.message},
    )


@app.exception_handler(ValidationError)
async def validation_handler(request: Request, exc: ValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.message},
    )


# ---------------------------------------------------------------------------
# Роутеры
# ---------------------------------------------------------------------------

app.include_router(departments_router)


# ---------------------------------------------------------------------------
# Healthcheck
# ---------------------------------------------------------------------------

@app.get("/health", tags=["system"], summary="Healthcheck")
async def health() -> dict:
    return {"status": "ok", "env": settings.app_env}