# Medical Feedback Analysis Platform

A FastAPI backend system for analyzing medical feedback using Gemini AI, with real-time alerts via Socket.IO.

python -c "import secrets; print(secrets.token_urlsafe(64))"

## Features


- **Feedback Submission**: Patients can submit feedback with ratings and comments
- **AI Analysis**: Automatic sentiment analysis, emotion detection, and urgency classification using Google Gemini AI
- **Real-time Alerts**: Socket.IO notifications for critical feedback
- **Analytics Dashboard**: Comprehensive analytics and trends for staff
- **Staff Actions**: Track and manage feedback resolution

## Quick Start (Windows / PowerShell)

1. (First time) Create venv and install dependencies:
   ```bash
   py -m venv .venv
   .\.venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. Create a `.env` file in the project root with:
   ```env
   GOOGLE_API_KEY=YOUR_GOOGLE_API_KEY
   DATABASE_URL=postgresql+asyncpg://postgres:password@localhost/feedback_db
   ```

3. Create the PostgreSQL database (via psql or pgAdmin):
   ```bash
   psql -U postgres -h localhost -c "CREATE DATABASE feedback_db;"
   ```

4. Run the server (Socket.IO enabled). The browser will auto-open:
   ```bash
   uvicorn app.main:asgi_app --reload --host 127.0.0.1 --port 8000
   ```
   
   The API will be available at:
   - API: http://127.0.0.1:8000
   - API Docs: http://127.0.0.1:8000/docs
   - Frontend: http://127.0.0.1:8000/ (served automatically)
   - Socket.IO: ws://127.0.0.1:8000/socket.io/

Optional:
- Disable auto-open browser: set `AUTO_OPEN_BROWSER=0`
- Change port (and auto-open target): set `PORT=9000` and run with `--port 9000`
- FastAPI only (no Socket.IO): `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`

## Authentication (Staff/Admin)

MVP includes simple JWT auth with roles (`admin`, `staff`) for admin features (lists, updates, analytics, export).

1. Register a user (for demo; in production restrict this to admins):
```bash
POST /auth/register
{ "email": "admin@example.com", "password": "Secret123", "role": "admin" }
```

2. Login to get tokens:
```bash
POST /auth/login
{ "email": "admin@example.com", "password": "Secret123" }
```
Use `Authorization: Bearer <access_token>` for:
- `GET /feedback/all`, `GET /feedback/urgent`, `GET /feedback/{id}`
- `POST /feedback/{id}/update`
- `GET /analytics/summary`, `GET /analytics/trends`

Env keys:
- `SECRET_KEY`: set a strong secret in `.env` for JWT signing.

5. Test flow: Submit feedback → AI analysis runs in background → real-time notifications on dashboard.

## API Endpoints

### Feedback
- `POST /feedback` - Submit new feedback
- `GET /feedback/all` - Get all feedback with filters
- `GET /feedback/all?format=csv` - Export feedback as CSV
- `GET /feedback/{id}` - Get single feedback with analysis
- `POST /feedback/{id}/update` - Update feedback status and add notes
- `GET /feedback/urgent` - List urgent/critical feedback

### Analytics
- `GET /analytics/summary` - Get analytics summary
- `GET /analytics/trends` - Get trends data

## Socket.IO Events

### Server → Client
- `new_feedback` - New feedback received
- `urgent_alert` - Critical feedback alert
- `analysis_complete` - Analysis completed
- `dashboard_stats_update` - Dashboard stats updated

### Client → Server
- Staff actions on feedback
- Request real-time updates

## Project Structure

```
app/
├── main.py              # FastAPI app initialization
├── routers/             # API routes
├── services/            # Business logic
├── models/              # Database models
├── sockets/             # Socket.IO events
├── utils/               # Utilities
└── db.py                # Database connection
```

Notes:
- Frontend assets are served from `frontend/` at `/static` and `/` (index).
- If `frontend/favicon.ico` is missing, `/favicon.ico` returns 204 (no 404 noise).
- Tip: 0.0.0.0 is a bind address (for listening on all interfaces). In your browser, open `http://127.0.0.1:8000/` (or `http://localhost:8000/`).

