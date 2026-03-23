from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime
from typing import Optional, List

# ===== STUDENT SCHEMAS =====

class StudentBase(BaseModel):
    """Base student schema with common fields"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: Optional[str] = None

class StudentCreate(StudentBase):
    """Schema for creating a new student"""
    password: str = Field(..., min_length=6, max_length=100)

    @field_validator('password')
    @classmethod
    def password_strength(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters')
        return v

class StudentLogin(BaseModel):
    """Schema for student login"""
    username: str
    password: str

class StudentResponse(StudentBase):
    """Schema for returning student data (no password)"""
    id: int
    is_active: bool
    is_teacher: bool
    created_at: datetime
    last_login: datetime

    class Config:
        from_attributes = True

class StudentUpdate(BaseModel):
    """Schema for updating student profile"""
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None

# ===== QUESTION SCHEMAS =====

class QuestionBase(BaseModel):
    """Base question schema"""
    topic: str = Field(..., min_length=1, max_length=100)
    difficulty: int = Field(..., ge=1, le=5)
    question_text: str = Field(..., min_length=10)
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    correct_answer: str = Field(..., pattern="^[ABCD]$")  # ✅ Changed from regex to pattern
    explanation: Optional[str] = None

class QuestionCreate(QuestionBase):
    """Schema for creating a question"""
    pass

class QuestionResponse(QuestionBase):
    """Schema for returning question data"""
    id: int
    created_at: datetime
    times_asked: int
    times_correct: int
    success_rate: float

    class Config:
        from_attributes = True

class QuestionForStudent(BaseModel):
    """Schema for question displayed to student (no correct answer)"""
    id: int
    topic: str
    difficulty: int
    question_text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str

    class Config:
        from_attributes = True

# ===== INTERACTION SCHEMAS =====

class AnswerSubmission(BaseModel):
    """Schema for student submitting an answer"""
    student_id: int
    question_id: int
    answer_given: str = Field(..., pattern="^[ABCD]$")  # ✅ Changed from regex to pattern
    time_taken_seconds: int = Field(..., ge=0)

class AnswerResponse(BaseModel):
    """Schema for answer submission response"""
    correct: bool
    correct_answer: Optional[str] = None
    explanation: Optional[str] = None
    ai_explanation: Optional[str] = None
    new_mastery_level: float
    mastery_change: float
    needs_review: bool

class InteractionResponse(BaseModel):
    """Schema for interaction history"""
    id: int
    question_id: int
    answer_given: str
    is_correct: bool
    time_taken_seconds: int
    timestamp: datetime

    class Config:
        from_attributes = True

# ===== KNOWLEDGE STATE SCHEMAS =====

class KnowledgeStateResponse(BaseModel):
    """Schema for knowledge state"""
    id: int
    topic: str
    mastery_level: float
    total_attempts: int
    correct_attempts: int
    accuracy: float
    last_practiced: datetime
    needs_review: bool
    consecutive_correct: int
    consecutive_wrong: int

    class Config:
        from_attributes = True

class TopicMastery(BaseModel):
    """Simplified topic mastery for dashboards"""
    topic: str
    mastery_level: float
    needs_review: bool

# ===== ANALYTICS SCHEMAS =====

class StudentStats(BaseModel):
    """Overall student statistics"""
    total_questions: int
    correct_answers: int
    accuracy: float
    total_time_spent: int
    current_streak: int
    topics_mastered: int
    topics_in_progress: int
    topics_struggling: int

class DailyProgress(BaseModel):
    """Daily progress data"""
    date: str
    questions_attempted: int
    accuracy: float
    time_spent: int

class TopicDifficulty(BaseModel):
    """Topic difficulty analysis"""
    topic: str
    total_students: int
    avg_mastery: float
    avg_attempts: int
    success_rate: float

# ===== AUTH SCHEMAS =====

class Token(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    """Data stored in JWT token"""
    username: Optional[str] = None
    student_id: Optional[int] = None
