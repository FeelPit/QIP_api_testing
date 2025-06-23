#!/usr/bin/env python3
"""
Скрипт для инициализации базы данных
Создает все таблицы и добавляет базовые данные
"""

import sys
import os

# Добавляем корневую директорию в путь
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine, SessionLocal
from app.models import Base, Test, Question, User
from app.config import settings

def init_database():
    """Инициализация базы данных"""
    print("Создание таблиц...")
    
    # Создаем все таблицы
    Base.metadata.create_all(bind=engine)
    print("✅ Все таблицы созданы успешно")
    
    # Создаем сессию для добавления данных
    db = SessionLocal()
    
    try:
        # Проверяем, есть ли уже тесты
        existing_tests = db.query(Test).count()
        if existing_tests > 0:
            print("ℹ️  Тесты уже существуют, пропускаем создание базовых данных")
            return
        
        print("Добавление базовых тестов...")
        
        # Создаем тест для Frontend
        frontend_test = Test(
            name="Frontend Developer Test",
            description="Тест для проверки знаний в области фронтенд разработки",
            test_type="frontend",
            is_active=True,
            time_limit_per_question=90
        )
        db.add(frontend_test)
        db.flush()  # Получаем ID
        
        # Вопросы для Frontend теста
        frontend_questions = [
            Question(
                test_id=frontend_test.id,
                question_text="Что такое React и каковы его основные преимущества?",
                question_type="text",
                correct_answer="React - это JavaScript библиотека для создания пользовательских интерфейсов. Основные преимущества: компонентный подход, виртуальный DOM, однонаправленный поток данных, большое сообщество.",
                points=10,
                order=1
            ),
            Question(
                test_id=frontend_test.id,
                question_text="Объясните разницу между let, const и var в JavaScript",
                question_type="text",
                correct_answer="var - функциональная область видимости, можно переопределять; let - блочная область видимости, можно изменять значение; const - блочная область видимости, нельзя изменять значение после инициализации.",
                points=8,
                order=2
            ),
            Question(
                test_id=frontend_test.id,
                question_text="Что такое CSS Grid и как он отличается от Flexbox?",
                question_type="text",
                correct_answer="CSS Grid - двумерная система макета, создает сетку из строк и столбцов. Flexbox - одномерная система, работает с одной осью. Grid лучше для сложных макетов, Flexbox для простых выравниваний.",
                points=7,
                order=3
            )
        ]
        
        for question in frontend_questions:
            db.add(question)
        
        # Создаем тест для Backend
        backend_test = Test(
            name="Backend Developer Test",
            description="Тест для проверки знаний в области бэкенд разработки",
            test_type="backend",
            is_active=True,
            time_limit_per_question=90
        )
        db.add(backend_test)
        db.flush()
        
        # Вопросы для Backend теста
        backend_questions = [
            Question(
                test_id=backend_test.id,
                question_text="Объясните принципы REST API",
                question_type="text",
                correct_answer="REST - архитектурный стиль для веб-сервисов. Принципы: безсостояние, единообразие интерфейса, кэширование, многоуровневая система, код по требованию.",
                points=10,
                order=1
            ),
            Question(
                test_id=backend_test.id,
                question_text="Что такое SQL инъекции и как их предотвратить?",
                question_type="text",
                correct_answer="SQL инъекции - атаки через внедрение вредоносного SQL кода. Предотвращение: использование параметризованных запросов, валидация входных данных, принцип наименьших привилегий.",
                points=9,
                order=2
            ),
            Question(
                test_id=backend_test.id,
                question_text="Объясните разницу между синхронным и асинхронным программированием",
                question_type="text",
                correct_answer="Синхронное - операции выполняются последовательно, блокируя выполнение. Асинхронное - операции выполняются параллельно, не блокируя основной поток.",
                points=8,
                order=3
            )
        ]
        
        for question in backend_questions:
            db.add(question)
        
        # Создаем тестового пользователя
        test_user = User(
            telegram_id=123456789,
            username="test_user",
            first_name="Test",
            last_name="User"
        )
        db.add(test_user)
        
        # Сохраняем все изменения
        db.commit()
        print("✅ Базовые данные добавлены успешно")
        
    except Exception as e:
        print(f"❌ Ошибка при добавлении данных: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def main():
    """Основная функция"""
    print("🚀 Инициализация базы данных Quantum Insight API")
    print(f"📊 База данных: {settings.database_url}")
    
    try:
        init_database()
        print("\n🎉 Инициализация завершена успешно!")
        print("\n📋 Созданные таблицы:")
        print("   - users (пользователи)")
        print("   - tests (тесты)")
        print("   - questions (вопросы)")
        print("   - test_results (результаты тестов)")
        print("   - answers (ответы)")
        print("   - suspicious_activities (подозрительная активность)")
        print("   - aeon_sessions (сессии ÆON интервью)")
        print("   - aeon_questions (вопросы ÆON интервью)")
        print("   - aeon_answers (ответы ÆON интервью)")
        print("   - aeon_reports (отчеты ÆON интервью)")
        
    except Exception as e:
        print(f"\n❌ Ошибка инициализации: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 