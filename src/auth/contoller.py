from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from src.auth.models import UserCreate, Token
from src.auth.services import get_password_hash, create_access_token, verify_password
from src.entities.users import User
from src.database.core import get_db

router = APIRouter(
    tags=["Authentication"],
    prefix="/auth"
)


@router.post("/register",)
def register(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if user exists
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=get_password_hash(user.password),
        display_name=user.display_name or user.username
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Create token
    # access_token = create_access_token(data={"sub": db_user.id})
    return {
        
        "user": db_user
    }


@router.post("/login", response_model=Token)
def login(username: str, password: str, db: Session = Depends(get_db)):
    """Login user"""
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Update online status
    user.is_online = True
    user.last_seen = datetime.utcnow()
    db.commit()
    
    access_token = create_access_token(data={"sub": user.id})
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }