from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import List

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
    topic: str = None,
    difficulty: int = None,
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

    # Store old mastery for calculating change
    old_mastery = knowledge_state.mastery_level

    # Update knowledge state (simple version - will enhance with ML in Day 3)
    knowledge_state.total_attempts += 1

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
