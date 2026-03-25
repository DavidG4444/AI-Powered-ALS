from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, case, desc
from utils.recommender import QuestionRecommender
from ai.groq_client import groq_client
from ml_models.knowledge_tracker import knowledge_tracker
from ml_models.difficulty_adapter import difficulty_adapter
from ml_models.learning_path import learning_path_generator
from services.analytics_service import AnalyticsService
from typing import Optional
from datetime import timedelta
from typing import Optional, List

# Import our modules
from config import get_settings
from database import get_db, init_db, test_connection
from models import Student, Question, Interaction, KnowledgeState
from schemas import (
    StudentCreate, StudentResponse, StudentLogin,
    QuestionCreate, QuestionResponse, QuestionForStudent,
    AnswerSubmission, AnswerResponse,
    KnowledgeStateResponse, Token
)
from auth import (
    get_password_hash, authenticate_student, create_access_token,
    get_current_student
)

# Get settings
settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="AI-Powered Adaptive Learning System API",
    version="1.0.0",
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc"  # ReDoc
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== STARTUP/SHUTDOWN EVENTS =====

@app.on_event("startup")
def startup_event():
    """
    Run when application starts
    """
    print("🚀 Starting Adaptive Learning System API...")

    # Test database connection
    if test_connection():
        print("✅ Database connection successful")
        # Initialize database tables
        if init_db():
            print("✅ Database initialized")
    else:
        print("❌ Database connection failed!")


    print("👋 Shutting down Adaptive Learning System API...")

# ===== ROOT ENDPOINT =====

@app.get("/")
def read_root():
    """
    Root endpoint - API health check
    """
    return {
        "message": f"Welcome to {settings.APP_NAME} API",
        "status": "online",
        "docs": "/docs",
        "version": "1.0.0"
    }

# ===== AUTHENTICATION ENDPOINTS =====

@app.post("/api/auth/register", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
def register_student(
    student_data: StudentCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new student

    - **username**: Unique username (3-50 characters)
    - **email**: Valid email address
    - **password**: Minimum 6 characters
    - **full_name**: Optional full name
    """
    # Check if username already exists
    existing_student = db.query(Student).filter(Student.username == student_data.username).first()
    if existing_student:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    # Check if email already exists
    existing_email = db.query(Student).filter(Student.email == student_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create new student
    hashed_password = get_password_hash(student_data.password)

    new_student = Student(
        username=student_data.username,
        email=student_data.email,
        hashed_password=hashed_password,
        full_name=student_data.full_name
    )

    db.add(new_student)
    db.commit()
    db.refresh(new_student)

    return new_student

@app.post("/api/auth/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Login and get access token

    - **username**: Your username
    - **password**: Your password

    Returns JWT access token
    """
    student = authenticate_student(db, form_data.username, form_data.password)

    if not student:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": student.username, "student_id": student.id},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/auth/me", response_model=StudentResponse)
def get_current_user_info(
    current_student: Student = Depends(get_current_student)
):
    """
    Get current logged-in student information

    Requires authentication token
    """
    return current_student

# ===== STUDENT ENDPOINTS =====

@app.get("/api/students/{student_id}", response_model=StudentResponse)
def get_student(
    student_id: int,
    db: Session = Depends(get_db),
    current_student: Student = Depends(get_current_student)
):
    """
    Get student information by ID

    Students can only view their own profile unless they're a teacher
    """
    # Check authorization
    if current_student.id != student_id and not current_student.is_teacher:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this profile"
        )

    student = db.query(Student).filter(Student.id == student_id).first()

    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )

    return student

# ===== QUESTION ENDPOINTS =====

@app.post("/api/questions", response_model=QuestionResponse, status_code=status.HTTP_201_CREATED)
def create_question(
    question_data: QuestionCreate,
    db: Session = Depends(get_db),
    current_student: Student = Depends(get_current_student)
):
    """
    Create a new question

    Requires authentication
    """
    new_question = Question(
        topic=question_data.topic,
        difficulty=question_data.difficulty,
        question_text=question_data.question_text,
        option_a=question_data.option_a,
        option_b=question_data.option_b,
        option_c=question_data.option_c,
        option_d=question_data.option_d,
        correct_answer=question_data.correct_answer,
        explanation=question_data.explanation,
        created_by=current_student.id
    )

    db.add(new_question)
    db.commit()
    db.refresh(new_question)

    return new_question

@app.get("/api/questions", response_model=List[QuestionForStudent])
def get_questions(
    topic: str = 0,
    difficulty: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_student: Student = Depends(get_current_student)
):
    """
    Get questions (without correct answers)

    - **topic**: Filter by topic (optional)
    - **difficulty**: Filter by difficulty 1-5 (optional)
    - **limit**: Maximum number of questions (default 10)
    """
    query = db.query(Question)

    if topic:
        query = query.filter(Question.topic == topic)
    if difficulty:
        query = query.filter(Question.difficulty == difficulty)

    questions = query.limit(limit).all()

    return questions

@app.get("/api/questions/{question_id}", response_model=QuestionForStudent)
def get_question(
    question_id: int,
    db: Session = Depends(get_db),
    current_student: Student = Depends(get_current_student)
):
    """
    Get a specific question by ID (without correct answer)
    """
    question = db.query(Question).filter(Question.id == question_id).first()

    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )

    return question

# ===== ANSWER SUBMISSION ENDPOINT =====

@app.post("/api/submit-answer", response_model=AnswerResponse)
def submit_answer(
    submission: AnswerSubmission,
    db: Session = Depends(get_db),
    current_student: Student = Depends(get_current_student)
):
    """
    Submit an answer to a question

    This is the core endpoint that:
    1. Checks if answer is correct
    2. Generates AI explanation if wrong
    3. Updates knowledge state
    4. Records interaction
    """
    # Verify student_id matches current user
    if submission.student_id != current_student.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot submit answer for another student"
        )

    # Get question
    question = db.query(Question).filter(Question.id == submission.question_id).first()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )

    # Check if answer is correct
    is_correct = submission.answer_given == question.correct_answer

    # Update question statistics
    question.times_asked += 1
    if is_correct:
        question.times_correct += 1

    # TODO: Generate AI explanation if wrong (will implement in Day 3)
    ai_explanation = None
    if not is_correct:
        ai_explanation = "AI explanation will be generated here using Groq API"

    # Record interaction
    interaction = Interaction(
        student_id=submission.student_id,
        question_id=submission.question_id,
        answer_given=submission.answer_given,
        is_correct=is_correct,
        time_taken_seconds=submission.time_taken_seconds,
        ai_explanation=ai_explanation
    )
    db.add(interaction)

    # Get or create knowledge state
    knowledge_state = db.query(KnowledgeState).filter(
        KnowledgeState.student_id == submission.student_id,
        KnowledgeState.topic == question.topic
    ).first()

    if not knowledge_state:
        knowledge_state = KnowledgeState(
            student_id=submission.student_id,
            topic=question.topic
        )
        db.add(knowledge_state)

    # Ensure fields are never None for math operations
    knowledge_state.total_attempts = (knowledge_state.total_attempts or 0) + 1
    knowledge_state.correct_attempts = knowledge_state.correct_attempts or 0
    knowledge_state.consecutive_correct = knowledge_state.consecutive_correct or 0
    knowledge_state.consecutive_wrong = knowledge_state.consecutive_wrong or 0
    knowledge_state.mastery_level = knowledge_state.mastery_level if knowledge_state.mastery_level is not None else 0.5

    # Store old mastery for calculating change
    old_mastery = knowledge_state.mastery_level

    if is_correct:
        knowledge_state.correct_attempts += 1
        knowledge_state.consecutive_correct += 1
        knowledge_state.consecutive_wrong = 0
        # Increase mastery (diminishing returns as mastery approaches 1.0)
        knowledge_state.mastery_level = min(1.0, knowledge_state.mastery_level + 0.05 * (1.0 - knowledge_state.mastery_level))
    else:
        knowledge_state.consecutive_wrong += 1
        knowledge_state.consecutive_correct = 0
        # Decrease mastery
        knowledge_state.mastery_level = max(0.0, knowledge_state.mastery_level - 0.1)
        knowledge_state.needs_review = True

    # Calculate mastery change
    mastery_change = knowledge_state.mastery_level - old_mastery

    # Commit all changes
    db.commit()

    # Prepare response
    response = AnswerResponse(
        correct=is_correct,
        correct_answer=question.correct_answer if not is_correct else None,
        explanation=question.explanation if not is_correct else None,
        ai_explanation=ai_explanation,
        new_mastery_level=knowledge_state.mastery_level,
        mastery_change=mastery_change,
        needs_review=knowledge_state.needs_review
    )

    return response

# ===== KNOWLEDGE STATE ENDPOINTS =====

@app.get("/api/students/{student_id}/knowledge", response_model=List[KnowledgeStateResponse])
def get_student_knowledge_states(
    student_id: int,
    db: Session = Depends(get_db),
    current_student: Student = Depends(get_current_student)
):
    """
    Get all knowledge states for a student

    Shows mastery levels across all topics
    """
    # Authorization check
    if current_student.id != student_id and not current_student.is_teacher:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this data"
        )

    knowledge_states = db.query(KnowledgeState).filter(
        KnowledgeState.student_id == student_id
    ).all()

    return knowledge_states

# ===== UTILITY ENDPOINTS =====

@app.get("/api/topics")
def get_all_topics(
    db: Session = Depends(get_db)
):
    """
    Get list of all available topics
    """
    topics = db.query(Question.topic).distinct().all()
    return {"topics": [topic[0] for topic in topics]}

@app.get("/api/health")
def health_check():
    """
    Health check endpoint for monitoring
    """
    return {
        "status": "healthy",
        "database": "connected",
        "version": "1.0.0"
    }

# Run with: uvicorn main:app --reload

# ===== QUESTION RECOMMENDATION ENDPOINTS =====

@app.get("/api/questions/next", response_model=QuestionForStudent)
def get_next_question(
    topic: Optional[str] = None,
    db: Session = Depends(get_db),
    current_student: Student = Depends(get_current_student)
):
    """
    Get next recommended question for the student

    - Considers student's knowledge state
    - Recommends appropriate difficulty
    - Prioritizes weak areas
    - Avoids recently answered questions
    """
    recommender = QuestionRecommender(db)
    question = recommender.get_next_question(current_student.id, topic)

    if not question:
        raise HTTPException(
            status_code=404,
            detail="No suitable questions found. Try a different topic."
        )

    return question

@app.get("/api/recommendations/topics")
def get_topic_recommendations(
    limit: int = 3,
    db: Session = Depends(get_db),
    current_student: Student = Depends(get_current_student)
):
    """
    Get recommended topics for student to practice

    Returns topics ordered by priority (weakest areas first)
    """
    recommender = QuestionRecommender(db)
    recommendations = recommender.get_recommended_topics(current_student.id, limit)

    return {
        "student_id": current_student.id,
        "recommendations": recommendations
    }

@app.get("/api/students/{student_id}/stats")
def get_student_stats(
    student_id: int,
    db: Session = Depends(get_db),
    current_student: Student = Depends(get_current_student)
):
    """
    Get overall statistics for a student
    """
    # Authorization check
    if current_student.id != student_id and not current_student.is_teacher:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Get all interactions
    interactions = db.query(Interaction).filter(
        Interaction.student_id == student_id
    ).all()

    total_questions = len(interactions)
    correct_answers = sum(1 for i in interactions if i.is_correct)
    accuracy = (correct_answers / total_questions * 100) if total_questions > 0 else 0

    # Get knowledge states
    knowledge_states = db.query(KnowledgeState).filter(
        KnowledgeState.student_id == student_id
    ).all()

    topics_mastered = sum(1 for ks in knowledge_states if ks.mastery_level >= 0.8)
    topics_in_progress = sum(1 for ks in knowledge_states if 0.4 <= ks.mastery_level < 0.8)
    topics_struggling = sum(1 for ks in knowledge_states if ks.mastery_level < 0.4)

    return {
        "student_id": student_id,
        "total_questions": total_questions,
        "correct_answers": correct_answers,
        "accuracy": round(accuracy, 2),
        "topics_mastered": topics_mastered,
        "topics_in_progress": topics_in_progress,
        "topics_struggling": topics_struggling,
        "knowledge_states": [
            {
                "topic": ks.topic,
                "mastery_level": round(ks.mastery_level, 2),
                "accuracy": round(ks.accuracy, 2)
            }
            for ks in knowledge_states
        ]
    }
@app.post("/api/submit-answer", response_model=AnswerResponse)
def submit_answer(
    submission: AnswerSubmission,
    db: Session = Depends(get_db),
    current_student: Student = Depends(get_current_student)
):
    """
    Submit answer with AI-powered feedback and ML-based knowledge tracking
    """
    if submission.student_id != current_student.id:
        raise HTTPException(status_code=403, detail="Cannot submit for another student")

    # Get question
    question = db.query(Question).filter(Question.id == submission.question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    is_correct = submission.answer_given == question.correct_answer

    # Update question statistics
    question.times_asked += 1
    if is_correct:
        question.times_correct += 1

    # Generate AI explanation if wrong
    ai_explanation = None
    if not is_correct:
        try:
            ai_explanation = groq_client.generate_explanation(
                question_text=question.question_text,
                correct_answer=question.correct_answer,
                student_answer=submission.answer_given,
                topic=question.topic,
                explanation=question.explanation
            )
        except Exception as e:
            print(f"AI explanation error: {e}")
            ai_explanation = question.explanation

    # Record interaction
    interaction = Interaction(
        student_id=submission.student_id,
        question_id=submission.question_id,
        answer_given=submission.answer_given,
        is_correct=is_correct,
        time_taken_seconds=submission.time_taken_seconds,
        ai_explanation=ai_explanation
    )
    db.add(interaction)

    # Get or create knowledge state
    knowledge_state = db.query(KnowledgeState).filter(
        KnowledgeState.student_id == submission.student_id,
        KnowledgeState.topic == question.topic
    ).first()

    if not knowledge_state:
        knowledge_state = KnowledgeState(
            student_id=submission.student_id,
            topic=question.topic,
            mastery_level=knowledge_tracker.initialize_knowledge()
        )
        db.add(knowledge_state)

    # Ensure fields are never None for math operations
    knowledge_state.total_attempts = (knowledge_state.total_attempts or 0)
    knowledge_state.correct_attempts = knowledge_state.correct_attempts or 0
    knowledge_state.consecutive_correct = knowledge_state.consecutive_correct or 0
    knowledge_state.consecutive_wrong = knowledge_state.consecutive_wrong or 0
    knowledge_state.mastery_level = knowledge_state.mastery_level if knowledge_state.mastery_level is not None else 0.5

    # Store old mastery
    old_mastery = knowledge_state.mastery_level

    # Update using Bayesian Knowledge Tracking
    new_mastery = knowledge_tracker.update_knowledge(
        current_mastery=old_mastery,
        is_correct=is_correct,
        difficulty=question.difficulty
    )

    # Update knowledge state
    knowledge_state.mastery_level = new_mastery
    knowledge_state.total_attempts += 1

    if is_correct:
        knowledge_state.correct_attempts += 1
        knowledge_state.consecutive_correct += 1
        knowledge_state.consecutive_wrong = 0
    else:
        knowledge_state.consecutive_wrong += 1
        knowledge_state.consecutive_correct = 0
        knowledge_state.needs_review = new_mastery < 0.6

    mastery_change = new_mastery - old_mastery

    db.commit()

    # Prepare response
    response = AnswerResponse(
        correct=is_correct,
        correct_answer=question.correct_answer if not is_correct else None,
        explanation=question.explanation if not is_correct else None,
        ai_explanation=ai_explanation,
        new_mastery_level=new_mastery,
        mastery_change=mastery_change,
        needs_review=knowledge_state.needs_review
    )

    return response

# ===== AI-POWERED ENDPOINTS =====

@app.get("/api/questions/{question_id}/hint")
def get_question_hint(
    question_id: int,
    db: Session = Depends(get_db),
    current_student: Student = Depends(get_current_student)
):
    """
    Get an AI-generated hint for a question (without revealing answer)
    """
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    try:
        hint = groq_client.generate_hint(
            question_text=question.question_text,
            topic=question.topic,
            difficulty=question.difficulty
        )
        return {"question_id": question_id, "hint": hint}
    except Exception as e:
        return {"question_id": question_id, "hint": "Think about the key concepts and try to eliminate wrong answers."}

@app.get("/api/students/{student_id}/learning-path")
def get_learning_path(
    student_id: int,
    time_available: Optional[int] = None,
    db: Session = Depends(get_db),
    current_student: Student = Depends(get_current_student)
):
    """
    Generate personalized learning path

    Args:
        student_id: Student ID
        time_available: Optional time constraint in minutes
    """
    if current_student.id != student_id and not current_student.is_teacher:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Get knowledge states
    knowledge_states = db.query(KnowledgeState).filter(
        KnowledgeState.student_id == student_id
    ).all()

    # Convert to dict
    mastery_dict = {ks.topic: ks.mastery_level for ks in knowledge_states}

    # Get all available topics
    all_topics = db.query(Question.topic).distinct().all()
    available_topics = [t[0] for t in all_topics]

    # Generate path
    path = learning_path_generator.generate_path(
        knowledge_states=mastery_dict,
        available_topics=available_topics,
        time_available_minutes=time_available,
        focus_weak_areas=True
    )

    return {
        "student_id": student_id,
        "path": [
            {
                "topic": step.topic,
                "difficulty": step.difficulty,
                "estimated_questions": step.estimated_questions,
                "estimated_time_minutes": step.estimated_time_minutes,
                "current_mastery": round(step.current_mastery, 2),
                "target_mastery": round(step.target_mastery, 2),
                "priority": step.priority,
                "reason": step.reason
            }
            for step in path
        ]
    }

@app.get("/api/students/{student_id}/study-tips")
def get_study_tips(
    student_id: int,
    db: Session = Depends(get_db),
    current_student: Student = Depends(get_current_student)
):
    """
    Get AI-generated study tips based on weak areas
    """
    if current_student.id != student_id and not current_student.is_teacher:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Find weak areas
    knowledge_states = db.query(KnowledgeState).filter(
        and_(
            KnowledgeState.student_id == student_id,
            KnowledgeState.mastery_level < 0.6
        )
    ).all()

    if not knowledge_states:
        return {
            "student_id": student_id,
            "message": "Great job! You're doing well in all areas. Keep practicing to maintain your skills.",
            "tips": None
        }

    # Get main weak topic
    weakest = min(knowledge_states, key=lambda x: x.mastery_level)
    weak_topics = [ks.topic for ks in knowledge_states[:3]]  # Top 3 weak areas

    try:
        tips = groq_client.generate_study_tips(
            topic=weakest.topic,
            weak_areas=weak_topics
        )

        return {
            "student_id": student_id,
            "weak_areas": weak_topics,
            "tips": tips
        }
    except Exception as e:
        return {
            "student_id": student_id,
            "weak_areas": weak_topics,
            "tips": f"Focus on practicing {', '.join(weak_topics)}. Review the fundamentals and try explaining concepts in your own words."
        }

@app.get("/api/knowledge-gaps")
def analyze_knowledge_gaps(
    db: Session = Depends(get_db),
    current_student: Student = Depends(get_current_student)
):
    """
    Analyze knowledge gaps using BKT model
    """
    # Get all knowledge states
    knowledge_states = db.query(KnowledgeState).filter(
        KnowledgeState.student_id == current_student.id
    ).all()

    if not knowledge_states:
        return {
            "student_id": current_student.id,
            "gaps": [],
            "message": "Start practicing to identify areas for improvement!"
        }

    # Convert to dict for BKT analysis
    mastery_dict = {ks.topic: ks.mastery_level for ks in knowledge_states}

    # Identify gaps using BKT
    gaps = knowledge_tracker.identify_knowledge_gaps(mastery_dict, threshold=0.6)

    return {
        "student_id": current_student.id,
        "gaps": gaps,
        "total_gaps": len(gaps)
    }
# ===== ANALYTICS ENDPOINTS =====

@app.get("/api/analytics/student/{student_id}/overview")
def get_student_analytics_overview(
    student_id: int,
    db: Session = Depends(get_db),
    current_student: Student = Depends(get_current_student)
):
    """
    Get comprehensive analytics overview for a student
    """
    # Authorization check
    if current_student.id != student_id and not current_student.is_teacher:
        raise HTTPException(status_code=403, detail="Not authorized")

    analytics = AnalyticsService(db)
    overview = analytics.get_student_overview(student_id)

    return overview

@app.get("/api/analytics/student/{student_id}/progress")
def get_student_progress(
    student_id: int,
    days: int = 30,
    db: Session = Depends(get_db),
    current_student: Student = Depends(get_current_student)
):
    """
    Get daily progress data for visualization
    """
    if current_student.id != student_id and not current_student.is_teacher:
        raise HTTPException(status_code=403, detail="Not authorized")

    analytics = AnalyticsService(db)
    progress = analytics.get_progress_over_time(student_id, days)

    return {
        "student_id": student_id,
        "days": days,
        "data": progress
    }

@app.get("/api/analytics/student/{student_id}/topics")
def get_student_topic_breakdown(
    student_id: int,
    db: Session = Depends(get_db),
    current_student: Student = Depends(get_current_student)
):
    """
    Get detailed performance breakdown by topic
    """
    if current_student.id != student_id and not current_student.is_teacher:
        raise HTTPException(status_code=403, detail="Not authorized")

    analytics = AnalyticsService(db)
    topics = analytics.get_topic_breakdown(student_id)

    return {
        "student_id": student_id,
        "topics": topics
    }

@app.get("/api/analytics/student/{student_id}/difficulty")
def get_performance_by_difficulty(
    student_id: int,
    db: Session = Depends(get_db),
    current_student: Student = Depends(get_current_student)
):
    """
    Analyze performance across difficulty levels
    """
    if current_student.id != student_id and not current_student.is_teacher:
        raise HTTPException(status_code=403, detail="Not authorized")

    analytics = AnalyticsService(db)
    difficulty_stats = analytics.get_performance_by_difficulty(student_id)

    return {
        "student_id": student_id,
        "difficulty_analysis": difficulty_stats
    }

@app.get("/api/analytics/student/{student_id}/comparison")
def compare_to_class(
    student_id: int,
    db: Session = Depends(get_db),
    current_student: Student = Depends(get_current_student)
):
    """
    Compare student performance to class average
    """
    if current_student.id != student_id and not current_student.is_teacher:
        raise HTTPException(status_code=403, detail="Not authorized")

    analytics = AnalyticsService(db)
    comparison = analytics.compare_student_to_class(student_id)

    return comparison

@app.get("/api/analytics/student/{student_id}/trends")
def get_improvement_trends(
    student_id: int,
    days: int = 14,
    db: Session = Depends(get_db),
    current_student: Student = Depends(get_current_student)
):
    """
    Analyze improvement trends
    """
    if current_student.id != student_id and not current_student.is_teacher:
        raise HTTPException(status_code=403, detail="Not authorized")

    analytics = AnalyticsService(db)
    trends = analytics.get_improvement_trends(student_id, days)

    return trends

# ===== TEACHER DASHBOARD ENDPOINTS =====

@app.get("/api/teacher/dashboard")
def get_teacher_dashboard(
    db: Session = Depends(get_db),
    current_student: Student = Depends(get_current_student)
):
    """
    Get complete teacher dashboard data

    Requires teacher privileges
    """
    if not current_student.is_teacher:
        raise HTTPException(
            status_code=403,
            detail="Teacher access required"
        )

    analytics = AnalyticsService(db)

    return {
        "class_overview": analytics.get_class_overview(),
        "struggling_students": analytics.get_struggling_students(mastery_threshold=0.4, min_attempts=5)[:10],
        "inactive_students": analytics.get_inactive_students(days=7)[:10],
        "topic_difficulty": analytics.get_topic_difficulty_analysis()
    }

@app.get("/api/teacher/struggling-students")
def get_struggling_students(
    mastery_threshold: float = 0.4,
    min_attempts: int = 5,
    db: Session = Depends(get_db),
    current_student: Student = Depends(get_current_student)
):
    """
    Get list of students who need help
    """
    if not current_student.is_teacher:
        raise HTTPException(status_code=403, detail="Teacher access required")

    analytics = AnalyticsService(db)
    struggling = analytics.get_struggling_students(mastery_threshold, min_attempts)

    return {
        "threshold": mastery_threshold,
        "min_attempts": min_attempts,
        "students": struggling,
        "total_struggling": len(struggling)
    }

@app.get("/api/teacher/inactive-students")
def get_inactive_students(
    days: int = 7,
    db: Session = Depends(get_db),
    current_student: Student = Depends(get_current_student)
):
    """
    Find students who haven't practiced recently
    """
    if not current_student.is_teacher:
        raise HTTPException(status_code=403, detail="Teacher access required")

    analytics = AnalyticsService(db)
    inactive = analytics.get_inactive_students(days)

    return {
        "days_threshold": days,
        "inactive_students": inactive,
        "total_inactive": len(inactive)
    }

@app.get("/api/teacher/topic-analysis")
def get_topic_difficulty_analysis(
    db: Session = Depends(get_db),
    current_student: Student = Depends(get_current_student)
):
    """
    Analyze which topics are hardest for the class
    """
    if not current_student.is_teacher:
        raise HTTPException(status_code=403, detail="Teacher access required")

    analytics = AnalyticsService(db)
    topics = analytics.get_topic_difficulty_analysis()

    return {
        "topics": topics,
        "total_topics": len(topics)
    }

@app.get("/api/teacher/common-mistakes")
def get_common_mistakes(
    topic: Optional[str] = None,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_student: Student = Depends(get_current_student)
):
    """
    Find most common mistakes students make
    """
    if not current_student.is_teacher:
        raise HTTPException(status_code=403, detail="Teacher access required")

    analytics = AnalyticsService(db)
    mistakes = analytics.get_common_mistakes(topic, limit)

    return {
        "topic_filter": topic,
        "common_mistakes": mistakes,
        "total": len(mistakes)
    }

@app.get("/api/teacher/class-overview")
def get_class_overview(
    db: Session = Depends(get_db),
    current_student: Student = Depends(get_current_student)
):
    """
    Get overall class statistics
    """
    if not current_student.is_teacher:
        raise HTTPException(status_code=403, detail="Teacher access required")

    analytics = AnalyticsService(db)
    overview = analytics.get_class_overview()

    return overview

# ===== LEADERBOARD ENDPOINT =====

@app.get("/api/leaderboard")
def get_leaderboard(
    limit: int = 10,
    metric: str = "accuracy",  # "accuracy", "mastery", "questions"
    db: Session = Depends(get_db),
    current_student: Student = Depends(get_current_student)
):
    """
    Get leaderboard rankings

    Metrics:
    - accuracy: Overall accuracy percentage
    - mastery: Average mastery across topics
    - questions: Total questions answered
    """
    if metric == "accuracy":
        # Rank by accuracy
        leaderboard_query = db.query(
            Student.id,
            Student.username,
            func.count(Interaction.id).label('total_questions'),
            func.sum(case((Interaction.is_correct == True, 1), else_=0)).label('correct'),
            (func.sum(case((Interaction.is_correct == True, 1.0), else_=0.0)) /
             func.count(Interaction.id) * 100).label('accuracy')
        ).join(
            Interaction, Interaction.student_id == Student.id
        ).group_by(
            Student.id,
            Student.username
        ).having(
            func.count(Interaction.id) >= 10  # Minimum 10 questions
        ).order_by(
            desc('accuracy')
        ).limit(limit)

    elif metric == "mastery":
        # Rank by average mastery
        leaderboard_query = db.query(
            Student.id,
            Student.username,
            func.count(KnowledgeState.id).label('topics_count'),
            func.avg(KnowledgeState.mastery_level).label('avg_mastery')
        ).join(
            KnowledgeState, KnowledgeState.student_id == Student.id
        ).group_by(
            Student.id,
            Student.username
        ).order_by(
            desc('avg_mastery')
        ).limit(limit)

    else:  # questions
        # Rank by total questions
        leaderboard_query = db.query(
            Student.id,
            Student.username,
            func.count(Interaction.id).label('total_questions')
        ).join(
            Interaction, Interaction.student_id == Student.id
        ).group_by(
            Student.id,
            Student.username
        ).order_by(
            desc('total_questions')
        ).limit(limit)

    results = leaderboard_query.all()

    leaderboard = []
    for rank, student in enumerate(results, 1):
        if metric == "accuracy":
            leaderboard.append({
                "rank": rank,
                "student_id": student.id,
                "username": student.username,
                "total_questions": student.total_questions,
                "correct": student.correct,
                "accuracy": round(student.accuracy, 2)
            })
        elif metric == "mastery":
            leaderboard.append({
                "rank": rank,
                "student_id": student.id,
                "username": student.username,
                "topics_count": student.topics_count,
                "avg_mastery": round(student.avg_mastery, 2)
            })
        else:
            leaderboard.append({
                "rank": rank,
                "student_id": student.id,
                "username": student.username,
                "total_questions": student.total_questions
            })

    return {
        "metric": metric,
        "leaderboard": leaderboard
    }
