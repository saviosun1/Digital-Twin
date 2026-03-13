# 技术架构文档 - Digital Twin

## 1. 系统架构概览

```
┌─────────────────────────────────────────────────────────────┐
│                         客户端层                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   Web App   │  │  Mobile Web │  │   WeChat MiniApp    │ │
│  │  (React)    │  │  (PWA)      │  │    (Future)         │ │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘ │
└─────────┼────────────────┼────────────────────┼────────────┘
          │                │                    │
          └────────────────┴────────────────────┘
                           │
                    ┌──────▼──────┐
                    │   Nginx     │
                    │   (Proxy)   │
                    └──────┬──────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                      API Gateway                            │
│         (Rate Limiting, Auth, Load Balancing)               │
└──────────────────────────┬──────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
┌───────▼──────┐  ┌────────▼────────┐  ┌──────▼───────┐
│   REST API   │  │   WebSocket     │  │   Webhook    │
│   (HTTP)     │  │   (Real-time)   │  │   (External) │
└───────┬──────┘  └────────┬────────┘  └──────┬───────┘
        │                  │                  │
        └──────────────────┼──────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                    应用服务层 (FastAPI)                      │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐ │
│  │  User Service│ │ Avatar Service│ │  Scheduler Service  │ │
│  └──────────────┘ └──────────────┘ └──────────────────────┘ │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐ │
│  │ Chat Service │ │ Memory Service│ │ Notification Service│ │
│  └──────────────┘ └──────────────┘ └──────────────────────┘ │
└──────────────────────────┬──────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
┌───────▼──────┐  ┌────────▼────────┐  ┌──────▼───────┐
│    PostgreSQL │  │     Redis       │  │   ChromaDB   │
│  (Relational) │  │  (Cache/Queue)  │  │  (Vector DB) │
└───────────────┘  └─────────────────┘  └──────────────┘
        │                  │                  │
        └──────────────────┼──────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                     AI 服务层                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              LLM API (Kimi/OpenAI)                   │  │
│  │   - Persona Generation    - Conversation             │  │
│  │   - Memory Extraction     - Style Transfer           │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │            Voice Service (Optional)                  │  │
│  │   - TTS (Text-to-Speech)  - Voice Cloning            │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## 2. 数据模型

### 2.1 核心实体关系

```
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│    User     │───┐   │   Avatar    │◄──────┤   Memory    │
│  (创建者)   │   │   │  (数字分身) │       │   (记忆)    │
└─────────────┘   │   └─────────────┘       └─────────────┘
       │          │          │
       │          │   ┌──────┴──────┐
       │          │   │             │
       ▼          ▼   ▼             ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│   Visitor   │  │ Personality │  │  Schedule   │
│  (访客授权)  │  │  (人格模型)  │  │  (定时任务)  │
└─────────────┘  └─────────────┘  └─────────────┘
```

### 2.2 数据库 Schema

```sql
-- 用户表
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20),
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(100) NOT NULL,
    avatar_url TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 数字分身表
CREATE TABLE avatars (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    status VARCHAR(20) DEFAULT 'draft', -- draft, training, ready, archived
    config JSONB DEFAULT '{}',
    personality_vector_id VARCHAR(100), -- ChromaDB ID
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 问答数据表
CREATE TABLE questionnaire_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    avatar_id UUID REFERENCES avatars(id) ON DELETE CASCADE,
    category VARCHAR(50) NOT NULL, -- personality, preferences, life_events, etc.
    question TEXT NOT NULL,
    answer TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 记忆片段表（用于RAG）
CREATE TABLE memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    avatar_id UUID REFERENCES avatars(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    memory_type VARCHAR(30), -- fact, story, preference, relationship
    source VARCHAR(50), -- questionnaire, upload, conversation
    embedding_id VARCHAR(100), -- ChromaDB ID
    importance_score FLOAT DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 访客授权表
CREATE TABLE visitor_permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    avatar_id UUID REFERENCES avatars(id) ON DELETE CASCADE,
    visitor_email VARCHAR(255) NOT NULL,
    access_level VARCHAR(20) DEFAULT 'chat', -- chat, restricted, full
    allowed_from TIMESTAMP, -- 何时开始可以访问
    allowed_until TIMESTAMP, -- 访问截止时间
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 定时任务表
CREATE TABLE scheduled_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    avatar_id UUID REFERENCES avatars(id) ON DELETE CASCADE,
    recipient_email VARCHAR(255) NOT NULL,
    trigger_type VARCHAR(30), -- fixed_date, relative_date, condition
    trigger_config JSONB NOT NULL, -- 触发条件配置
    message_content TEXT,
    message_type VARCHAR(20) DEFAULT 'text', -- text, voice, video
    status VARCHAR(20) DEFAULT 'pending', -- pending, sent, failed, cancelled
    scheduled_at TIMESTAMP,
    sent_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 对话记录表
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    avatar_id UUID REFERENCES avatars(id) ON DELETE CASCADE,
    visitor_id VARCHAR(255), -- 匿名或已识别访客
    messages JSONB DEFAULT '[]',
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP
);
```

## 3. 服务模块设计

### 3.1 User Service
```python
class UserService:
    - register(email, password, name)
    - login(email, password)
    - update_profile(user_id, data)
    - change_password(user_id, old_pwd, new_pwd)
    - delete_account(user_id)
```

### 3.2 Avatar Service
```python
class AvatarService:
    - create_avatar(user_id, name, config)
    - update_avatar(avatar_id, data)
    - get_avatar(avatar_id)
    - list_user_avatars(user_id)
    - train_avatar(avatar_id)  # 触发训练流程
    - get_training_status(avatar_id)
    - delete_avatar(avatar_id)
```

### 3.3 Questionnaire Service
```python
class QuestionnaireService:
    - get_questions(category=None)  # 获取问题列表
    - save_answer(avatar_id, question_id, answer)
    - get_progress(avatar_id)  # 完成进度
    - generate_dynamic_questions(avatar_id)  # AI生成追问
```

### 3.4 Chat Service
```python
class ChatService:
    - create_conversation(avatar_id, visitor_id)
    - send_message(conversation_id, message)
    - get_conversation_history(conversation_id)
    - end_conversation(conversation_id)
    
    # 核心：生成回复
    async def generate_response(avatar_id, message, context):
        # 1. 检索相关记忆
        memories = memory_service.retrieve(avatar_id, message)
        # 2. 构建人格prompt
        persona = personality_service.get_persona(avatar_id)
        # 3. 调用LLM生成
        response = await llm.generate(persona, memories, message, context)
        return response
```

### 3.5 Memory Service
```python
class MemoryService:
    - add_memory(avatar_id, content, type, source)
    - retrieve_memories(avatar_id, query, top_k=5)
    - update_memory(memory_id, content)
    - delete_memory(memory_id)
    - build_memory_graph(avatar_id)  # 构建记忆图谱
```

### 3.6 Scheduler Service
```python
class SchedulerService:
    - create_scheduled_message(avatar_id, config)
    - list_scheduled_messages(avatar_id)
    - update_scheduled_message(message_id, config)
    - cancel_scheduled_message(message_id)
    - process_due_messages()  # Celery定时任务调用
```

## 4. AI 架构

### 4.1 人格Prompt模板

```python
PERSONA_PROMPT_TEMPLATE = """
你是一个数字分身，模拟以下人物：

【基本信息】
姓名: {name}
年龄: {age}
职业: {occupation}

【性格特征】
{personality_traits}

【语言风格】
{communication_style}

【重要记忆】
{memories}

【价值观】
{values}

【人物关系】
{relationships}

指令：
1. 始终以第一人称回答，仿佛你就是这个人
2. 使用上述性格特征和语言风格
3. 可以引用"重要记忆"中的内容
4. 如果不确定，诚实地表示"我不记得了"或"这不像我会说的话"
5. 保持尊重、温暖、真诚的态度

用户问题: {question}
"""
```

### 4.2 记忆检索流程

```
User Query
    │
    ▼
┌─────────────────┐
│  Query Embedding │  ──►  ChromaDB.similarity_search()
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ Retrieve Top-K  │  (默认5条相关记忆)
│   Memories      │
└─────────────────┘
    │
    ▼
┌─────────────────┐
│  Re-ranking     │  (可选：Cross-encoder精排)
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ Inject to Prompt│
└─────────────────┘
```

### 4.3 对话生成流程

```python
async def generate_avatar_response(avatar_id: str, user_message: str, conversation_history: list):
    # 1. 获取人格配置
    persona = await get_persona(avatar_id)
    
    # 2. 检索相关记忆
    memories = await memory_service.retrieve(
        avatar_id=avatar_id,
        query=user_message,
        top_k=5
    )
    
    # 3. 构建系统Prompt
    system_prompt = build_persona_prompt(persona, memories)
    
    # 4. 构建消息历史
    messages = [
        {"role": "system", "content": system_prompt},
        *conversation_history[-10:],  # 最近10轮
        {"role": "user", "content": user_message}
    ]
    
    # 5. 调用LLM
    response = await openai_client.chat.completions.create(
        model="gpt-4" or "kimi-k2.5",
        messages=messages,
        temperature=0.7,  # 有一定创造性但不要太离谱
        max_tokens=500
    )
    
    return response.choices[0].message.content
```

## 5. 部署架构

### 5.1 Docker Compose 配置

见 `docker-compose.yml`

### 5.2 生产环境建议

```
┌─────────────────────────────────────────┐
│              K8s Cluster                │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐   │
│  │Frontend │ │Backend  │ │Celery   │   │
│  │  Pods   │ │  Pods   │ │ Workers │   │
│  └─────────┘ └─────────┘ └─────────┘   │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐   │
│  │PostgreSQL│ │  Redis  │ │ChromaDB │   │
│  │  StatefulSet        │ │         │   │
│  └─────────┘ └─────────┘ └─────────┘   │
└─────────────────────────────────────────┘
```

## 6. 安全考虑

### 6.1 数据安全
- 敏感数据AES-256加密存储
- 数据库连接SSL
- 定期备份到异地

### 6.2 访问控制
- JWT Token认证
- API限流（Rate Limiting）
- CORS配置

### 6.3 隐私保护
- 数据最小化原则
- 用户完全控制数据删除
- 明确的数据使用协议

## 7. 监控与日志

### 7.1 指标监控
- Prometheus + Grafana
- 关键指标：API延迟、错误率、对话质量评分

### 7.2 日志管理
- ELK Stack 或 Loki
- 结构化日志
- 敏感信息脱敏

### 7.3 告警
- 服务宕机
- API错误率 > 5%
- 磁盘空间不足
