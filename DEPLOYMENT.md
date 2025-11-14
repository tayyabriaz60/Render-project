# 🚀 Deployment Guide - Render.com

## Step 1: GitHub Repository Setup

### 1.1 Initialize Git (if not already done)
```bash
cd Medical-Feedback-Analysis-Platform-
git init
```

### 1.2 Check .gitignore
Make sure `.gitignore` includes:
- `.env`
- `logs/`
- `__pycache__/`
- `.venv/`
- `*.pyc`

### 1.3 Add All Files
```bash
git add .
git commit -m "Initial commit: Medical Feedback Analysis Platform"
```

### 1.4 Create GitHub Repository
1. Go to https://github.com/new
2. Repository name: `medical-feedback-platform` (or your choice)
3. Description: "Medical Feedback Analysis Platform with AI"
4. **DO NOT** initialize with README (we already have one)
5. Click "Create repository"

### 1.5 Push to GitHub
```bash
# Add remote (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/medical-feedback-platform.git

# Push to GitHub
git branch -M main
git push -u origin main
```

---

## Step 2: Render.com Setup

### 2.1 Create Render Account
1. Go to https://render.com
2. Sign up with GitHub (recommended)
3. Authorize Render to access your GitHub repositories

### 2.2 Create PostgreSQL Database

1. **Go to Dashboard** → Click "New +" → Select "PostgreSQL"

2. **Database Settings:**
   - **Name**: `feedback-db`
   - **Database**: `feedback_db`
   - **User**: `feedback_user`
   - **Region**: Choose closest to you
   - **Plan**: Free (or Starter for production)
   - Click "Create Database"

3. **Save Connection String:**
   - Wait for database to be created
   - Go to database dashboard
   - Copy "Internal Database URL" (we'll use this later)
   - Format: `postgresql://user:password@host:port/database`

### 2.3 Create Web Service

1. **Go to Dashboard** → Click "New +" → Select "Web Service"

2. **Connect Repository:**
   - Select your GitHub repository
   - Click "Connect"

3. **Service Settings:**
   - **Name**: `medical-feedback-api`
   - **Region**: Same as database
   - **Branch**: `main`
   - **Root Directory**: Leave empty (or `Medical-Feedback-Analysis-Platform-` if needed)
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:asgi_app --host 0.0.0.0 --port $PORT`

4. **Environment Variables:**
   Click "Add Environment Variable" and add:

   ```
   SECRET_KEY=your-secret-key-here
   ```
   Generate with: `python -c "import secrets; print(secrets.token_urlsafe(64))"`

   ```
   GOOGLE_API_KEY=your-google-api-key
   ```

   ```
   DATABASE_URL=postgresql+asyncpg://user:password@host:port/database
   ```
   Use the Internal Database URL from step 2.2, but change `postgresql://` to `postgresql+asyncpg://`

   ```
   ADMIN_EMAIL=admin@yourdomain.com
   ```

   ```
   ADMIN_PASSWORD=YourStrongPassword123!
   ```

   ```
   LOG_LEVEL=INFO
   ```

   ```
   ENVIRONMENT=production
   ```

   ```
   SQL_ECHO=false
   ```

   ```
   AUTO_OPEN_BROWSER=0
   ```

   ```
   DB_POOL_SIZE=10
   ```

   ```
   DB_MAX_OVERFLOW=5
   ```

   ```
   DB_POOL_TIMEOUT=30
   ```

   ```
   DB_POOL_RECYCLE=3600
   ```

   ```
   PORT=10000
   ```
   (Render automatically sets PORT, but this is a fallback)

5. **Advanced Settings:**
   - **Auto-Deploy**: Yes (deploys on every push)
   - Click "Create Web Service"

### 2.4 Wait for Deployment
- Render will build and deploy your app
- Check logs for any errors
- First deployment takes 5-10 minutes

---

## Step 3: Verify Deployment

### 3.1 Check Service Status
- Go to your service dashboard
- Status should be "Live"
- Copy your service URL (e.g., `https://medical-feedback-api.onrender.com`)

### 3.2 Test Endpoints
1. **Health Check:**
   ```
   https://your-service-url.onrender.com/health
   ```

2. **API Docs:**
   ```
   https://your-service-url.onrender.com/docs
   ```

3. **Frontend:**
   ```
   https://your-service-url.onrender.com/
   ```

### 3.3 Test Login
1. Go to frontend URL
2. Click "Login"
3. Use your `ADMIN_EMAIL` and `ADMIN_PASSWORD`

---

## Step 4: Post-Deployment Configuration

### 4.1 Update CORS (if needed)
If you have a custom domain, update CORS in `app/main.py`:
```python
origins = [
    "https://your-custom-domain.com",
    "https://your-service.onrender.com",
]
```

### 4.2 Custom Domain (Optional)
1. Go to service settings
2. Click "Custom Domains"
3. Add your domain
4. Follow DNS configuration instructions

---

## Troubleshooting

### Build Fails
- Check build logs in Render dashboard
- Verify `requirements.txt` is correct
- Check Python version compatibility

### Database Connection Error
- Verify `DATABASE_URL` is correct
- Make sure it uses `postgresql+asyncpg://` (not `postgresql://`)
- Check database is running

### Application Crashes
- Check service logs
- Verify all environment variables are set
- Check `SECRET_KEY` is set and valid

### Socket.IO Not Working
- Render free tier has connection limits
- Consider upgrading to paid plan for production
- Check WebSocket support in service logs

---

## Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | ✅ Yes | JWT signing key (64+ chars) |
| `GOOGLE_API_KEY` | ✅ Yes | Gemini AI API key |
| `DATABASE_URL` | ✅ Yes | PostgreSQL connection string |
| `ADMIN_EMAIL` | ✅ Yes | Initial admin email |
| `ADMIN_PASSWORD` | ✅ Yes | Initial admin password |
| `LOG_LEVEL` | ❌ No | Logging level (default: INFO) |
| `ENVIRONMENT` | ❌ No | Environment name (default: production) |
| `SQL_ECHO` | ❌ No | SQL query logging (default: false) |
| `AUTO_OPEN_BROWSER` | ❌ No | Auto-open browser (default: 0) |
| `DB_POOL_SIZE` | ❌ No | DB pool size (default: 10) |
| `DB_MAX_OVERFLOW` | ❌ No | DB max overflow (default: 5) |
| `DB_POOL_TIMEOUT` | ❌ No | DB pool timeout (default: 30) |
| `DB_POOL_RECYCLE` | ❌ No | DB pool recycle (default: 3600) |
| `PORT` | ❌ No | Server port (Render sets automatically) |

---

## Quick Commands

### Generate Secret Key
```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

### Check Git Status
```bash
git status
```

### Push Updates
```bash
git add .
git commit -m "Your commit message"
git push origin main
```

---

## Cost Estimate (Render Free Tier)

- **Web Service**: Free (with limitations)
  - Spins down after 15 minutes of inactivity
  - Limited resources
- **PostgreSQL Database**: Free (with limitations)
  - 90 days retention
  - Limited storage

**For Production**: Consider upgrading to paid plans for:
- Always-on service
- More resources
- Better performance
- Custom domains

---

## Next Steps

1. ✅ Code pushed to GitHub
2. ✅ Database created on Render
3. ✅ Web service deployed
4. ✅ Environment variables configured
5. ✅ Application tested
6. 🎉 **Deployment Complete!**

**Your app is now live! 🚀**

