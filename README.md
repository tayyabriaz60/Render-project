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

2. Copy `env.example` to `.env` and replace placeholder values (never commit `.env`):
   ```env
   # Core
   SECRET_KEY=REPLACE_WITH_A_LONG_RANDOM_SECRET
   GOOGLE_API_KEY=YOUR_GOOGLE_API_KEY
   DATABASE_URL=postgresql+asyncpg://postgres:password@localhost/feedback_db

   # Bootstrap first admin (created automatically if no users exist)
   ADMIN_EMAIL=admin@example.com
   ADMIN_PASSWORD=StrongPass123

   # Local dev server behavior
   AUTO_OPEN_BROWSER=1
   PORT=8000
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

## Security Setup (Required)

- Generate a secure secret: `python -c "import secrets; print(secrets.token_urlsafe(64))"` and add to `.env`.
- Set a strong `ADMIN_PASSWORD` (12+ chars, mixed case/numbers/symbols).
- Ensure `.env` is ignored by git (already configured) and never checked in.
- Restrict CORS and Socket.IO origins in production (currently wide-open for local dev).
- Rotate the secret key and database credentials if they ever leak.

## Architecture Notes

- FastAPI application with async SQLAlchemy sessions and connection pooling.
- AI analysis performed via true async HTTP calls to the Gemini REST API.
- Background tasks open their own database sessions to avoid lifecycle leaks.
- Structured logging (console + rotating file) is enabled via `app/logging_config.py`.
- CSV exports stream rows to avoid high memory usage on large datasets.

## Deployment

### Deploy to Render.com

See [DEPLOYMENT.md](./DEPLOYMENT.md) for complete deployment instructions.

**Quick Steps:**
1. Push code to GitHub
2. Create PostgreSQL database on Render
3. Create Web Service on Render
4. Set environment variables
5. Deploy!

**Important:** Make sure to set all required environment variables in Render dashboard:
- `SECRET_KEY` (generate with: `python -c "import secrets; print(secrets.token_urlsafe(64))"`)
- `GOOGLE_API_KEY`
- `DATABASE_URL` (from Render PostgreSQL)
- `ADMIN_EMAIL`
- `ADMIN_PASSWORD`

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

## Known Limitations & Future Improvements

1. **Concurrent Load:** Optimized for dozens of concurrent staff users; use a task queue (Celery/Redis) for heavy Gemini workloads.
2. **AI Rate Limits:** Gemini API quotas apply. Consider request throttling or a queue if users generate spikes.
3. **Real-time Scaling:** Socket.IO runs in-process; add a shared adapter (Redis) before scaling horizontally.
4. **Large Exports:** Streaming CSV handles thousands of rows, but prefer data warehouses for massive exports.
5. **Testing:** Add automated unit/integration tests before production deployment.

Recommended production checklist:
- [ ] Configure HTTPS / reverse proxy.
- [ ] Add monitoring & alerting (Prometheus, Grafana, etc.).
- [ ] Set up log aggregation (ELK, Loki, CloudWatch).
- [ ] Schedule database backups and apply migrations via Alembic.

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

