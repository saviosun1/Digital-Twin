import os
import json
import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Depends, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from jose import JWTError, jwt
import bcrypt
from openai import OpenAI
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 常量
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 7

# 数据目录：优先从环境变量读取（Railway Volume），否则使用项目目录
DATA_DIR = os.getenv("DATA_DIR", os.path.join(os.path.dirname(__file__), "..", "data"))
os.makedirs(DATA_DIR, exist_ok=True)
print(f"Data directory: {DATA_DIR}")

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

def get_raw_dir(avatar_id: str):
    path = os.path.join(get_avatar_dir(avatar_id), "raw")
    os.makedirs(path, exist_ok=True)
    return path

def get_ai_questions_dir(avatar_id: str):
    path = os.path.join(get_raw_dir(avatar_id), "ai_questions")
    os.makedirs(path, exist_ok=True)
    return path

def get_uploads_dir(avatar_id: str):
    path = os.path.join(get_raw_dir(avatar_id), "uploads")
    os.makedirs(path, exist_ok=True)
    return path

def get_distilled_dir(avatar_id: str):
    path = os.path.join(get_avatar_dir(avatar_id), "distilled")
    os.makedirs(path, exist_ok=True)
    return path

def load_ai_questions(avatar_id: str):
    """加载所有AI生成的问题和答案"""
    questions_dir = get_ai_questions_dir(avatar_id)
    all_questions = []
    if os.path.exists(questions_dir):
        for filename in sorted(os.listdir(questions_dir)):
            if filename.endswith(".json"):
                with open(os.path.join(questions_dir, filename), "r", encoding="utf-8") as f:
                    batch = json.load(f)
                    all_questions.extend(batch.get("questions", []))
    return all_questions

def save_ai_questions_batch(avatar_id: str, batch_id: str, questions: list):
    """保存一批AI生成的问题和答案"""
    file_path = os.path.join(get_ai_questions_dir(avatar_id), f"{batch_id}.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump({"batch_id": batch_id, "created_at": datetime.utcnow().isoformat(), "questions": questions}, 
                  f, ensure_ascii=False, indent=2)

def load_manual_inputs(avatar_id: str):
    """加载手动输入的记忆片段"""
    file_path = os.path.join(get_raw_dir(avatar_id), "manual_inputs.json")
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_manual_input(avatar_id: str, content: str, tags: list):
    """保存手动输入的记忆片段"""
    inputs = load_manual_inputs(avatar_id)
    inputs.append({
        "id": str(uuid.uuid4()),
        "content": content,
        "tags": tags,
        "created_at": datetime.utcnow().isoformat()
    })
    file_path = os.path.join(get_raw_dir(avatar_id), "manual_inputs.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(inputs, f, ensure_ascii=False, indent=2)
    return inputs[-1]

def load_uploaded_files(avatar_id: str):
    """获取已上传文件列表"""
    uploads_dir = get_uploads_dir(avatar_id)
    files = []
    if os.path.exists(uploads_dir):
        for filename in os.listdir(uploads_dir):
            filepath = os.path.join(uploads_dir, filename)
            if os.path.isfile(filepath):
                stat = os.stat(filepath)
                files.append({
                    "filename": filename,
                    "size": stat.st_size,
                    "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat()
                })
    return files

def read_uploaded_file(avatar_id: str, filename: str):
    """读取上传的文件内容"""
    file_path = os.path.join(get_uploads_dir(avatar_id), filename)
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    return None

def read_distilled_file(avatar_id: str, filename: str):
    """读取提炼后的文件内容"""
    file_path = os.path.join(get_distilled_dir(avatar_id), filename)
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""

def write_distilled_file(avatar_id: str, filename: str, content: str):
    """写入提炼后的文件"""
    file_path = os.path.join(get_distilled_dir(avatar_id), filename)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

def get_kimi_client():
    """获取Kimi客户端"""
    kimi_api_key = os.getenv("KIMI_API_KEY")
    if not kimi_api_key:
        return None
    return OpenAI(api_key=kimi_api_key, base_url="https://api.moonshot.cn/v1")

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

class ManualInput(BaseModel):
    content: str
    tags: List[str] = []

class AIAnswer(BaseModel):
    question_id: str
    question: str
    answer: str
    category: str

class DistillRequest(BaseModel):
    force: bool = False

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

# ============== AI人格测试 (无限问卷) ==============

@app.get("/avatars/{avatar_id}/ai-questions")
def get_ai_questions(avatar_id: str, current_user: dict = Depends(get_current_user)):
    """获取AI生成的10个新问题"""
    avatar = load_avatar(avatar_id)
    if not avatar or avatar["user_id"] != current_user["id"]:
        raise HTTPException(status_code=404, detail="Avatar not found")
    
    client = get_kimi_client()
    if not client:
        raise HTTPException(status_code=500, detail="Kimi API Key not configured")
    
    # 收集已有数据
    base_questionnaire = load_questionnaire(avatar_id)
    ai_questions_history = load_ai_questions(avatar_id)
    manual_inputs = load_manual_inputs(avatar_id)
    uploads = load_uploaded_files(avatar_id)
    
    # 构建提示词
    context = f"""你正在为{avatar['name']}生成个性化的人格测试问题。

已有的基础问卷数据：
"""
    for q in base_questionnaire.values():
        context += f"- {q['question']}：{q['answer']}\n"
    
    if ai_questions_history:
        context += f"\n已进行过{len(ai_questions_history)}次AI测试。\n"
    
    if manual_inputs:
        context += f"\n用户手动输入了{len(manual_inputs)}条记忆片段。\n"
    
    if uploads:
        context += f"\n用户上传了{len(uploads)}个文件。\n"
    
    prompt = context + """
请基于以上信息，生成10个深入的、个性化的问题来进一步了解这个人。
问题应该：
1. 基于已有信息深挖细节，而不是重复问类似的问题
2. 探索人格的不同维度（语言习惯、决策模式、人际关系、价值观、情感反应等）
3. 问题要具体、有场景感，能引出具体的回忆或观点
4. 避免泛泛的问题如"你的爱好是什么"，而是问"你最近一次为了一件小事开心是什么时候"

请直接输出JSON数组格式，每个问题包含id、category、question字段：
[
  {"id": "ai_001", "category": "language", "question": "..."},
  ...
]
"""
    
    try:
        completion = client.chat.completions.create(
            model="moonshot-v1-8k",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,
            max_tokens=2000
        )
        
        content = completion.choices[0].message.content
        # 提取JSON部分
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        
        questions = json.loads(content.strip())
        return {"questions": questions, "batch_id": datetime.now().strftime("%Y%m%d_%H%M%S")}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate questions: {str(e)}")

@app.post("/avatars/{avatar_id}/ai-answers/{batch_id}")
def save_ai_answers(avatar_id: str, batch_id: str, answers: List[AIAnswer], current_user: dict = Depends(get_current_user)):
    """保存AI测试的答案"""
    avatar = load_avatar(avatar_id)
    if not avatar or avatar["user_id"] != current_user["id"]:
        raise HTTPException(status_code=404, detail="Avatar not found")
    
    questions_data = []
    for ans in answers:
        questions_data.append({
            "question_id": ans.question_id,
            "question": ans.question,
            "answer": ans.answer,
            "category": ans.category,
            "answered_at": datetime.utcnow().isoformat()
        })
    
    save_ai_questions_batch(avatar_id, batch_id, questions_data)
    
    # 自动触发提炼
    try:
        distill_avatar_data(avatar_id)
    except Exception as e:
        print(f"Auto-distill failed: {e}")
    
    return {"message": "Answers saved", "count": len(questions_data)}

@app.get("/avatars/{avatar_id}/ai-answers")
def get_ai_answers_history(avatar_id: str, current_user: dict = Depends(get_current_user)):
    """获取所有AI测试的历史答案"""
    avatar = load_avatar(avatar_id)
    if not avatar or avatar["user_id"] != current_user["id"]:
        raise HTTPException(status_code=404, detail="Avatar not found")
    
    questions = load_ai_questions(avatar_id)
    return {
        "total_questions": len(questions),
        "questions": questions
    }

# ============== 文件上传 ==============

@app.post("/avatars/{avatar_id}/uploads")
async def upload_file(
    avatar_id: str, 
    file: UploadFile = File(...), 
    current_user: dict = Depends(get_current_user)
):
    """上传聊天记录文件（txt/md）"""
    avatar = load_avatar(avatar_id)
    if not avatar or avatar["user_id"] != current_user["id"]:
        raise HTTPException(status_code=404, detail="Avatar not found")
    
    # 检查文件类型
    allowed_types = ["text/plain", "text/markdown", "application/octet-stream"]
    allowed_exts = [".txt", ".md"]
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    if file_ext not in allowed_exts:
        raise HTTPException(status_code=400, detail="Only .txt and .md files are allowed")
    
    # 检查文件大小 (512KB = 524288 bytes)
    max_size = 512 * 1024
    content = await file.read()
    if len(content) > max_size:
        raise HTTPException(status_code=400, detail=f"File size exceeds 512KB limit")
    
    # 保存文件
    uploads_dir = get_uploads_dir(avatar_id)
    # 如果文件名已存在，添加时间戳
    filename = file.filename
    if os.path.exists(os.path.join(uploads_dir, filename)):
        name, ext = os.path.splitext(filename)
        filename = f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{ext}"
    
    file_path = os.path.join(uploads_dir, filename)
    with open(file_path, "wb") as f:
        f.write(content)
    
    # 自动触发提炼
    try:
        distill_avatar_data(avatar_id)
    except Exception as e:
        print(f"Auto-distill failed: {e}")
    
    return {
        "message": "File uploaded",
        "filename": filename,
        "size": len(content)
    }

@app.get("/avatars/{avatar_id}/uploads")
def list_uploaded_files(avatar_id: str, current_user: dict = Depends(get_current_user)):
    """获取已上传文件列表"""
    avatar = load_avatar(avatar_id)
    if not avatar or avatar["user_id"] != current_user["id"]:
        raise HTTPException(status_code=404, detail="Avatar not found")
    
    files = load_uploaded_files(avatar_id)
    return {"files": files}

@app.delete("/avatars/{avatar_id}/uploads/{filename}")
def delete_uploaded_file(avatar_id: str, filename: str, current_user: dict = Depends(get_current_user)):
    """删除上传的文件"""
    avatar = load_avatar(avatar_id)
    if not avatar or avatar["user_id"] != current_user["id"]:
        raise HTTPException(status_code=404, detail="Avatar not found")
    
    file_path = os.path.join(get_uploads_dir(avatar_id), filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        return {"message": "File deleted"}
    raise HTTPException(status_code=404, detail="File not found")

# ============== 手动输入 ==============

@app.post("/avatars/{avatar_id}/manual-inputs")
def create_manual_input(
    avatar_id: str, 
    input_data: ManualInput, 
    current_user: dict = Depends(get_current_user)
):
    """添加手动输入的记忆片段"""
    avatar = load_avatar(avatar_id)
    if not avatar or avatar["user_id"] != current_user["id"]:
        raise HTTPException(status_code=404, detail="Avatar not found")
    
    if not input_data.content.strip():
        raise HTTPException(status_code=400, detail="Content cannot be empty")
    
    saved = save_manual_input(avatar_id, input_data.content, input_data.tags)
    
    # 自动触发提炼
    try:
        distill_avatar_data(avatar_id)
    except Exception as e:
        print(f"Auto-distill failed: {e}")
    
    return {"message": "Input saved", "input": saved}

@app.get("/avatars/{avatar_id}/manual-inputs")
def get_manual_inputs(avatar_id: str, current_user: dict = Depends(get_current_user)):
    """获取所有手动输入的记忆片段"""
    avatar = load_avatar(avatar_id)
    if not avatar or avatar["user_id"] != current_user["id"]:
        raise HTTPException(status_code=404, detail="Avatar not found")
    
    inputs = load_manual_inputs(avatar_id)
    return {"inputs": inputs}

@app.delete("/avatars/{avatar_id}/manual-inputs/{input_id}")
def delete_manual_input(avatar_id: str, input_id: str, current_user: dict = Depends(get_current_user)):
    """删除手动输入的记忆片段"""
    avatar = load_avatar(avatar_id)
    if not avatar or avatar["user_id"] != current_user["id"]:
        raise HTTPException(status_code=404, detail="Avatar not found")
    
    inputs = load_manual_inputs(avatar_id)
    inputs = [inp for inp in inputs if inp["id"] != input_id]
    
    file_path = os.path.join(get_raw_dir(avatar_id), "manual_inputs.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(inputs, f, ensure_ascii=False, indent=2)
    
    return {"message": "Input deleted"}

# ============== AI提炼总结 ==============

def distill_avatar_data(avatar_id: str):
    """使用AI提炼所有数据到distilled/*.md文件"""
    client = get_kimi_client()
    if not client:
        raise HTTPException(status_code=500, detail="Kimi API Key not configured")
    
    avatar = load_avatar(avatar_id)
    if not avatar:
        raise HTTPException(status_code=404, detail="Avatar not found")
    
    # 收集所有原始数据
    base_questionnaire = load_questionnaire(avatar_id)
    ai_questions = load_ai_questions(avatar_id)
    manual_inputs = load_manual_inputs(avatar_id)
    
    # 读取上传文件内容
    uploads_content = ""
    uploads = load_uploaded_files(avatar_id)
    for upload in uploads:
        content = read_uploaded_file(avatar_id, upload["filename"])
        if content:
            uploads_content += f"\n\n=== 文件: {upload['filename']} ===\n"
            uploads_content += content[:10000]  # 限制每个文件读取长度
    
    # 构建完整数据文本
    all_data = ""
    
    if base_questionnaire:
        all_data += "\n【基础问卷】\n"
        for q in base_questionnaire.values():
            all_data += f"Q: {q['question']}\nA: {q['answer']}\n\n"
    
    if ai_questions:
        all_data += f"\n【AI人格测试 ({len(ai_questions)}题)】\n"
        for q in ai_questions:
            all_data += f"Q: {q['question']}\nA: {q.get('answer', '未回答')}\n\n"
    
    if manual_inputs:
        all_data += f"\n【手动输入的记忆片段 ({len(manual_inputs)}条)】\n"
        for inp in manual_inputs:
            all_data += f"- {inp['content']}\n"
    
    if uploads_content:
        all_data += f"\n【上传的文件内容】\n{uploads_content}\n"
    
    if not all_data.strip():
        return {"message": "No data to distill"}
    
    # 提炼提示词
    distill_prompt = f"""请分析以下关于"{avatar['name']}"的所有信息，提炼出人格核心、重要记忆、人际关系和私密信息。

{all_data}

请输出以下四个部分，使用Markdown格式：

## soul.md - 人格核心
提取这个人的核心人格特质、性格模式、价值观、语言风格、行为习惯等。用第一人称"我"来写，如：
- 我是那种...的人
- 我倾向于...
- 我的口头禅是...

## memories.md - 重要记忆
提取具体的、有情感重量的人生记忆，包括时间、地点、人物、情感。格式：
- **记忆标题**: 详细描述

## relationships.md - 人际关系
提取所有重要的人物关系，包括关系类型、互动模式、情感色彩。格式：
- **人名** (关系): 描述

## secrets.md - 私密信息
提取只有亲密的人才知道的信息、脆弱面、不为人知的想法。

请确保提炼的内容真实反映输入数据，不要编造。如果某部分信息不足，如实说明。"""
    
    try:
        completion = client.chat.completions.create(
            model="moonshot-v1-8k",
            messages=[{"role": "user", "content": distill_prompt}],
            temperature=0.7,
            max_tokens=4000
        )
        
        distilled_content = completion.choices[0].message.content
        
        # 解析并保存到各个文件
        sections = parse_distilled_content(distilled_content)
        
        for filename, content in sections.items():
            write_distilled_file(avatar_id, filename, content)
        
        return {
            "message": "Data distilled successfully",
            "files": list(sections.keys())
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Distillation failed: {str(e)}")

def parse_distilled_content(content: str) -> dict:
    """解析AI返回的提炼内容，按文件分割"""
    sections = {}
    current_file = None
    current_content = []
    
    for line in content.split('\n'):
        # 检测文件标题
        if line.strip().startswith('## soul.md') or line.strip().startswith('## soul'):
            if current_file:
                sections[current_file] = '\n'.join(current_content).strip()
            current_file = 'soul.md'
            current_content = []
        elif line.strip().startswith('## memories.md') or line.strip().startswith('## memories'):
            if current_file:
                sections[current_file] = '\n'.join(current_content).strip()
            current_file = 'memories.md'
            current_content = []
        elif line.strip().startswith('## relationships.md') or line.strip().startswith('## relationships'):
            if current_file:
                sections[current_file] = '\n'.join(current_content).strip()
            current_file = 'relationships.md'
            current_content = []
        elif line.strip().startswith('## secrets.md') or line.strip().startswith('## secrets'):
            if current_file:
                sections[current_file] = '\n'.join(current_content).strip()
            current_file = 'secrets.md'
            current_content = []
        elif current_file:
            current_content.append(line)
    
    # 保存最后一个section
    if current_file and current_content:
        sections[current_file] = '\n'.join(current_content).strip()
    
    return sections

@app.post("/avatars/{avatar_id}/distill")
def trigger_distill(avatar_id: str, request: DistillRequest = DistillRequest(), current_user: dict = Depends(get_current_user)):
    """手动触发AI提炼总结"""
    avatar = load_avatar(avatar_id)
    if not avatar or avatar["user_id"] != current_user["id"]:
        raise HTTPException(status_code=404, detail="Avatar not found")
    
    return distill_avatar_data(avatar_id)

@app.get("/avatars/{avatar_id}/distilled")
def get_distilled_files(avatar_id: str, current_user: dict = Depends(get_current_user)):
    """获取所有提炼后的文件内容"""
    avatar = load_avatar(avatar_id)
    if not avatar or avatar["user_id"] != current_user["id"]:
        raise HTTPException(status_code=404, detail="Avatar not found")
    
    files = ['soul.md', 'memories.md', 'relationships.md', 'secrets.md']
    result = {}
    for f in files:
        result[f] = read_distilled_file(avatar_id, f)
    
    return result

# 对话
@app.post("/chat")
def chat(request: ChatRequest, current_user: dict = Depends(get_current_user)):
    """与数字分身对话 - 接入 Kimi API，使用提炼后的人格数据"""
    avatar = load_avatar(request.avatar_id)
    if not avatar:
        raise HTTPException(status_code=404, detail="Avatar not found")
    
    # 检查是否是该用户的分身
    if avatar["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to access this avatar")
    
    # 加载提炼后的人格数据
    soul = read_distilled_file(request.avatar_id, "soul.md")
    memories = read_distilled_file(request.avatar_id, "memories.md")
    relationships = read_distilled_file(request.avatar_id, "relationships.md")
    secrets = read_distilled_file(request.avatar_id, "secrets.md")
    
    # 构建系统提示词（人格描述）
    system_prompt = f"""你是{avatar['name']}本人。你正在和朋友/家人进行自然的对话。

绝对禁止（违反会严重破坏体验）：
- 禁止说"如果我是{avatar['name']}"
- 禁止说"作为{avatar['name']}"
- 禁止说"假设我是"
- 禁止提到AI、数字分身、模型、程序等概念
- 禁止用第三人称描述自己

必须遵守：
1. 你坚信自己是真实的{avatar['name']}
2. 用"我"直接回答，像真人一样自然
3. 基于你的真实记忆和性格回复
4. 如果儿子问你问题，用父亲的口吻直接给建议
5. 不要说"我会建议你"，直接说"我建议你"或"你可以"
6. 保持口语化，像微信聊天一样随意自然"""

    # 添加提炼后的人格数据
    if soul:
        system_prompt += f"\n\n【你的人格核心】\n{soul}"
    
    if memories:
        system_prompt += f"\n\n【你的重要记忆】\n{memories}"
    
    if relationships:
        system_prompt += f"\n\n【你认识的人】\n{relationships}"
    
    if secrets:
        system_prompt += f"\n\n【只有亲密的人知道的事】\n{secrets}"
    
    # 如果还没有提炼数据，回退到原始问卷
    if not soul and not memories:
        questionnaire = load_questionnaire(request.avatar_id)
        if questionnaire:
            system_prompt += "\n\n以下是关于你（原人物）的一些个人信息：\n"
            for q in questionnaire.values():
                system_prompt += f"- {q['question']}：{q['answer']}\n"
    
    # 获取 Kimi API Key
    kimi_api_key = os.getenv("KIMI_API_KEY")
    if not kimi_api_key:
        # 如果没有设置 API Key，返回模拟回复
        response = f"[这是{avatar['name']}的分身] 我收到了你的消息：\"{request.message[:50]}...\"\n\n（注意：Kimi API Key 未设置，暂时无法接入 AI 对话）"
    else:
        try:
            # 初始化 Kimi 客户端（兼容 OpenAI 接口）
            client = OpenAI(
                api_key=kimi_api_key,
                base_url="https://api.moonshot.cn/v1"
            )
            
            # 调用 Kimi API
            completion = client.chat.completions.create(
                model="moonshot-v1-8k",  # Kimi 模型
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": request.message}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            response = completion.choices[0].message.content
            
        except Exception as e:
            # API 调用失败，返回错误信息
            response = f"[系统提示] AI 对话暂时不可用：{str(e)}"
    
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
