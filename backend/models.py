from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Student(Base):
    """
    Student/User table
    Stores authentication and profile information
    """
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100))
    is_active = Column(Boolean, default=True)
    is_teacher = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, default=datetime.utcnow)

    # Relationships
    interactions = relationship("Interaction", back_populates="student", cascade="all, delete-orphan")
    knowledge_states = relationship("KnowledgeState", back_populates="student", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Student(id={self.id}, username='{self.username}')>"


class Question(Base):
    """
    Question bank table
    Stores all questions with metadata
    """
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    topic = Column(String(100), nullable=False, index=True)
    difficulty = Column(Integer, nullable=False)  # 1-5 scale
    question_text = Column(Text, nullable=False)
    option_a = Column(String(500), nullable=False)
    option_b = Column(String(500), nullable=False)
    option_c = Column(String(500), nullable=False)
    option_d = Column(String(500), nullable=False)
    correct_answer = Column(String(1), nullable=False)  # A, B, C, or D
    explanation = Column(Text)
    created_by = Column(Integer, ForeignKey("students.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    times_asked = Column(Integer, default=0)
    times_correct = Column(Integer, default=0)

    # Relationships
    interactions = relationship("Interaction", back_populates="question")

    def __repr__(self):
        return f"<Question(id={self.id}, topic='{self.topic}', difficulty={self.difficulty})>"

    @property
    def success_rate(self):
        """Calculate success rate for this question"""
        if self.times_asked == 0:
            return 0.0
        return (self.times_correct / self.times_asked) * 100


class Interaction(Base):
    """
    Student-Question interaction table
    Records every answer attempt
    """
    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False, index=True)
    answer_given = Column(String(1), nullable=False)  # A, B, C, or D
    is_correct = Column(Boolean, nullable=False)
    time_taken_seconds = Column(Integer)  # Time to answer
    ai_explanation = Column(Text)  # Groq AI explanation if wrong
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    student = relationship("Student", back_populates="interactions")
    question = relationship("Question", back_populates="interactions")

    def __repr__(self):
        return f"<Interaction(student_id={self.student_id}, question_id={self.question_id}, correct={self.is_correct})>"


class KnowledgeState(Base):
    """
    Student knowledge state per topic
    Tracks mastery levels using Bayesian Knowledge Tracing
    """
    __tablename__ = "knowledge_states"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    topic = Column(String(100), nullable=False, index=True)
    mastery_level = Column(Float, default=0.5)  # 0.0 to 1.0
    total_attempts = Column(Integer, default=0)
    correct_attempts = Column(Integer, default=0)
    last_practiced = Column(DateTime, default=datetime.utcnow)
    needs_review = Column(Boolean, default=False)
    consecutive_correct = Column(Integer, default=0)
    consecutive_wrong = Column(Integer, default=0)

    # Relationships
    student = relationship("Student", back_populates="knowledge_states")

    def __repr__(self):
        return f"<KnowledgeState(student_id={self.student_id}, topic='{self.topic}', mastery={self.mastery_level:.2f})>"

    @property
    def accuracy(self):
        """Calculate accuracy percentage"""
        if self.total_attempts == 0:
            return 0.0
        return (self.correct_attempts / self.total_attempts) * 100
