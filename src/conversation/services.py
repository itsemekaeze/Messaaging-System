from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from src.conversation.models import ConversationCreate, ConversationResponse, ConversationUpdate, AddParticipantsRequest, TypingEvent, ParticipantResponse
from src.auth.services import get_current_user
from src.entities.conversation import Conversation
from src.entities.conversation_participant import ConversationParticipant
from src.entities.users import User
from src.entities.message import Message, MessageType
from src.entities.typing_indicator import TypingIndicator
from src.database.core import get_db
from src.entities.conversation_participant import ParticipantRole
from datetime import datetime

def create_conversations(
    conv: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create conversation"""
    participants = db.query(User).filter(User.id.in_(conv.participant_ids), User.is_active == True).all()
    if len(participants) != len(conv.participant_ids):
        raise HTTPException(status_code=400, detail="Some users not found")
    
    # Check if 1-on-1 exists
    if not conv.is_group and len(conv.participant_ids) == 1:
        other_user_id = conv.participant_ids[0]
        existing = db.query(Conversation).join(ConversationParticipant
                                               ).filter(Conversation.is_group == False).filter(ConversationParticipant.user_id.in_([current_user.id, other_user_id]))\
            .filter(ConversationParticipant.is_active == True).group_by(Conversation.id).having(db.func.count(ConversationParticipant.id) == 2).first()
        
        if existing:
            return get_conversation_response(existing, current_user.id, db)
    
    conversation = Conversation(
        name=conv.name, is_group=conv.is_group, created_by=current_user.id
    )
    db.add(conversation)
    db.flush()
    
    # Add creator as admin
    creator_participant = ConversationParticipant(
        conversation_id=conversation.id,
        user_id=current_user.id,
        role=ParticipantRole.ADMIN if conv.is_group else ParticipantRole.MEMBER
    )
    db.add(creator_participant)
    
    # Add other participants
    for user_id in conv.participant_ids:
        if user_id != current_user.id:
            participant = ConversationParticipant(
                conversation_id=conversation.id,
                user_id=user_id,
                role=ParticipantRole.MEMBER
            )
            db.add(participant)
    
    db.commit()
    db.refresh(conversation)
    return get_conversation_response(conversation, current_user.id, db)


def get_all_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all user conversations"""
    conversations = db.query(Conversation)\
        .join(ConversationParticipant)\
        .filter(ConversationParticipant.user_id == current_user.id)\
        .filter(ConversationParticipant.is_active == True)\
        .order_by(Conversation.updated_at.desc())\
        .all()
    
    return [get_conversation_response(conv, current_user.id, db) for conv in conversations]


def get_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific conversation"""
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    participant = db.query(ConversationParticipant)\
        .filter(
            ConversationParticipant.conversation_id == conversation_id,
            ConversationParticipant.user_id == current_user.id,
            ConversationParticipant.is_active == True
        ).first()
    
    if not participant:
        raise HTTPException(status_code=403, detail="Not a participant")
    
    return get_conversation_response(conversation, current_user.id, db)



def update_conversations(
    conversation_id: str,
    update: ConversationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update conversation (admin only)"""
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Not found")
    
    participant = db.query(ConversationParticipant)\
        .filter(
            ConversationParticipant.conversation_id == conversation_id,
            ConversationParticipant.user_id == current_user.id,
            ConversationParticipant.is_active == True
        ).first()
    
    if not participant or participant.role != ParticipantRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin only")
    
    if update.name:
        conversation.name = update.name
    
    db.commit()
    db.refresh(conversation)
    return get_conversation_response(conversation, current_user.id, db)



def add_participants(
    conversation_id: str,
    request: AddParticipantsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add participants to group (admin only)"""
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation or not conversation.is_group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    my_participant = db.query(ConversationParticipant)\
        .filter(
            ConversationParticipant.conversation_id == conversation_id,
            ConversationParticipant.user_id == current_user.id,
            ConversationParticipant.is_active == True
        ).first()
    
    if not my_participant or my_participant.role != ParticipantRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin only")
    
    added_users = []
    for user_id in request.user_ids:
        user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
        if not user:
            continue
        
        existing = db.query(ConversationParticipant)\
            .filter(
                ConversationParticipant.conversation_id == conversation_id,
                ConversationParticipant.user_id == user_id
            ).first()
        
        if existing:
            if not existing.is_active:
                existing.is_active = True
                existing.joined_at = datetime.utcnow()
                existing.left_at = None
                added_users.append(user_id)
        else:
            participant = ConversationParticipant(
                conversation_id=conversation_id,
                user_id=user_id,
                role=ParticipantRole.MEMBER
            )
            db.add(participant)
            added_users.append(user_id)
        
        # System message
        system_msg = Message(
            conversation_id=conversation_id,
            sender_id=current_user.id,
            content=f"{current_user.display_name} added {user.display_name}",
            message_type=MessageType.SYSTEM
        )
        db.add(system_msg)
    
    db.commit()
    return {"message": f"Added {len(added_users)} participants", "added_user_ids": added_users}


def remove_participants(
    conversation_id: str,
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove participant from group (admin only or self)"""
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation or not conversation.is_group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    my_participant = db.query(ConversationParticipant)\
        .filter(
            ConversationParticipant.conversation_id == conversation_id,
            ConversationParticipant.user_id == current_user.id,
            ConversationParticipant.is_active == True
        ).first()
    
    if not my_participant:
        raise HTTPException(status_code=403, detail="Not a participant")
    
    # Check permission: admin or removing self
    if user_id != current_user.id and my_participant.role != ParticipantRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin only")
    
    target_participant = db.query(ConversationParticipant)\
        .filter(
            ConversationParticipant.conversation_id == conversation_id,
            ConversationParticipant.user_id == user_id,
            ConversationParticipant.is_active == True
        ).first()
    
    if not target_participant:
        raise HTTPException(status_code=404, detail="Participant not found")
    
    # Soft delete
    target_participant.is_active = False
    target_participant.left_at = datetime.utcnow()
    
    # System message
    target_user = db.query(User).filter(User.id == user_id).first()
    action = "left" if user_id == current_user.id else "removed"
    system_msg = Message(
        conversation_id=conversation_id,
        sender_id=current_user.id,
        content=f"{target_user.display_name} {action} the group",
        message_type=MessageType.SYSTEM
    )
    db.add(system_msg)
    
    db.commit()
    return {"message": "Participant removed"}


def leave_conversations(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Leave a conversation"""
    participant = db.query(ConversationParticipant)\
        .filter(
            ConversationParticipant.conversation_id == conversation_id,
            ConversationParticipant.user_id == current_user.id,
            ConversationParticipant.is_active == True
        ).first()
    
    if not participant:
        raise HTTPException(status_code=404, detail="Not a participant")
    
    participant.is_active = False
    participant.left_at = datetime.utcnow()
    
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if conversation.is_group:
        system_msg = Message(
            conversation_id=conversation_id,
            sender_id=current_user.id,
            content=f"{current_user.display_name} left the group",
            message_type=MessageType.SYSTEM
        )
        db.add(system_msg)
    
    db.commit()
    return {"message": "Left conversation"}

def get_conversation_response(conversation: Conversation, user_id: str, db: Session):
    """Build conversation response with metadata"""
    last_message = db.query(Message)\
        .filter(Message.conversation_id == conversation.id, Message.is_deleted == False)\
        .order_by(Message.created_at.desc())\
        .first()
    
    participant = db.query(ConversationParticipant)\
        .filter(
            ConversationParticipant.conversation_id == conversation.id,
            ConversationParticipant.user_id == user_id
        ).first()
    
    unread_count = 0
    my_role = None
    if participant:
        my_role = participant.role.value
        unread_count = db.query(Message)\
            .filter(
                Message.conversation_id == conversation.id,
                Message.created_at > participant.last_read_at,
                Message.sender_id != user_id,
                Message.is_deleted == False
            ).count()
    
    participant_responses = []
    for p in conversation.participants:
        if p.is_active:
            participant_responses.append(ParticipantResponse(
                user=p.user,
                role=p.role.value,
                joined_at=p.joined_at
            ))
    
    return ConversationResponse(
        id=conversation.id,
        name=conversation.name,
        is_group=conversation.is_group,
        avatar_url=conversation.avatar_url,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        participants=participant_responses,
        last_message=last_message,
        unread_count=unread_count,
        my_role=my_role
    )



def send_typing_indicators(
    conversation_id: str,
    event: TypingEvent,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send typing indicator"""
    if event.is_typing:
        typing = TypingIndicator(conversation_id=conversation_id, user_id=current_user.id)
        db.add(typing)
        db.commit()
    else:
        db.query(TypingIndicator)\
            .filter(
                TypingIndicator.conversation_id == conversation_id,
                TypingIndicator.user_id == current_user.id
            ).delete()
        db.commit()
    
    return {"message": "Typing indicator sent"}

