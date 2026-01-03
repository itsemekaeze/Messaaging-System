from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from datetime import datetime
from src.auth.services import decode_token
from src.database.core import get_db
from src.entities.users import User
from src.websocket.websocket_manager import manager
from src.entities.conversation import Conversation
from src.entities.conversation_participant import ConversationParticipant

router = APIRouter()



@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str, db: Session = Depends(get_db)):
    """WebSocket for real-time messaging"""
    user_id = decode_token(token)
    if not user_id:
        await websocket.close(code=1008)
        return
    
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        await websocket.close(code=1008)
        return
    
    await manager.connect(websocket, user_id)
    
    user.is_online = True
    user.last_seen = datetime.utcnow()
    db.commit()
    
    # Join all conversations
    conversations = db.query(ConversationParticipant)\
        .filter(ConversationParticipant.user_id == user_id, ConversationParticipant.is_active == True)\
        .all()
    
    for cp in conversations:
        manager.join_conversation(user_id, cp.conversation_id)
    
    try:
        while True:
            data = await websocket.receive_text()
            # Handle pings or other client messages
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
        user.is_online = False
        user.last_seen = datetime.utcnow()
        db.commit()
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket, user_id)
        user.is_online = False
        db.commit()