# ⚡ Quick Demo Checklist (5 Minutes Before Demo)

## ✅ Pre-Flight Check

- [ ] Server running hai? 
  ```bash
  uvicorn app.main:asgi_app --reload --host 127.0.0.1 --port 8000
  ```

- [ ] Browser open hai? 
  - http://127.0.0.1:8000

- [ ] Login credentials ready hain?
  - Email: Check `.env` file mein `ADMIN_EMAIL`
  - Password: Check `.env` file mein `ADMIN_PASSWORD`

- [ ] Gemini API key set hai? (`.env` file mein `GOOGLE_API_KEY`)

- [ ] Database connected hai? (Server logs mein "Database initialized" dikhna chahiye)

---

## 🎯 Demo Flow (Quick)

### 1. Patient Form (30 sec)
- [ ] Browser open karo
- [ ] Patient form dikhao
- [ ] Sample critical feedback submit karo:
  ```
  Name: Ahmed Ali
  Department: Emergency  
  Rating: 1
  Feedback: "Severe chest pain, difficulty breathing, life-threatening situation"
  ```

### 2. Staff Login (30 sec)
- [ ] Login button click
- [ ] Credentials enter karo
- [ ] Dashboard open hoga

### 3. Dashboard Show (1 min)
- [ ] All feedback list dikhao
- [ ] Sentiment badges dikhao (Positive/Negative)
- [ ] Urgency badges dikhao (Critical/High/Medium/Low)
- [ ] "View" button click karke AI analysis dikhao

### 4. Urgent Tab (1 min)
- [ ] Urgent tab click karo
- [ ] Critical feedback dikhao
- [ ] Explain: "Auto-refresh hota hai, real-time updates"

### 5. Analytics (30 sec)
- [ ] Analytics tab open karo
- [ ] Charts aur statistics dikhao

### 6. Action (30 sec)
- [ ] Action button click karo
- [ ] Action create karo
- [ ] Save karo

---

## 🎤 Key Points to Say

1. **"AI-powered analysis"** - Automatic sentiment & urgency detection
2. **"Real-time updates"** - Socket.IO live notifications  
3. **"Urgent feedback highlighting"** - Critical cases automatically flagged
4. **"User-friendly interface"** - Clean, modern design
5. **"Secure & scalable"** - JWT auth, async operations

---

## 🐛 If Something Breaks

- **Analysis fail?** → "Retry" button click karo
- **Data nahi dikhe?** → Browser refresh (F5)
- **Login issue?** → Check `.env` file credentials
- **API error?** → Check Gemini API key

**Stay Calm & Continue! 😊**

---

## 📞 Backup Plan

Agar live demo fail ho:
- Screenshots ready rakho
- Video recording (agar possible)
- API docs dikhao: http://127.0.0.1:8000/docs

**You Got This! 🚀**

