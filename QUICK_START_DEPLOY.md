# ⚡ Quick Start: GitHub + Render Deployment

## 🎯 Complete Process (15 minutes)

### Part 1: GitHub Push (5 min)

```bash
# 1. Navigate to project
cd Medical-Feedback-Analysis-Platform-

# 2. Initialize Git (if needed)
git init

# 3. Add all files
git add .

# 4. Commit
git commit -m "Initial commit: Medical Feedback Analysis Platform"

# 5. Create repository on GitHub.com (via browser)
#    Go to: https://github.com/new
#    Name: medical-feedback-platform
#    Click: Create repository

# 6. Push to GitHub (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/medical-feedback-platform.git
git branch -M main
git push -u origin main
```

**✅ Done! Code is on GitHub**

---

### Part 2: Render Deployment (10 min)

#### Step 1: Create Database
1. Go to https://render.com
2. Click "New +" → "PostgreSQL"
3. Name: `feedback-db`
4. Plan: Free
5. Click "Create Database"
6. **Copy Internal Database URL** (save it!)

#### Step 2: Create Web Service
1. Click "New +" → "Web Service"
2. Connect your GitHub repository
3. Settings:
   - **Name**: `medical-feedback-api`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:asgi_app --host 0.0.0.0 --port $PORT`
   - **Environment**: Python 3

#### Step 3: Set Environment Variables
Click "Add Environment Variable" for each:

```
SECRET_KEY=your-generated-secret-key
```
Generate: `python -c "import secrets; print(secrets.token_urlsafe(64))"`

```
GOOGLE_API_KEY=your-google-api-key
```

```
DATABASE_URL=postgresql+asyncpg://user:pass@host:port/db
```
(Change `postgresql://` to `postgresql+asyncpg://` from Internal Database URL)

```
ADMIN_EMAIL=admin@example.com
```

```
ADMIN_PASSWORD=YourStrongPassword123!
```

```
LOG_LEVEL=INFO
ENVIRONMENT=production
SQL_ECHO=false
AUTO_OPEN_BROWSER=0
```

#### Step 4: Deploy
1. Click "Create Web Service"
2. Wait 5-10 minutes for build
3. Copy your service URL

**✅ Done! App is live!**

---

## 🔗 Important Links

- **GitHub Push Guide**: [GITHUB_PUSH.md](./GITHUB_PUSH.md)
- **Full Deployment Guide**: [DEPLOYMENT.md](./DEPLOYMENT.md)
- **Demo Guide**: [DEMO_GUIDE.md](./DEMO_GUIDE.md)

---

## ✅ Checklist

### Before Pushing:
- [ ] `.env` file is NOT in repository (check .gitignore)
- [ ] All code files are ready
- [ ] `requirements.txt` is updated
- [ ] `env.example` exists

### Before Deploying:
- [ ] GitHub repository created
- [ ] Code pushed to GitHub
- [ ] Render account created
- [ ] Database created on Render
- [ ] Environment variables ready

### After Deploying:
- [ ] Service is "Live" on Render
- [ ] Health check works: `/health`
- [ ] Frontend loads: `/`
- [ ] Login works with admin credentials

---

## 🚀 You're Ready!

Follow the steps above and your app will be live on Render! 🎉

