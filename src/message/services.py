from fastapi import Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from src.message.models import MessageCreate, MessageResponse, MessageEdit
from src.auth.services import get_current_user, save_upload_file
from src.entities.users import User
from src.entities.conversation_participant import ConversationParticipant
from src.entities.message import Message, MessageType
from src.entities.conversation import Conversation
from src.entities.message_read_receipt import MessageReadReceipt
from src.entities.typing_indicator import TypingIndicator
from datetime import datetime
from typing import Optional
from src.database.core import get_db



def send_messages(message: MessageCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):

    """Send a message"""
    # Verify user is participant
    participant = db.query(ConversationParticipant).filter(
            ConversationParticipant.conversation_id == message.conversation_id,
            ConversationParticipant.user_id == current_user.id
        ).first()
    
    if not participant:
        raise HTTPException(status_code=403, detail="Not a participant")
    
    # Create message
    db_message = Message(
        conversation_id=message.conversation_id,
        sender_id=current_user.id,
        content=message.content,
        message_type=message.message_type
    )
    db.add(db_message)
    
    # Update conversation timestamp
    conversation = db.query(Conversation).filter(Conversation.id == message.conversation_id).first()
    conversation.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_message)
    
    return db_message


def get_all_messages(
    conversation_id: str,
    limit: int = 50,
    before: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get messages from conversation"""
    participant = db.query(ConversationParticipant)\
        .filter(
            ConversationParticipant.conversation_id == conversation_id,
            ConversationParticipant.user_id == current_user.id,
            ConversationParticipant.is_active == True
        ).first()
    
    if not participant:
        raise HTTPException(status_code=403, detail="Not a participant")
    
    query = db.query(Message)\
        .filter(Message.conversation_id == conversation_id, Message.is_deleted == False)
    
    if before:
        query = query.filter(Message.id < before)
    
    messages = query.order_by(Message.created_at.desc()).limit(limit).all()
    
    # Add read_by info
    result = []
    for msg in reversed(messages):
        read_by = [r.user_id for r in msg.read_receipts]
        msg_dict = MessageResponse.from_orm(msg).dict()
        msg_dict['read_by'] = read_by
        result.append(MessageResponse(**msg_dict))
    
    return result


def mark_message_as_read(message_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):

    """Mark message as read"""
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    # Check if already read
    existing = db.query(MessageReadReceipt).filter(
            MessageReadReceipt.message_id == message_id,
            MessageReadReceipt.user_id == current_user.id
        ).first()
    
    if existing:
        return {"message": "Already marked as read"}
    
    # Create read receipt
    receipt = MessageReadReceipt(
        message_id=message_id,
        user_id=current_user.id
    )
    db.add(receipt)
    
    # Update last_read_at
    participant = db.query(ConversationParticipant).filter(
            ConversationParticipant.conversation_id == message.conversation_id,
            ConversationParticipant.user_id == current_user.id
        ).first()
    
    if participant:
        participant.last_read_at = datetime.utcnow()
    
    db.commit()
    
    return {"message": "Message marked as read"}



def send_media_messages(
    conversation_id: str,
    file: UploadFile = File(...),
    caption: str = "",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send image/video/file message"""
    participant = db.query(ConversationParticipant)\
        .filter(
            ConversationParticipant.conversation_id == conversation_id,
            ConversationParticipant.user_id == current_user.id,
            ConversationParticipant.is_active == True
        ).first()
    
    if not participant:
        raise HTTPException(status_code=403, detail="Not a participant")
    
    # Determine message type and subfolder
    content_type = file.content_type
    if content_type.startswith("image/"):
        message_type = MessageType.IMAGE
        subfolder = "images"
    elif content_type.startswith("video/"):
        message_type = MessageType.VIDEO
        subfolder = "videos"
    else:
        message_type = MessageType.FILE
        subfolder = "files"
    
    # Save file
    file_path, file_size = save_upload_file(file, subfolder)
    
    # Create message
    db_message = Message(
        conversation_id=conversation_id,
        sender_id=current_user.id,
        content=caption or file.filename,
        message_type=message_type,
        file_url=f"/{file_path}",
        file_name=file.filename,
        file_size=file_size
    )
    db.add(db_message)
    
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    conversation.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_message)
    return db_message

def edit_messages(
    message_id: str,
    edit: MessageEdit,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Edit message (sender only)"""
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    if message.sender_id != current_user.id:
        raise HTTPException(status_code=403, detail="Can only edit your own messages")
    
    if message.is_deleted:
        raise HTTPException(status_code=400, detail="Cannot edit deleted message")
    
    message.content = edit.content
    message.is_edited = True
    message.edited_at = datetime.utcnow()
    
    db.commit()
    db.refresh(message)
    return message


def delete_messages(
    message_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete message (sender only)"""
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    if message.sender_id != current_user.id:
        raise HTTPException(status_code=403, detail="Can only delete your own messages")
    
    message.is_deleted = True
    message.deleted_at = datetime.utcnow()
    message.content = "This message was deleted"
    
    db.commit()
    return {"message": "Message deleted"}