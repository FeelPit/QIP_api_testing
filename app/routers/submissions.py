from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.schemas import TestSubmission, TestSubmissionResponse
from app.services import TestResultService, UserService

router = APIRouter(prefix="/api/submissions", tags=["submissions"])


@router.post("/{test_id}/submit", response_model=TestSubmissionResponse)
def submit_test(
    test_id: int,
    submission: TestSubmission,
    db: Session = Depends(get_db),
    x_telegram_user_id: Optional[int] = Header(None),
    x_telegram_username: Optional[str] = Header(None),
    x_telegram_first_name: Optional[str] = Header(None),
    x_telegram_last_name: Optional[str] = Header(None)
):
    """Отправить ответы на тест"""
    
    # Проверяем, что test_id в URL совпадает с test_id в данных
    if submission.test_id != test_id:
        raise HTTPException(status_code=400, detail="Test ID mismatch")
    
    # Получаем или создаем пользователя
    if not x_telegram_user_id:
        raise HTTPException(status_code=400, detail="Telegram user ID required")
    
    user = UserService.get_or_create_user(
        db=db,
        telegram_id=x_telegram_user_id,
        username=x_telegram_username,
        first_name=x_telegram_first_name,
        last_name=x_telegram_last_name
    )
    
    try:
        # Отправляем тест
        result = TestResultService.submit_test(db, submission, user.id)
        
        return TestSubmissionResponse(
            result_id=result.id,
            total_score=result.total_score,
            max_score=result.max_score,
            percentage=result.percentage,
            is_suspicious=result.is_suspicious,
            message="Тест успешно завершен! Результаты отправлены команде QIP."
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error") 