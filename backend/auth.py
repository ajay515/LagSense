from passlib.context import CryptContext
from sqlalchemy.orm import Session
from database import User

# Use argon2 instead of bcrypt to avoid the 72-byte limit
pwd_context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hash password using argon2 (no 72-byte limit like bcrypt)"""
    if len(password) > 1000:
        password = password[:1000]  # Safety limit
    return pwd_context.hash(password)

def verify_password(password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    if len(password) > 1000:
        password = password[:1000]
    return pwd_context.verify(password, hashed_password)

def register_user(db: Session, email: str, password: str):
    """Register a new user"""
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        return None

    user = User(
        email=email,
        password=hash_password(password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def login_user(db: Session, email: str, password: str):
    """Login user and verify password"""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None
    if not verify_password(password, user.password):
        return None
    return user