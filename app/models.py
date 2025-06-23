from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True, nullable=False)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    results = relationship("TestResult", back_populates="user")
    aeon_sessions = relationship("AeonSession", back_populates="user")


class Test(Base):
    __tablename__ = "tests"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    test_type = Column(String(50), nullable=False)  # 'frontend' or 'backend'
    is_active = Column(Boolean, default=True)
    time_limit_per_question = Column(Integer, default=90)  # seconds
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    questions = relationship("Question", back_populates="test")
    results = relationship("TestResult", back_populates="test")


class Question(Base):
    __tablename__ = "questions"
    
    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(Integer, ForeignKey("tests.id"), nullable=False)
    question_text = Column(Text, nullable=False)
    question_type = Column(String(50), nullable=False)  # 'text', 'multiple_choice'
    options = Column(JSON, nullable=True)  # для множественного выбора
    correct_answer = Column(Text, nullable=True)
    points = Column(Integer, default=1)
    order = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    test = relationship("Test", back_populates="questions")
    answers = relationship("Answer", back_populates="question")


class TestResult(Base):
    __tablename__ = "test_results"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    test_id = Column(Integer, ForeignKey("tests.id"), nullable=False)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    total_score = Column(Float, default=0.0)
    max_score = Column(Float, default=0.0)
    percentage = Column(Float, default=0.0)
    is_suspicious = Column(Boolean, default=False)
    suspicious_reasons = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="results")
    test = relationship("Test", back_populates="results")
    answers = relationship("Answer", back_populates="test_result")


class Answer(Base):
    __tablename__ = "answers"
    
    id = Column(Integer, primary_key=True, index=True)
    test_result_id = Column(Integer, ForeignKey("test_results.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    answer_text = Column(Text, nullable=False)
    is_correct = Column(Boolean, nullable=True)
    points_earned = Column(Float, default=0.0)
    time_spent = Column(Integer, nullable=True)  # seconds
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    test_result = relationship("TestResult", back_populates="answers")
    question = relationship("Question", back_populates="answers")


class SuspiciousActivity(Base):
    __tablename__ = "suspicious_activities"
    
    id = Column(Integer, primary_key=True, index=True)
    test_result_id = Column(Integer, ForeignKey("test_results.id"), nullable=False)
    activity_type = Column(String(100), nullable=False)  # 'copy_paste', 'too_fast', 'identical_answers'
    description = Column(Text, nullable=False)
    confidence_score = Column(Float, default=0.0)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ÆON Interview Models
class AeonSession(Base):
    __tablename__ = "aeon_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    current_question = Column(Integer, default=0)
    total_questions = Column(Integer, default=5)
    status = Column(String(50), default="active")  # 'active', 'completed', 'abandoned'
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="aeon_sessions")
    questions = relationship("AeonQuestion", back_populates="session")
    report = relationship("AeonReport", back_populates="session", uselist=False)


class AeonQuestion(Base):
    __tablename__ = "aeon_questions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("aeon_sessions.id"), nullable=False)
    question_number = Column(Integer, nullable=False)
    question_text = Column(Text, nullable=False)
    question_type = Column(String(50), nullable=False)  # 'personality', 'thinking', 'potential', 'behavior', 'integration'
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    session = relationship("AeonSession", back_populates="questions")
    answer = relationship("AeonAnswer", back_populates="question", uselist=False)


class AeonAnswer(Base):
    __tablename__ = "aeon_answers"
    
    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("aeon_questions.id"), nullable=False)
    answer_text = Column(Text, nullable=False)
    analysis = Column(JSON, nullable=True)  # AI анализ ответа
    sentiment_score = Column(Float, nullable=True)
    confidence_score = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    question = relationship("AeonQuestion", back_populates="answer")


class AeonReport(Base):
    __tablename__ = "aeon_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("aeon_sessions.id"), nullable=False)
    archetype = Column(String(100), nullable=True)
    consciousness_vector = Column(String(100), nullable=True)
    motivation_score = Column(Float, nullable=True)
    growth_zone = Column(Text, nullable=True)
    genius_zone = Column(Text, nullable=True)
    synergy_score = Column(Float, nullable=True)
    flexibility_score = Column(Float, nullable=True)
    independence_score = Column(Float, nullable=True)
    adaptability_score = Column(Float, nullable=True)
    overall_assessment = Column(Text, nullable=True)
    recommendations = Column(JSON, nullable=True)
    report_json = Column(JSON, nullable=True)  # Полный отчет в JSON
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    session = relationship("AeonSession", back_populates="report") 