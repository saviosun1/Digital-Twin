# Digital Twin Backend

FastAPI backend for Digital Twin application.

## Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn main:app --reload
```

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry
│   ├── config.py            # Configuration settings
│   ├── database.py          # Database connection
│   ├── models/              # SQLAlchemy models
│   ├── routers/             # API route handlers
│   ├── services/            # Business logic
│   ├── schemas/             # Pydantic schemas
│   └── utils/               # Utility functions
├── tasks/                   # Celery tasks
├── tests/                   # Test files
├── alembic/                 # Database migrations
├── requirements.txt
└── Dockerfile
```

## API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - User login
- `POST /auth/refresh` - Refresh token

### Users
- `GET /users/me` - Get current user
- `PUT /users/me` - Update user profile
- `DELETE /users/me` - Delete account

### Avatars
- `POST /avatars` - Create new avatar
- `GET /avatars` - List user avatars
- `GET /avatars/{id}` - Get avatar details
- `PUT /avatars/{id}` - Update avatar
- `DELETE /avatars/{id}` - Delete avatar
- `POST /avatars/{id}/train` - Start training

### Questionnaire
- `GET /questions` - Get questions
- `POST /answers` - Submit answer
- `GET /progress/{avatar_id}` - Get completion progress

### Chat
- `POST /chat` - Create conversation
- `POST /chat/{id}/message` - Send message
- `GET /chat/{id}` - Get conversation history
- `WebSocket /ws/chat/{id}` - Real-time chat

### Scheduler
- `POST /scheduler` - Create scheduled message
- `GET /scheduler` - List scheduled messages
- `PUT /scheduler/{id}` - Update message
- `DELETE /scheduler/{id}` - Cancel message
