from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Test, Question
from app.schemas import Test as TestSchema, Question as QuestionSchema
from app.services import TestService

router = APIRouter(prefix="/api/tests", tags=["tests"])


@router.get("/", response_model=List[TestSchema])
def get_tests(db: Session = Depends(get_db)):
    """Получить список активных тестов"""
    tests = TestService.get_active_tests(db)
    return tests


@router.get("/{test_id}", response_model=TestSchema)
def get_test(test_id: int, db: Session = Depends(get_db)):
    """Получить конкретный тест"""
    test = TestService.get_test_by_id(db, test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    return test


@router.get("/{test_id}/questions", response_model=List[QuestionSchema])
def get_test_questions(test_id: int, db: Session = Depends(get_db)):
    """Получить вопросы теста"""
    # Проверяем существование теста
    test = TestService.get_test_by_id(db, test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    
    questions = TestService.get_test_questions(db, test_id)
    return questions 