from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


# User schemas
class UserBase(BaseModel):
    telegram_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class UserCreate(UserBase):
    pass


class User(UserBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Test schemas
class TestBase(BaseModel):
    name: str
    description: Optional[str] = None
    test_type: str = Field(..., pattern="^(frontend|backend)$")
    time_limit_per_question: int = 90


class TestCreate(TestBase):
    pass


class Test(TestBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# Question schemas
class QuestionBase(BaseModel):
    question_text: str
    question_type: str = Field(..., pattern="^(text|multiple_choice)$")
    options: Optional[List[str]] = None
    points: int = 1
    order: int


class QuestionCreate(QuestionBase):
    test_id: int


class Question(QuestionBase):
    id: int
    test_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# Answer schemas
class AnswerBase(BaseModel):
    answer_text: str
    time_spent: Optional[int] = None


class AnswerCreate(AnswerBase):
    question_id: int


class Answer(AnswerBase):
    id: int
    test_result_id: int
    question_id: int
    is_correct: Optional[bool] = None
    points_earned: float
    created_at: datetime
    
    class Config:
        from_attributes = True


# Test Result schemas
class TestResultBase(BaseModel):
    test_id: int


class TestResultCreate(TestResultBase):
    pass


class TestResult(TestResultBase):
    id: int
    user_id: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    total_score: float
    max_score: float
    percentage: float
    is_suspicious: bool
    suspicious_reasons: Optional[List[str]] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# Test submission schemas
class TestSubmission(BaseModel):
    test_id: int
    answers: List[AnswerCreate]
    total_time: Optional[int] = None


class TestSubmissionResponse(BaseModel):
    result_id: int
    total_score: float
    max_score: float
    percentage: float
    is_suspicious: bool
    message: str


# Export schemas
class ExportRequest(BaseModel):
    format: str = Field(..., pattern="^(json|markdown)$")
    test_id: Optional[int] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    include_suspicious: bool = True


class ExportResponse(BaseModel):
    data: Dict[str, Any]
    format: str
    filename: str


# Suspicious Activity schemas
class SuspiciousActivityBase(BaseModel):
    activity_type: str
    description: str
    confidence_score: float
    details: Optional[Dict[str, Any]] = None


class SuspiciousActivity(SuspiciousActivityBase):
    id: int
    test_result_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# API Response schemas
class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None


class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None 