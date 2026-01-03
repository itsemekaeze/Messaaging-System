from fastapi import WebSocket
from typing import  Dict, Set, Optional
from src.database.core import ASYNC_DATABASE_URL
import asyncpg
import json



class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.conversation_rooms: Dict[str, Set[str]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
        print(f"User {user_id} connected. Active: {sum(len(c) for c in self.active_connections.values())}")
    
    def disconnect(self, websocket: WebSocket, user_id: str):
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                for room_users in self.conversation_rooms.values():
                    room_users.discard(user_id)
        print(f"User {user_id} disconnected")
    
    def join_conversation(self, user_id: str, conversation_id: str):
        if conversation_id not in self.conversation_rooms:
            self.conversation_rooms[conversation_id] = set()
        self.conversation_rooms[conversation_id].add(user_id)
    
    def leave_conversation(self, user_id: str, conversation_id: str):
        if conversation_id in self.conversation_rooms:
            self.conversation_rooms[conversation_id].discard(user_id)
    
    async def send_personal_message(self, message: dict, user_id: str):
        if user_id in self.active_connections:
            disconnected = set()
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except:
                    disconnected.add(connection)
            for conn in disconnected:
                self.active_connections[user_id].discard(conn)
    
    async def broadcast_to_conversation(self, message: dict, conversation_id: str, exclude_user: Optional[str] = None):
        if conversation_id in self.conversation_rooms:
            for user_id in self.conversation_rooms[conversation_id]:
                if user_id != exclude_user:
                    await self.send_personal_message(message, user_id)

manager = ConnectionManager()




class PostgresNotifier:
    def __init__(self):
        self.connection = None
        self.listening = False
    
    async def connect(self):
        self.connection = await asyncpg.connect(ASYNC_DATABASE_URL)
        await self.connection.add_listener('new_message', self.message_callback)
        await self.connection.add_listener('message_edited', self.edit_callback)
        await self.connection.add_listener('message_deleted', self.delete_callback)
        await self.connection.add_listener('typing_indicator', self.typing_callback)
        await self.connection.add_listener('message_read', self.read_receipt_callback)
        await self.connection.add_listener('participant_added', self.participant_added_callback)
        await self.connection.add_listener('participant_removed', self.participant_removed_callback)
        self.listening = True
        print("PostgreSQL LISTEN started")
    
    async def message_callback(self, conn, pid, channel, payload):
        try:
            data = json.loads(payload)
            await manager.broadcast_to_conversation(
                {"type": "new_message", "data": data},
                data.get('conversation_id'),
                exclude_user=data.get('sender_id')
            )
        except Exception as e:
            print(f"Error: {e}")
    
    async def edit_callback(self, conn, pid, channel, payload):
        try:
            data = json.loads(payload)
            await manager.broadcast_to_conversation(
                {"type": "message_edited", "data": data},
                data.get('conversation_id')
            )
        except Exception as e:
            print(f"Error: {e}")
    
    async def delete_callback(self, conn, pid, channel, payload):
        try:
            data = json.loads(payload)
            await manager.broadcast_to_conversation(
                {"type": "message_deleted", "data": data},
                data.get('conversation_id')
            )
        except Exception as e:
            print(f"Error: {e}")
    
    async def typing_callback(self, conn, pid, channel, payload):
        try:
            data = json.loads(payload)
            await manager.broadcast_to_conversation(
                {"type": "typing_indicator", "data": data},
                data.get('conversation_id'),
                exclude_user=data.get('user_id')
            )
        except Exception as e:
            print(f"Error: {e}")
    
    async def read_receipt_callback(self, conn, pid, channel, payload):
        try:
            data = json.loads(payload)
            await manager.broadcast_to_conversation(
                {"type": "message_read", "data": data},
                data.get('conversation_id')
            )
        except Exception as e:
            print(f"Error: {e}")
    
    async def participant_added_callback(self, conn, pid, channel, payload):
        try:
            data = json.loads(payload)
            await manager.broadcast_to_conversation(
                {"type": "participant_added", "data": data},
                data.get('conversation_id')
            )
        except Exception as e:
            print(f"Error: {e}")
    
    async def participant_removed_callback(self, conn, pid, channel, payload):
        try:
            data = json.loads(payload)
            await manager.broadcast_to_conversation(
                {"type": "participant_removed", "data": data},
                data.get('conversation_id')
            )
        except Exception as e:
            print(f"Error: {e}")
    
    async def close(self):
        if self.connection:
            await self.connection.close()

postgres_notifier = PostgresNotifier()