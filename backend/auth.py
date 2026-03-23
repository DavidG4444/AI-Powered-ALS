#Code to generate a secret key
#import secrets
#print(secrets.token_urlsafe(32))

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from config import get_settings
from database import get_db
from models import Student
from schemas import TokenData

# Get settings
settings = get_settings()

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

# ===== PASSWORD FUNCTIONS =====

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    Hash a plain password
    """
    return pwd_context.hash(password)

# ===== TOKEN FUNCTIONS =====

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    Create JWT access token

    Args:
        data: Data to encode in token (usually {"sub": username})
        expires_delta: Token expiration time

    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    return encoded_jwt

def decode_access_token(token: str) -> TokenData:
    """
    Decode and verify JWT token

    Args:
        token: JWT token string

    Returns:
        TokenData with username

    Raises:
        HTTPException if token is invalid
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        student_id: int = payload.get("student_id")

        if username is None:
            raise credentials_exception

        token_data = TokenData(username=username, student_id=student_id)
        return token_data

    except JWTError:
        raise credentials_exception

# ===== USER AUTHENTICATION =====

def authenticate_student(db: Session, username: str, password: str) -> Optional[Student]:
    """
    Authenticate a student with username and password

    Args:
        db: Database session
        username: Student username
        password: Plain password

    Returns:
        Student object if authentication successful, None otherwise
    """
    student = db.query(Student).filter(Student.username == username).first()

    if not student:
        return None

    if not verify_password(password, student.hashed_password):
        return None

    # Update last login
    student.last_login = datetime.utcnow()
    db.commit()

    return student

def get_current_student(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Student:
    """
    Get current authenticated student from JWT token

    This is a FastAPI dependency that can be used in route functions:

    @app.get("/protected-route")
    def protected_route(current_student: Student = Depends(get_current_student)):
        return {"message": f"Hello {current_student.username}"}

    Args:
        token: JWT token from Authorization header
        db: Database session

    Returns:
        Current student object

    Raises:
        HTTPException if authentication fails
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token_data = decode_access_token(token)

    student = db.query(Student).filter(Student.username == token_data.username).first()

    if student is None:
        raise credentials_exception

    if not student.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive account"
        )

    return student

def get_current_active_teacher(
    current_student: Student = Depends(get_current_student)
) -> Student:
    """
    Ensure current user is a teacher

    Usage:
    @app.get("/teacher-only-route")
    def teacher_route(teacher: Student = Depends(get_current_active_teacher)):
        return {"message": "Teacher access granted"}
    """
    if not current_student.is_teacher:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Teacher access required"
        )

    return current_student
