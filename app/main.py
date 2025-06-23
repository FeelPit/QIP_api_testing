from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from app.config import settings
from app.database import engine
from app.models import Base
from app.routers import tests, submissions, results, aeon_interview


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Создаем таблицы при запуске
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Quantum Insight Telegram Test API",
    description="API для мини-приложения Telegram тестирования стажёров",
    version="1.0.0",
    lifespan=lifespan
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роутеры
app.include_router(tests.router)
app.include_router(submissions.router)
app.include_router(results.router)
app.include_router(aeon_interview.router)


@app.get("/")
async def root():
    """Корневой эндпоинт"""
    return {
        "message": "Quantum Insight Telegram Test API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Проверка здоровья API"""
    return {"status": "healthy"}


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Обработчик HTTP исключений"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "error_code": exc.status_code}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Обработчик общих исключений"""
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error_code": "INTERNAL_ERROR"}
    ) 