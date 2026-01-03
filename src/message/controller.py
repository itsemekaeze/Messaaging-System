from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from src.message.models import MessageCreate, MessageResponse, MessageEdit
from src.auth.services import get_current_user
from src.entities.users import User
from typing import Optional
from src.database.core import get_db
from src.message.services import send_messages, get_all_messages, mark_message_as_read, send_media_messages, edit_messages, delete_messages

router = APIRouter(
    tags=["Messaging"]

)


@router.post("/messages", response_model=MessageResponse)
def send_message(message: MessageCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):

    return send_messages(message, current_user, db)


@router.post("/messages/upload")
def send_media_message(
    conversation_id: str,
    file: UploadFile = File(...),
    caption: str = "",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return send_media_messages(conversation_id, file, caption, current_user, db)

@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageResponse])
def get_messages(conversation_id: str, limit: int = 50, before: Optional[str] = None, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):

    return get_all_messages(conversation_id, limit, before, current_user, db)

@router.post("/messages/{message_id}/read")
def mark_message_read(message_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):

   
    return mark_message_as_read(message_id, current_user, db)


@router.patch("/messages/{message_id}", response_model=MessageResponse)
def edit_message(
    message_id: str,
    edit: MessageEdit,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return edit_messages(message_id, edit, current_user, db)

@router.delete("/messages/{message_id}")
def delete_message(
    message_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return delete_messages(message_id, current_user, db)