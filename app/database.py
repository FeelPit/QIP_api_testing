from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Создаем engine с поддержкой SQLite и PostgreSQL
if settings.database_url.startswith("sqlite"):
    engine = create_engine(
        settings.database_url, 
        connect_args={"check_same_thread": False}
    )
else:
    # Используем исправленный URL для PostgreSQL
    engine = create_engine(settings.database_url_fixed)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 