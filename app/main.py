"""
FastAPI application main entry point
"""
from fastapi import FastAPI
from fastapi import Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import socketio
from contextlib import asynccontextmanager
import os
import threading
import tempfile
import time
import webbrowser

from app.db import init_db
from app.routers import feedback, analytics
from app.routers import auth as auth_router
from app.sockets.events import sio
from app.services.auth_service import ensure_admin_user
from app.db import AsyncSessionLocal


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup
    print("Initializing database...")
    await init_db()
    print("Database initialized successfully")

    # Seed initial admin user if provided via env and no users exist
    try:
        admin_email = os.getenv("ADMIN_EMAIL")
        admin_password = os.getenv("ADMIN_PASSWORD")
        if admin_email and admin_password:
            async with AsyncSessionLocal() as seed_session:
                await ensure_admin_user(seed_session, admin_email, admin_password)
                print("Admin bootstrap checked")
        else:
            print("Admin bootstrap skipped (set ADMIN_EMAIL and ADMIN_PASSWORD to enable)")
    except Exception as e:
        print(f"Admin bootstrap error: {e}")

    # Optionally auto-open default browser to frontend once
    # Controlled by env AUTO_OPEN_BROWSER (default: "1")
    # Uses a temp lock file to avoid multiple openings with --reload
    try:
        if os.getenv("AUTO_OPEN_BROWSER", "1") == "1":
            lock_path = os.path.join(tempfile.gettempdir(), "mfap_browser_open.lock")
            should_open = True
            # If lock file exists and is recent, skip
            if os.path.exists(lock_path):
                try:
                    last_mtime = os.path.getmtime(lock_path)
                    # Skip if opened within the last 120 seconds
                    if (time.time() - last_mtime) < 120:
                        should_open = False
                except Exception:
                    pass
            if should_open:
                # Touch/refresh lock
                try:
                    with open(lock_path, "w", encoding="utf-8") as f:
                        f.write(str(time.time()))
                except Exception:
                    pass

                port = os.getenv("PORT", "8000")
                url = f"http://localhost:{port}/"
                threading.Timer(1.0, lambda: webbrowser.open(url)).start()
                print(f"Opening browser at {url} ...")
    except Exception as e:
        # Non-fatal if auto-open fails
        print(f"Auto-open browser skipped: {e}")
    
    yield
    
    # Shutdown
    print("Shutting down...")


# Create FastAPI app
app = FastAPI(
    title="Medical Feedback Analysis Platform",
    description="Backend API for analyzing medical feedback using Gemini AI",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(feedback.router)
app.include_router(analytics.router)
app.include_router(auth_router.router)

# Serve frontend static files
frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")
    
    @app.get("/staff", include_in_schema=False)
    async def serve_staff_login():
        """Serve staff login page"""
        staff_path = os.path.join(frontend_path, "staff_login.html")
        if os.path.exists(staff_path):
            return FileResponse(staff_path)
        return {"message": "Staff login page not found"}

    @app.get("/", include_in_schema=False)
    async def serve_frontend():
        """Serve frontend index.html"""
        index_path = os.path.join(frontend_path, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        return {
            "message": "Medical Feedback Analysis Platform API",
            "version": "1.0.0",
            "docs": "/docs"
        }

    @app.get("/favicon.ico", include_in_schema=False)
    async def serve_favicon():
        """Serve favicon if present; otherwise return 204 to avoid 404 noise"""
        icon_path = os.path.join(frontend_path, "favicon.ico")
        if os.path.exists(icon_path):
            return FileResponse(icon_path)
        return Response(status_code=204)
else:
    # Root endpoint (if frontend not found)
    @app.get("/")
    async def root():
        """Root endpoint"""
        return {
            "message": "Medical Feedback Analysis Platform API",
            "version": "1.0.0",
            "docs": "/docs"
        }


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


# Create ASGI application with Socket.IO
asgi_app = socketio.ASGIApp(sio, app)


# Export the ASGI app for uvicorn
# Use 'asgi_app' when running with uvicorn to enable Socket.IO
# Use 'app' if you only need FastAPI without Socket.IO
__all__ = ["app", "asgi_app"]

if __name__ == "__main__":
    import uvicorn
    # Run with asgi_app to enable Socket.IO
    uvicorn.run(
        "app.main:asgi_app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

