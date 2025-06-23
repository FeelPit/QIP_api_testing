#!/usr/bin/env python3
"""
Скрипт для обновления таблицы aeon_sessions с новыми полями
"""

import sys
import os

# Добавляем корневую директорию в путь
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.database import SessionLocal, engine

def update_aeon_sessions_table():
    """Добавить новые поля в таблицу aeon_sessions"""
    print("🔄 Обновление таблицы aeon_sessions...")
    
    db = SessionLocal()
    try:
        # Для SQLite используем pragma table_info
        result = db.execute(text("PRAGMA table_info(aeon_sessions)"))
        existing_columns = [row[1] for row in result.fetchall()]
        
        if 'candidate_name' not in existing_columns:
            print("➕ Добавление поля candidate_name...")
            db.execute(text("ALTER TABLE aeon_sessions ADD COLUMN candidate_name VARCHAR(255)"))
            print("✅ Поле candidate_name добавлено")
        else:
            print("ℹ️ Поле candidate_name уже существует")
        
        if 'candidate_email' not in existing_columns:
            print("➕ Добавление поля candidate_email...")
            db.execute(text("ALTER TABLE aeon_sessions ADD COLUMN candidate_email VARCHAR(255)"))
            print("✅ Поле candidate_email добавлено")
        else:
            print("ℹ️ Поле candidate_email уже существует")
        
        db.commit()
        print("🎉 Обновление таблицы завершено успешно!")
        
    except Exception as e:
        print(f"❌ Ошибка при обновлении таблицы: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def main():
    """Основная функция"""
    print("🚀 Обновление базы данных для ÆON Interview System")
    print("=" * 50)
    
    try:
        update_aeon_sessions_table()
        print("\n✅ Все обновления применены успешно!")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 