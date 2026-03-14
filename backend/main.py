import os
import json
import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from jose import JWTError, jwt
import bcrypt
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 常量
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 7
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
os.makedirs(DATA_DIR, exist_ok=True)

# 密码加密函数
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    try:
        # bcrypt checkpw expects bytes
        if isinstance(plain_password, str):
            plain_password = plain_password.encode('utf-8')
        if isinstance(hashed_password, str):
            hashed_password = hashed_password.encode('utf-8')
        return bcrypt.checkpw(plain_password, hashed_password)
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    """生成密码哈希 - bcrypt 限制 72 字节"""
    # bcrypt has a maximum password length of 72 bytes
    password_bytes = password.encode('utf-8')[:72]
    hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
    return hashed.decode('utf-8')

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

app = FastAPI(title="Digital Twin API", version="0.1.0")

# CORS
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://saviosun1.github.io",
    "https://saviosun1.github.io/Digital-Twin",
]
# 从环境变量读取额外允许的域名
allowed_origins = os.getenv("ALLOWED_ORIGINS", "")
if allowed_origins:
    origins.extend(allowed_origins.split(","))

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============== 数据文件操作 ==============

def get_users_file():
    return os.path.join(DATA_DIR, "users.json")

def get_avatar_file(avatar_id: str):
    return os.path.join(DATA_DIR, "avatars", f"{avatar_id}.json")

def get_avatar_dir(avatar_id: str):
    path = os.path.join(DATA_DIR, "avatars", avatar_id)
    os.makedirs(path, exist_ok=True)
    return path

def load_users():
    file_path = get_users_file()
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_users(users: dict):
    with open(get_users_file(), "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

def load_avatar(avatar_id: str):
    file_path = get_avatar_file(avatar_id)
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def save_avatar(avatar_id: str, data: dict):
    avatar_dir = os.path.join(DATA_DIR, "avatars")
    os.makedirs(avatar_dir, exist_ok=True)
    with open(get_avatar_file(avatar_id), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_questionnaire(avatar_id: str):
    file_path = os.path.join(get_avatar_dir(avatar_id), "questionnaire.json")
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_questionnaire(avatar_id: str, data: dict):
    with open(os.path.join(get_avatar_dir(avatar_id), "questionnaire.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ============== 认证相关 ==============

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    try:
        if isinstance(plain_password, str):
            plain_password = plain_password.encode('utf-8')
        if isinstance(hashed_password, str):
            hashed_password = hashed_password.encode('utf-8')
        return bcrypt.checkpw(plain_password, hashed_password)
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    """生成密码哈希 - bcrypt 限制 72 字节"""
    password_bytes = password.encode('utf-8')[:72]
    hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
    return hashed.decode('utf-8')

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    users = load_users()
    user = users.get(user_id)
    if user is None:
        raise credentials_exception
    return user

# ============== 数据模型 ==============

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str

class UserResponse(BaseModel):
    id: str
    email: str
    name: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class AvatarCreate(BaseModel):
    name: str

class AvatarResponse(BaseModel):
    id: str
    name: str
    user_id: str
    status: str
    created_at: str

class QuestionAnswer(BaseModel):
    question_id: str
    question: str
    answer: str
    category: str

class ChatRequest(BaseModel):
    message: str
    avatar_id: str

class ChatResponse(BaseModel):
    response: str

# ============== API 路由 ==============

@app.get("/")
def root():
    return {"message": "Digital Twin API", "version": "0.1.0"}

@app.get("/health")
def health():
    return {"status": "ok"}

# 认证
@app.post("/auth/register", response_model=UserResponse)
def register(user: UserCreate):
    users = load_users()
    
    # 检查邮箱是否已存在
    for existing_user in users.values():
        if existing_user["email"] == user.email:
            raise HTTPException(status_code=400, detail="Email already registered")
    
    user_id = str(uuid.uuid4())
    user_data = {
        "id": user_id,
        "email": user.email,
        "password_hash": get_password_hash(user.password),
        "name": user.name,
        "created_at": datetime.utcnow().isoformat()
    }
    
    users[user_id] = user_data
    save_users(users)
    
    return {"id": user_id, "email": user.email, "name": user.name}

@app.post("/auth/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    users = load_users()
    
    user = None
    for u in users.values():
        if u["email"] == form_data.username:
            user = u
            break
    
    if not user or not verify_password(form_data.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user["id"]})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=UserResponse)
def get_me(current_user: dict = Depends(get_current_user)):
    return {
        "id": current_user["id"],
        "email": current_user["email"],
        "name": current_user["name"]
    }

# 分身管理
@app.post("/avatars", response_model=AvatarResponse)
def create_avatar(avatar: AvatarCreate, current_user: dict = Depends(get_current_user)):
    avatar_id = str(uuid.uuid4())
    avatar_data = {
        "id": avatar_id,
        "name": avatar.name,
        "user_id": current_user["id"],
        "status": "draft",
        "created_at": datetime.utcnow().isoformat()
    }
    save_avatar(avatar_id, avatar_data)
    
    return AvatarResponse(
        id=avatar_id,
        name=avatar.name,
        user_id=current_user["id"],
        status="draft",
        created_at=avatar_data["created_at"]
    )

@app.get("/avatars", response_model=List[AvatarResponse])
def list_avatars(current_user: dict = Depends(get_current_user)):
    avatars_dir = os.path.join(DATA_DIR, "avatars")
    if not os.path.exists(avatars_dir):
        return []
    
    avatars = []
    for filename in os.listdir(avatars_dir):
        if filename.endswith(".json"):
            avatar = load_avatar(filename[:-5])
            if avatar and avatar.get("user_id") == current_user["id"]:
                avatars.append(AvatarResponse(
                    id=avatar["id"],
                    name=avatar["name"],
                    user_id=avatar["user_id"],
                    status=avatar.get("status", "draft"),
                    created_at=avatar["created_at"]
                ))
    return avatars

@app.get("/avatars/{avatar_id}", response_model=AvatarResponse)
def get_avatar(avatar_id: str, current_user: dict = Depends(get_current_user)):
    avatar = load_avatar(avatar_id)
    if not avatar or avatar["user_id"] != current_user["id"]:
        raise HTTPException(status_code=404, detail="Avatar not found")
    
    return AvatarResponse(
        id=avatar["id"],
        name=avatar["name"],
        user_id=avatar["user_id"],
        status=avatar.get("status", "draft"),
        created_at=avatar["created_at"]
    )

# 问卷
@app.get("/questions")
def get_questions():
    """获取问卷问题列表"""
    return [
        {"id": "name", "category": "basic", "question": "你的全名是什么？"},
        {"id": "birth", "category": "basic", "question": "你的出生日期和出生地？"},
        {"id": "occupation", "category": "basic", "question": "你的职业是什么？"},
        {"id": "personality", "category": "personality", "question": "用三个词形容你的性格"},
        {"id": "strength", "category": "personality", "question": "你最大的优点是什么？"},
        {"id": "fav_food", "category": "preferences", "question": "你最爱吃的一道菜是什么？"},
        {"id": "fav_music", "category": "preferences", "question": "最喜欢的音乐或歌手？"},
        {"id": "important_person", "category": "relationships", "question": "你生命中最重要的人是谁？"},
        {"id": "proud_moment", "category": "life", "question": "你最骄傲的时刻是什么？"},
        {"id": "life_advice", "category": "values", "question": "给年轻时的自己一个建议？"},
    ]

@app.post("/avatars/{avatar_id}/answers")
def save_answer(avatar_id: str, answer: QuestionAnswer, current_user: dict = Depends(get_current_user)):
    """保存问卷答案"""
    avatar = load_avatar(avatar_id)
    if not avatar or avatar["user_id"] != current_user["id"]:
        raise HTTPException(status_code=404, detail="Avatar not found")
    
    questionnaire = load_questionnaire(avatar_id)
    questionnaire[answer.question_id] = {
        "question": answer.question,
        "answer": answer.answer,
        "category": answer.category,
        "updated_at": datetime.utcnow().isoformat()
    }
    save_questionnaire(avatar_id, questionnaire)
    
    return {"message": "Answer saved"}

@app.get("/avatars/{avatar_id}/questionnaire")
def get_questionnaire(avatar_id: str, current_user: dict = Depends(get_current_user)):
    """获取问卷进度"""
    avatar = load_avatar(avatar_id)
    if not avatar or avatar["user_id"] != current_user["id"]:
        raise HTTPException(status_code=404, detail="Avatar not found")
    
    questionnaire = load_questionnaire(avatar_id)
    questions = get_questions()
    
    return {
        "avatar_id": avatar_id,
        "total": len(questions),
        "answered": len(questionnaire),
        "progress": len(questionnaire) / len(questions) if questions else 0,
        "answers": questionnaire
    }

# 对话
@app.post("/chat")
def chat(request: ChatRequest, current_user: dict = Depends(get_current_user)):
    """与数字分身对话"""
    avatar = load_avatar(request.avatar_id)
    if not avatar:
        raise HTTPException(status_code=404, detail="Avatar not found")
    
    # 加载问卷数据用于构建人格
    questionnaire = load_questionnaire(request.avatar_id)
    
    # 构建简单的人格描述
    persona = f"你是{avatar['name']}的数字分身。"
    if questionnaire:
        answers = [f"Q: {q['question']}\nA: {q['answer']}" for q in questionnaire.values()]
        persona += "\n\n以下是关于你的一些信息：\n" + "\n".join(answers[:5])
    
    # TODO: 集成 Kimi API
    # 暂时返回模拟回复
    response = f"[这是{avatar['name']}的分身] 我收到了你的消息：\"{request.message[:50]}...\"\n\n（注意：原型版本，尚未接入 AI 对话）"
    
    # 保存聊天记录
    conv_dir = os.path.join(get_avatar_dir(request.avatar_id), "conversations")
    os.makedirs(conv_dir, exist_ok=True)
    conv_file = os.path.join(conv_dir, f"{datetime.now().strftime('%Y%m%d')}.json")
    
    conversation = []
    if os.path.exists(conv_file):
        with open(conv_file, "r", encoding="utf-8") as f:
            conversation = json.load(f)
    
    conversation.append({
        "timestamp": datetime.utcnow().isoformat(),
        "user": request.message,
        "assistant": response
    })
    
    with open(conv_file, "w", encoding="utf-8") as f:
        json.dump(conversation, f, ensure_ascii=False, indent=2)
    
    return ChatResponse(response=response)

# 启动
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
