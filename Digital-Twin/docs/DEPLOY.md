# 部署到 GitHub Pages

## 步骤

### 1. 在 GitHub 创建仓库
- 登录 https://github.com
- 新建仓库，名称如 `digital-twin`
- 选择「Public」（GitHub Pages 免费需要公开仓库）

### 2. 推送代码到 GitHub
```bash
git remote add origin https://github.com/你的用户名/digital-twin.git
git branch -M main
git push -u origin main
```

### 3. 启用 GitHub Pages
1. 进入仓库 Settings → Pages
2. Source 选择 "GitHub Actions"
3. 保存

### 4. 自动部署
- 每次 push 到 main 分支会自动触发部署
- 部署完成后访问：`https://你的用户名.github.io/digital-twin/`

## ⚠️ 重要提示

GitHub Pages **只能托管静态前端**，Python 后端需要另外部署：

### 后端部署选项

**A. 免费方案（推荐原型测试）**
- Railway: https://railway.app
- Render: https://render.com
- 阿里云/腾讯云免费额度

**B. 一体化方案**
- 把整个项目部署到 Vercel（Next.js 全栈）
- 或 Railway（支持 Python）

### 当前状态
- ✅ 前端可部署到 GitHub Pages
- ⚠️ 后端 API 需另行部署
- ⚠️ 需要修改前端 `stores/auth.ts` 中的 `API_URL` 指向你的后端地址
