from fastapi import FastAPI
import json
import asyncio
import asyncpg
from src.database.core import Base, engine
from src.auth.contoller import router as auth_router
from src.users.controller import router as user_router
from src.conversation.controller import router as conversation_router
from src.message.controller import router as message_router
from src.websocket.websocket_controller import router as websocket_router
from src.websocket.websocket_manager import postgres_notifier
from src.database.core import ASYNC_DATABASE_URL

Base.metadata.create_all(bind=engine)


app = FastAPI()

@app.get("/")
def root():
    return {"message": "Welcome to fastapi messaging system"}


app.include_router(auth_router)
app.include_router(user_router)
app.include_router(conversation_router)
app.include_router(message_router)
app.include_router(websocket_router)


@app.on_event("startup")
async def startup():
    await postgres_notifier.connect()
    
    async with asyncpg.create_pool(ASYNC_DATABASE_URL) as pool:
        async with pool.acquire() as conn:
            # New message trigger
            await conn.execute("""
                CREATE OR REPLACE FUNCTION notify_new_message()
                RETURNS TRIGGER AS $$
                DECLARE
                    sender_data JSON;
                BEGIN
                    SELECT row_to_json(u.*) INTO sender_data FROM users u WHERE u.id = NEW.sender_id;
                    PERFORM pg_notify('new_message', json_build_object(
                        'id', NEW.id, 'conversation_id', NEW.conversation_id,
                        'sender_id', NEW.sender_id, 'content', NEW.content,
                        'message_type', NEW.message_type, 'file_url', NEW.file_url,
                        'file_name', NEW.file_name, 'created_at', NEW.created_at,
                        'sender', sender_data
                    )::text);
                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql;
                
                DROP TRIGGER IF EXISTS new_message_trigger ON messages;
                CREATE TRIGGER new_message_trigger AFTER INSERT ON messages
                FOR EACH ROW WHEN (NEW.is_deleted = FALSE)
                EXECUTE FUNCTION notify_new_message();
            """)
            
            # Message edited trigger
            await conn.execute("""
                CREATE OR REPLACE FUNCTION notify_message_edited()
                RETURNS TRIGGER AS $$
                BEGIN
                    IF OLD.content != NEW.content AND NEW.is_deleted = FALSE THEN
                        PERFORM pg_notify('message_edited', json_build_object(
                            'id', NEW.id, 'conversation_id', NEW.conversation_id,
                            'content', NEW.content, 'is_edited', NEW.is_edited,
                            'edited_at', NEW.edited_at
                        )::text);
                    END IF;
                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql;
                
                DROP TRIGGER IF EXISTS message_edited_trigger ON messages;
                CREATE TRIGGER message_edited_trigger AFTER UPDATE ON messages
                FOR EACH ROW EXECUTE FUNCTION notify_message_edited();
            """)
            
            # Message deleted trigger
            await conn.execute("""
                CREATE OR REPLACE FUNCTION notify_message_deleted()
                RETURNS TRIGGER AS $$
                BEGIN
                    IF OLD.is_deleted = FALSE AND NEW.is_deleted = TRUE THEN
                        PERFORM pg_notify('message_deleted', json_build_object(
                            'id', NEW.id, 'conversation_id', NEW.conversation_id,
                            'deleted_at', NEW.deleted_at
                        )::text);
                    END IF;
                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql;
                
                DROP TRIGGER IF EXISTS message_deleted_trigger ON messages;
                CREATE TRIGGER message_deleted_trigger AFTER UPDATE ON messages
                FOR EACH ROW EXECUTE FUNCTION notify_message_deleted();
            """)
            
            # Typing indicator trigger
            await conn.execute("""
                CREATE OR REPLACE FUNCTION notify_typing()
                RETURNS TRIGGER AS $$
                DECLARE user_data JSON;
                BEGIN
                    SELECT row_to_json(u.*) INTO user_data FROM users u WHERE u.id = NEW.user_id;
                    PERFORM pg_notify('typing_indicator', json_build_object(
                        'conversation_id', NEW.conversation_id,
                        'user_id', NEW.user_id, 'user', user_data, 'is_typing', TRUE
                    )::text);
                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql;
                
                DROP TRIGGER IF EXISTS typing_trigger ON typing_indicators;
                CREATE TRIGGER typing_trigger AFTER INSERT ON typing_indicators
                FOR EACH ROW EXECUTE FUNCTION notify_typing();
            """)
            
            # Read receipt trigger
            await conn.execute("""
                CREATE OR REPLACE FUNCTION notify_message_read()
                RETURNS TRIGGER AS $$
                BEGIN
                    PERFORM pg_notify('message_read', json_build_object(
                        'message_id', NEW.message_id, 'user_id', NEW.user_id,
                        'read_at', NEW.read_at,
                        'conversation_id', (SELECT conversation_id FROM messages WHERE id = NEW.message_id)
                    )::text);
                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql;
                
                DROP TRIGGER IF EXISTS read_receipt_trigger ON message_read_receipts;
                CREATE TRIGGER read_receipt_trigger AFTER INSERT ON message_read_receipts
                FOR EACH ROW EXECUTE FUNCTION notify_message_read();
            """)
            
            # Participant added/removed triggers
            await conn.execute("""
                CREATE OR REPLACE FUNCTION notify_participant_change()
                RETURNS TRIGGER AS $$
                DECLARE user_data JSON;
                BEGIN
                    SELECT row_to_json(u.*) INTO user_data FROM users u WHERE u.id = NEW.user_id;
                    
                    IF TG_OP = 'INSERT' THEN
                        PERFORM pg_notify('participant_added', json_build_object(
                            'conversation_id', NEW.conversation_id,
                            'user_id', NEW.user_id, 'user', user_data,
                            'role', NEW.role
                        )::text);
                    ELSIF TG_OP = 'UPDATE' AND OLD.is_active = TRUE AND NEW.is_active = FALSE THEN
                        PERFORM pg_notify('participant_removed', json_build_object(
                            'conversation_id', NEW.conversation_id,
                            'user_id', NEW.user_id
                        )::text);
                    END IF;
                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql;
                
                DROP TRIGGER IF EXISTS participant_change_trigger ON conversation_participants;
                CREATE TRIGGER participant_change_trigger
                AFTER INSERT OR UPDATE ON conversation_participants
                FOR EACH ROW EXECUTE FUNCTION notify_participant_change();
            """)
    
    print("Database triggers created")

@app.on_event("shutdown")
async def shutdown():
    await postgres_notifier.close()