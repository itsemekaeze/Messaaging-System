from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from typing import List
from src.users.models import UserResponse, UserUpdate
from src.auth.services import get_current_user, save_upload_file
from src.entities.users import User
from src.database.core import get_db
from datetime import datetime

router = APIRouter(
    tags=["User"],
    prefix="/user"
)


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user info"""
    return current_user

@router.get("/", response_model=List[UserResponse])
def search_users(query: str = "", limit: int = 20, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Search users"""

    users = db.query(User).filter(User.username.contains(query) | User.display_name.contains(query)).filter(User.id != current_user.id).limit(limit).all()

    return users

@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user info"""
    return current_user

@router.patch("/me", response_model=UserResponse)
def update_user(update: UserUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):

    """Update user profile"""
    if update.display_name:
        current_user.display_name = update.display_name
    if update.email:
        existing = db.query(User).filter(User.email == update.email, User.id != current_user.id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already in use")
        current_user.email = update.email
    
    db.commit()
    db.refresh(current_user)
    return current_user

@router.post("/me/avatar")
def upload_avatar(file: UploadFile = File(...), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):

    """Upload user avatar"""
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    file_path, _ = save_upload_file(file, "avatars")
    current_user.avatar_url = f"/{file_path}"
    db.commit()
    
    return {"avatar_url": current_user.avatar_url}

@router.delete("/me")
def delete_user_account(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):

    """Delete user account (soft delete)"""
    current_user.is_active = False
    current_user.deleted_at = datetime.utcnow()
    current_user.is_online = False
    db.commit()
    return {"message": "Account deleted successfully"}


@router.get("/", response_model=List[UserResponse])
def search_users(query: str = "", limit: int = 20, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Search users"""
    users = db.query(User).filter(User.is_active == True).filter(User.username.contains(query) | User.display_name.contains(query)).filter(User.id != current_user.id).limit(limit).all()
    
    return users