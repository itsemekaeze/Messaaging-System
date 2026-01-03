# 🚀 Real-Time Messaging System

A production-ready, feature-rich real-time messaging system built with **FastAPI** and **PostgreSQL**. This system supports one-on-one chats, group conversations, media sharing, and advanced features like typing indicators, read receipts, and real-time notifications.

---

## ✨ Features

### 🔐 Authentication & User Management
- **JWT-based authentication** with secure password hashing (bcrypt)
- **User registration and login**
- **Profile management** (update display name, email)
- **Avatar uploads** (profile pictures)
- **User search** functionality
- **Soft delete** for user accounts
- **Online/offline status** tracking

### 💬 Messaging
- **Text messages** - Send and receive instant text messages
- **Media support** - Share images, videos, and files
- **Message editing** - Edit your own messages after sending
- **Message deletion** - Soft delete messages (shows "This message was deleted")
- **Message history** - Paginated message retrieval
- **Captions** - Add text descriptions to media files

### 👥 Conversations
- **One-on-one chats** - Direct messaging between two users
- **Group chats** - Multi-participant conversations
- **Group management**:
  - Create groups with custom names
  - Add/remove participants (admin only)
  - Leave group functionality
  - Role-based permissions (Admin/Member)
- **System messages** - Automatic notifications for group events
- **Unread message counts** - Track unread messages per conversation

### ⚡ Real-Time Features
- **WebSocket connections** - Instant message delivery
- **PostgreSQL LISTEN/NOTIFY** - Database-level pub/sub for scalability
- **Typing indicators** - See when others are typing
- **Read receipts** - Track who read each message
- **Online status** - Real-time user presence
- **Live updates** - Instant notifications for:
  - New messages
  - Message edits
  - Message deletions
  - Participants added/removed
  - Typing status changes

---

## 🏗️ Architecture

### Technology Stack
- **Backend Framework**: FastAPI (Python 3.8+)
- **Database**: PostgreSQL 12+
- **Authentication**: JWT (JSON Web Tokens)
- **Real-Time**: WebSockets + PostgreSQL NOTIFY
- **ORM**: SQLAlchemy
- **Password Hashing**: Bcrypt (via Passlib)

### Database Schema

```
Users
├── id (UUID)
├── username (unique)
├── email (unique)
├── hashed_password
├── display_name
├── avatar_url
├── is_online
├── is_active (soft delete)
└── last_seen

Conversations
├── id (UUID)
├── name (for groups)
├── is_group
├── created_by
├── avatar_url
└── timestamps

ConversationParticipants
├── conversation_id
├── user_id
├── role (admin/member)
├── last_read_at
├── is_active
└── joined_at

Messages
├── id (UUID)
├── conversation_id
├── sender_id
├── content
├── message_type (text/image/video/file/system)
├── file_url
├── file_name
├── file_size
├── is_edited
├── is_deleted
└── timestamps

MessageReadReceipts
├── message_id
├── user_id
└── read_at

TypingIndicators
├── conversation_id
├── user_id
└── started_at
```

### Real-Time Architecture

```
Client (WebSocket) ↔ FastAPI Server ↔ PostgreSQL
                         ↓
                    LISTEN/NOTIFY
                         ↓
                  Broadcast to Clients
```

1. Client sends message via REST API
2. Message saved to PostgreSQL
3. Database trigger fires NOTIFY event
4. FastAPI listener receives notification
5. Server broadcasts to connected WebSocket clients
6. Clients receive real-time updates

---

## 🚀 Installation

### Prerequisites
- Python 3.8+
- PostgreSQL 12+
- pip (Python package manager)

### Step 1: Clone the Repository
```bash
git clone <repository-url>
cd realtime-messaging-system
```

### Step 2: Install Dependencies
```bash
pip install fastapi uvicorn sqlalchemy psycopg2-binary asyncpg python-jose[cryptography] passlib[bcrypt] python-multipart
```

### Step 3: Setup PostgreSQL Database
```bash
# Create database
createdb messaging_db

# Or using psql
psql -U postgres
CREATE DATABASE messaging_db;
\q
```

### Step 4: Configure Environment
Edit the configuration section in `main.py`:

```python
DATABASE_URL = "postgresql://username:password@localhost/messaging_db"
ASYNC_DATABASE_URL = "postgresql://username:password@localhost/messaging_db"
SECRET_KEY = "your-super-secret-key-change-in-production"
```

### Step 5: Run the Server
```bash
uvicorn main:app --reload
```

The API will be available at: `http://localhost:8000`

API Documentation: `http://localhost:8000/docs`

---

## 📡 API Endpoints

### Authentication

#### Register User
```http
POST /auth/register
Content-Type: application/json

{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "secure_password123",
  "display_name": "John Doe"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": {
    "id": "uuid-here",
    "username": "john_doe",
    "email": "john@example.com",
    "display_name": "John Doe",
    "avatar_url": null,
    "is_online": false,
    "last_seen": "2024-01-03T10:00:00"
  }
}
```

#### Login
```http
POST /auth/login?username=john_doe&password=secure_password123
```

### User Management

#### Get Current User
```http
GET /users/me
Authorization: Bearer <token>
```

#### Update Profile
```http
PATCH /users/me
Authorization: Bearer <token>
Content-Type: application/json

{
  "display_name": "John Smith",
  "email": "newmail@example.com"
}
```

#### Upload Avatar
```http
POST /users/me/avatar
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: <image-file>
```

#### Search Users
```http
GET /users?query=john&limit=20
Authorization: Bearer <token>
```

#### Delete Account
```http
DELETE /users/me
Authorization: Bearer <token>
```

### Conversations

#### Create Conversation
```http
POST /conversations
Authorization: Bearer <token>
Content-Type: application/json

# One-on-one chat
{
  "participant_ids": ["user-id-2"],
  "is_group": false
}

# Group chat
{
  "participant_ids": ["user-id-2", "user-id-3", "user-id-4"],
  "name": "Team Chat",
  "is_group": true
}
```

#### Get All Conversations
```http
GET /conversations
Authorization: Bearer <token>
```

#### Get Specific Conversation
```http
GET /conversations/{conversation_id}
Authorization: Bearer <token>
```

#### Update Conversation (Admin Only)
```http
PATCH /conversations/{conversation_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Updated Group Name"
}
```

#### Add Participants (Admin Only)
```http
POST /conversations/{conversation_id}/participants
Authorization: Bearer <token>
Content-Type: application/json

{
  "user_ids": ["user-id-5", "user-id-6"]
}
```

#### Remove Participant (Admin Only)
```http
DELETE /conversations/{conversation_id}/participants/{user_id}
Authorization: Bearer <token>
```

#### Leave Conversation
```http
POST /conversations/{conversation_id}/leave
Authorization: Bearer <token>
```

### Messages

#### Send Text Message
```http
POST /messages
Authorization: Bearer <token>
Content-Type: application/json

{
  "conversation_id": "conv-id",
  "content": "Hello, world!"
}
```

#### Send Media Message
```http
POST /messages/upload?conversation_id={conv_id}&caption=Check this out!
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: <image/video/file>
```

#### Get Messages
```http
GET /conversations/{conversation_id}/messages?limit=50&before={message_id}
Authorization: Bearer <token>
```

#### Edit Message
```http
PATCH /messages/{message_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "content": "Updated message content"
}
```

#### Delete Message
```http
DELETE /messages/{message_id}
Authorization: Bearer <token>
```

#### Mark Message as Read
```http
POST /messages/{message_id}/read
Authorization: Bearer <token>
```

#### Send Typing Indicator
```http
POST /conversations/{conversation_id}/typing
Authorization: Bearer <token>
Content-Type: application/json

{
  "conversation_id": "conv-id",
  "is_typing": true
}
```

### WebSocket Connection

```javascript
const token = "your-jwt-token";
const ws = new WebSocket(`ws://localhost:8000/ws?token=${token}`);

ws.onopen = () => {
  console.log("Connected to WebSocket");
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log("Received:", data);
  
  // Handle different event types
  switch(data.type) {
    case "new_message":
      // New message received
      console.log("New message:", data.data);
      break;
    case "message_edited":
      // Message was edited
      console.log("Message edited:", data.data);
      break;
    case "message_deleted":
      // Message was deleted
      console.log("Message deleted:", data.data);
      break;
    case "typing_indicator":
      // User is typing
      console.log("User typing:", data.data);
      break;
    case "message_read":
      // Message was read
      console.log("Message read:", data.data);
      break;
    case "participant_added":
      // Participant added to group
      console.log("Participant added:", data.data);
      break;
    case "participant_removed":
      // Participant removed from group
      console.log("Participant removed:", data.data);
      break;
  }
};

ws.onerror = (error) => {
  console.error("WebSocket error:", error);
};

ws.onclose = () => {
  console.log("WebSocket disconnected");
};
```

---

## 📁 Project Structure

```
messaging-system/
├── main.py                 # Main application file
├── uploads/                # Uploaded files directory
│   ├── images/            # Image files
│   ├── videos/            # Video files
│   ├── files/             # Other file types
│   └── avatars/           # User avatars
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

---

## 🔒 Security Features

- **JWT Authentication** - Secure token-based authentication
- **Password Hashing** - Bcrypt with salting
- **SQL Injection Protection** - SQLAlchemy ORM prevents SQL injection
- **Authorization Checks** - Role-based access control
- **Soft Deletes** - Data preservation for audit trails
- **CORS Support** - Configurable cross-origin requests

---

## 🎯 Use Cases

- **Team Collaboration** - Internal company messaging
- **Customer Support** - Real-time customer service chat
- **Social Networking** - User-to-user messaging
- **Gaming** - In-game chat systems
- **Education** - Student-teacher communication
- **Healthcare** - Patient-doctor secure messaging

---

## 🚀 Deployment

### Production Considerations

1. **Environment Variables**
   - Store secrets in environment variables
   - Use `.env` file with `python-dotenv`

2. **Database**
   - Use connection pooling
   - Set up read replicas for scalability
   - Regular backups

3. **File Storage**
   - Use cloud storage (AWS S3, Google Cloud Storage)
   - Implement CDN for media delivery

4. **WebSocket Scaling**
   - Use Redis for pub/sub across multiple servers
   - Load balancing with sticky sessions

5. **Monitoring**
   - Log aggregation (ELK stack)
   - Error tracking (Sentry)
   - Performance monitoring (New Relic, DataDog)

### Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  db:
    image: postgres:14
    environment:
      POSTGRES_DB: messaging_db
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  api:
    build: .
    ports:
      - "8000:8000"
    depends_on:
      - db
    environment:
      DATABASE_URL: postgresql://postgres:password@db/messaging_db

volumes:
  postgres_data:
```

---

## 🧪 Testing

### Manual Testing with cURL

```bash
# Register user
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"test","email":"test@example.com","password":"pass123"}'

# Login
curl -X POST "http://localhost:8000/auth/login?username=test&password=pass123"

# Get conversations (with token)
curl -X GET http://localhost:8000/conversations \
  -H "Authorization: Bearer <your-token>"
```

### Using Swagger UI
Navigate to `http://localhost:8000/docs` for interactive API documentation and testing.

---

## 📊 Performance

- **PostgreSQL NOTIFY** - Efficient pub/sub without polling
- **WebSocket Persistence** - Long-lived connections for real-time updates
- **Indexed Queries** - Optimized database queries with proper indexes
- **Connection Pooling** - Efficient database connection management
- **Async Operations** - Non-blocking I/O for better concurrency

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License.

---

## 🐛 Known Issues

- File upload size limits not configured (add in production)
- No rate limiting on endpoints (implement for production)
- WebSocket reconnection logic should be handled client-side

---

## 🔮 Future Enhancements

- [ ] Message reactions (emojis)
- [ ] Voice messages
- [ ] Video calls (WebRTC integration)
- [ ] End-to-end encryption
- [ ] Message search functionality
- [ ] Push notifications (mobile)
- [ ] Message forwarding
- [ ] Pinned messages
- [ ] User blocking
- [ ] Message threading/replies
- [ ] File preview generation
- [ ] Admin dashboard
- [ ] Analytics and reporting

---

## 📞 Support

For questions or issues:
- Open an issue on GitHub
- Email: support@example.com
- Documentation: `http://localhost:8000/docs`

---

## 👥 Authors

- Your Name - Initial work

---

## 🙏 Acknowledgments

- FastAPI community
- PostgreSQL team
- SQLAlchemy contributors

---

**Built with ❤️ using FastAPI and PostgreSQL**