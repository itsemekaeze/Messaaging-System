from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from src.conversation.models import ConversationCreate, ConversationResponse, ConversationUpdate, AddParticipantsRequest, TypingEvent
from src.auth.services import get_current_user
from src.entities.users import User
from src.database.core import get_db
from src.conversation.services import create_conversations, get_all_conversations, get_conversation, update_conversations, add_participants, leave_conversations, send_typing_indicators

router = APIRouter(
    tags=["Conversation"],
    prefix="/conversations"

)


@router.post("/", response_model=ConversationResponse)
def create_conversation(conv: ConversationCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    
       
    return create_conversations(conv, current_user, db)

@router.get("/", response_model=List[ConversationResponse])
def get_all_conversation(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
        
    return get_all_conversations(current_user, db)


@router.get("/{conversation_id}", response_model=ConversationResponse)
def get_conversations(conversation_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
        
    
    return get_conversation(conversation_id, current_user, db)


@router.patch("/{conversation_id}", response_model=ConversationResponse)
def update_conversation(
    conversation_id: str,
    update: ConversationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    return update_conversations(conversation_id, update, current_user, db)


@router.post("/{conversation_id}/participants")
def add_participant(
    conversation_id: str,
    request: AddParticipantsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return add_participants(conversation_id, request, current_user, db)

@router.delete("/{conversation_id}/participants/{user_id}")
def remove_participant(
    conversation_id: str,
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return remove_participant(conversation_id, user_id, current_user, db)


@router.post("/{conversation_id}/leave")
def leave_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return leave_conversations(conversation_id, current_user, db)


@router.post("/conversations/{conversation_id}/typing")
def send_typing_indicator(
    conversation_id: str,
    event: TypingEvent,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    
    
    return send_typing_indicators(conversation_id, event, current_user, db)