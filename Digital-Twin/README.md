# Digital Twin - 极简本地原型

本地运行的数字分身原型，无需服务器、无需 Docker。

## 快速开始

### 1. 克隆/下载项目

```bash
cd Digital-Twin
```

### 2. 启动后端

```bash
cd backend

# 创建虚拟环境（推荐）
python -m venv venv

# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 启动后端
python main.py
```

后端运行在 http://localhost:8000

### 3. 启动前端（新终端）

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端运行在 http://localhost:5173

### 4. 开始测试

1. 打开浏览器访问 http://localhost:5173
2. 注册账号
3. 创建数字分身
4. 填写问卷
5. 开始对话

## 数据存储

所有数据存储在项目目录的 `data/` 文件夹中：

```
data/
├── users.json              # 用户列表
├── avatars/                # 分身数据
│   ├── avatar_001.json     # 分身配置
│   └── avatar_001/         # 分身专属数据
│       ├── questionnaire.json
│       ├── memories.json
│       └── conversations/
└── chroma/                 # 向量数据库
```

## 技术栈

- **前端**: React + Vite + Tailwind CSS
- **后端**: Python + FastAPI
- **数据**: JSON 文件 + ChromaDB（本地）
- **AI**: Kimi API

## 配置 API Key

在项目根目录创建 `.env` 文件：

```
KIMI_API_KEY=your-api-key-here
```

## 功能清单

- [x] 用户注册/登录
- [x] 创建数字分身
- [x] 问卷数据收集（基础版）
- [x] 基于 Kimi 的对话
- [ ] 定时消息
- [ ] 语音支持
- [ ] 数据导出

## 注意事项

1. 这是原型，不要用于生产环境
2. 数据存储在本地，注意备份 `data/` 文件夹
3. 需要联网（调用 Kimi API）
