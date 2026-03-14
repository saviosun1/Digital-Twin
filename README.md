# Digital Twin - 数字分身

本地运行的数字分身原型，无需服务器、无需 Docker。

## 🚀 快速开始

### 本地开发

**1. 启动后端**

```bash
cd backend

# 创建虚拟环境（推荐）
python -m venv venv

# Mac/Linux
source venv/bin/activate
# Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 启动后端
python main.py
```

后端运行在 http://localhost:8000

**2. 启动前端（新终端）**

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端运行在 http://localhost:5173

**3. 开始测试**

1. 打开浏览器访问 http://localhost:5173
2. 注册账号
3. 创建数字分身
4. 填写问卷
5. 开始对话

---

## 🌐 部署到 GitHub Pages

### 步骤 1：创建 GitHub 仓库

1. 登录 https://github.com
2. 点击右上角 "+" → "New repository"
3. 仓库名称填 `digital-twin`
4. 选择 "Public"
5. 点击 "Create repository"

### 步骤 2：推送代码

```bash
# 在项目根目录执行
git remote add origin https://github.com/你的用户名/digital-twin.git
git branch -M main
git push -u origin main
```

### 步骤 3：启用 GitHub Pages

1. 进入仓库页面 → Settings → Pages
2. Source 选择 "GitHub Actions"
3. 点击 Save

### 步骤 4：配置后端地址

前端部署后需要连接后端 API。编辑 `.env.production`：

```bash
cd frontend
cp .env.production.example .env.production
# 编辑 .env.production，填入你的后端地址
```

内容示例：
```
VITE_API_URL=https://your-backend.railway.app
```

**后端部署选项：**
- Railway (免费): https://railway.app
- Render (免费): https://render.com
- 阿里云/腾讯云 (免费额度)

### 步骤 5：重新部署

```bash
git add .
git commit -m "Update API URL"
git push
```

GitHub Actions 会自动构建并部署到 Pages。

### 步骤 6：访问

部署完成后访问：
```
https://你的用户名.github.io/digital-twin/
```

---

## 📁 数据存储

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

---

## 🛠️ 技术栈

- **前端**: React + Vite + TypeScript + Tailwind CSS
- **后端**: Python + FastAPI
- **数据**: JSON 文件 + SQLite
- **AI**: Kimi API

---

## ✅ 功能清单

- [x] 用户注册/登录
- [x] 创建数字分身
- [x] 问卷数据收集（基础版）
- [x] 基于 Kimi 的对话
- [ ] 定时消息
- [ ] 语音支持
- [ ] 数据导出

---

## ⚠️ 注意事项

1. 这是原型，不要用于生产环境
2. 数据存储在本地，注意备份 `data/` 文件夹
3. 需要联网（调用 Kimi API）
4. GitHub Pages 只托管前端，后端需另行部署
