# Medical Feedback Analysis Platform - Complete Line-by-Line Code Analysis

## Table of Contents
1. [Main Entry Point (main.py)](#main-entry-point)
2. [Database Configuration (app/db.py)](#database-configuration)
3. [Dependencies (app/deps.py)](#dependencies)
4. [Logging Configuration](#logging-configuration)
5. [Models](#models)
6. [Services](#services)
7. [Routers](#routers)
8. [Utilities](#utilities)
9. [Socket.IO Events](#socketio-events)
10. [Frontend Files](#frontend-files)

---

## Main Entry Point

### `main.py` (166 lines)

**Lines 1-3**: Module docstring describing the FastAPI application entry point.

**Lines 4-26**: Imports
- `from __future__ import annotations`: Enables postponed evaluation of annotations (Python 3.7+)
- Standard library: `os`, `tempfile`, `threading`, `time`, `webbrowser`
- `contextlib.asynccontextmanager`: For lifespan management
- FastAPI components: `FastAPI`, `Response`, `CORSMiddleware`, `FileResponse`, `StaticFiles`
- `socketio`: For WebSocket support
- Application modules: database, logging, middleware, routers, services, sockets, utils

**Lines 28**: Logger initialization using the centralized logging config.

**Lines 31-38**: `_validate_configuration()` function
- **Line 33**: Validates SECRET_KEY (raises if invalid)
- **Line 34-35**: Checks DATABASE_URL environment variable
- **Line 36-37**: Warns if GOOGLE_API_KEY is missing (AI analysis will be disabled)

**Lines 40-66**: `lifespan()` async context manager
- **Line 43**: Sets up logging on startup
- **Line 45**: Validates configuration
- **Line 47**: Initializes database schema
- **Lines 50-60**: Admin user bootstrap logic
  - Creates admin user if ADMIN_EMAIL/ADMIN_PASSWORD env vars are set
  - Only runs if no users exist (bootstrap mode)
  - Logs errors but doesn't crash the app
- **Line 62**: Optionally opens browser automatically
- **Line 64**: `yield` - application runs here
- **Line 66**: Shutdown logging

**Lines 69-84**: `_maybe_open_browser()` function
- **Line 70**: Checks AUTO_OPEN_BROWSER env var (default "0")
- **Lines 72-77**: Lock file mechanism to prevent multiple browser opens
  - Uses temp directory lock file
  - Only opens if lock file is older than 120 seconds
- **Lines 79-80**: Creates/updates lock file with timestamp
- **Line 81**: Gets PORT from env (default 8000)
- **Line 83**: Opens browser after 1 second delay (non-blocking)

**Lines 87-92**: FastAPI app initialization
- Title, description, version metadata
- `lifespan` parameter for startup/shutdown events

**Lines 94-100**: CORS middleware configuration
- **Line 96**: `allow_origins=["*"]` - WIDE OPEN (security risk in production!)
- **Line 97**: `allow_credentials=True` - Allows cookies/auth headers
- **Lines 98-99**: Allows all methods and headers

**Line 101**: Custom request logging middleware

**Lines 103-104**: Exception handlers
- Custom APIError handler
- Generic exception handler

**Lines 106-109**: Router registration
- Feedback router
- Analytics router
- Auth router
- Health router

**Lines 112-148**: Frontend serving logic
- **Line 112**: Constructs frontend path relative to main.py
- **Line 113**: Checks if frontend directory exists
- **Line 114**: Mounts static files at `/static`
- **Lines 116-121**: `/staff` endpoint - serves staff login page
- **Lines 123-132**: `/` endpoint - serves index.html or API info
- **Lines 134-139**: `/favicon.ico` endpoint - serves favicon or 204 No Content
- **Lines 140-148**: Fallback if frontend doesn't exist - returns API info

**Line 151**: Creates ASGI app combining Socket.IO and FastAPI

**Line 153**: Module exports

**Lines 156-164**: `__main__` block
- Runs uvicorn server
- Uses `asgi_app` (includes Socket.IO)
- Host: 0.0.0.0 (all interfaces)
- Port from env (default 8000)
- Reload enabled for development

---

## Database Configuration

### `app/db.py` (77 lines)

**Lines 1-2**: Future annotations import

**Lines 4-5**: Standard library imports

**Line 6**: `load_dotenv()` - Loads environment variables from .env file

**Lines 7-8**: SQLAlchemy async imports
- `AsyncSession`, `async_sessionmaker`, `create_async_engine`
- `declarative_base` for ORM models

**Line 10**: Logger import

**Line 12**: Load environment variables

**Line 13**: Logger initialization

**Line 15**: DATABASE_URL from env (default PostgreSQL connection string)
- Format: `postgresql+asyncpg://user:password@host/database`

**Line 16**: ENVIRONMENT from env (default "development")

**Line 17**: SQL_ECHO - Only echo SQL in development mode
- Helps debug SQL queries

**Lines 18-21**: Connection pool configuration
- **POOL_SIZE**: Default 20 connections
- **MAX_OVERFLOW**: Default 10 additional connections
- **POOL_TIMEOUT**: Default 30 seconds wait for connection
- **POOL_RECYCLE**: Default 3600 seconds (1 hour) - recycles connections

**Lines 23-33**: Async engine creation
- **echo**: SQL logging (only in dev)
- **pool_size/max_overflow**: Connection pool limits
- **pool_timeout**: Wait time for connection
- **pool_recycle**: Connection lifetime
- **pool_pre_ping**: Checks connection health before use
- **pool_use_lifo**: Last-in-first-out queue (better for connection reuse)
- **future**: SQLAlchemy 2.0 style

**Line 35**: Session factory creation
- `expire_on_commit=False` - Objects remain accessible after commit

**Line 37**: Base class for ORM models

**Lines 40-46**: `get_db()` dependency function
- FastAPI dependency pattern
- Yields a database session
- Ensures session is closed in finally block

**Lines 49-53**: `init_db()` function
- Creates all database tables
- Uses `engine.begin()` for transaction
- `run_sync()` to run sync SQLAlchemy method in async context

**Lines 56-64**: `check_db_connection()` function
- Lightweight health check
- Executes `SELECT 1` query
- Returns True/False based on success
- Logs errors but doesn't raise

**Lines 67-75**: `get_pool_stats()` function
- Returns connection pool statistics
- Useful for monitoring and debugging
- Returns: size, checked_in, checked_out, overflow

---

## Dependencies

### `app/deps.py` (61 lines)

**Lines 1-5**: Imports
- `Optional`, `Callable` from typing
- FastAPI dependencies and security
- JWT handling with `jose`
- SQLAlchemy async session

**Lines 7-9**: Application imports

**Line 12**: HTTPBearer security scheme
- `auto_error=False` - Doesn't auto-raise on missing token

**Lines 15-30**: `get_current_user()` dependency
- **Line 19**: Checks if credentials exist and scheme is "bearer"
- **Line 20**: Raises 401 if not authenticated
- **Line 21**: Extracts token from credentials
- **Lines 22-24**: Decodes JWT token
  - Uses HS256 algorithm
  - Extracts user_id from "sub" claim
- **Line 25**: Handles JWT decode errors
- **Line 27**: Fetches user from database
- **Lines 28-29**: Raises 401 if user not found
- **Line 30**: Returns User object

**Lines 33-38**: `require_role()` function factory
- Creates a dependency that checks user role
- **Line 35**: Gets current user (must be authenticated)
- **Line 36**: Checks if user role is in allowed roles
- **Line 37**: Raises 403 if insufficient permissions
- **Line 38**: Returns user if authorized

**Lines 41-58**: `get_current_user_optional()` dependency
- Similar to `get_current_user()` but returns None instead of raising
- **Line 49**: Returns None if no credentials
- **Line 56**: Returns None on JWT error
- **Line 57**: Fetches user (may return None)
- **Line 58**: Returns user or None
- Useful for routes that allow both authenticated and anonymous access

---

## Logging Configuration

### `app/logging_config.py` (98 lines)

**Lines 1-3**: Module docstring

**Lines 4-11**: Standard library imports
- `logging`, `os`, `sys`
- `RotatingFileHandler` for file logging
- `Path` from pathlib
- `Optional` type hint

**Lines 14-30**: `_ColoredFormatter` class
- Custom formatter for colored console output
- **Lines 17-23**: ANSI color codes dictionary
  - DEBUG: cyan, INFO: green, WARNING: yellow, ERROR: red, CRITICAL: magenta
- **Line 24**: Reset code
- **Lines 26-30**: `format()` method
  - Adds color to levelname if color is enabled
  - Calls parent formatter
- **Lines 32-34**: `_use_color()` static method
  - Checks `NO_COLOR` env var (standard convention)
  - Returns False if NO_COLOR=1

**Lines 37-90**: `setup_logging()` function
- **Line 38**: Parameters with defaults
- **Line 46**: Gets log level from parameter or env (default INFO)
- **Line 47**: Converts string level to numeric
- **Lines 49-50**: Creates logs directory if needed
- **Line 52**: Gets root logger
- **Line 53**: Sets log level
- **Line 54**: Clears existing handlers (prevents duplicates)

**Lines 56-62**: Formatters
- **Lines 56-58**: Standard formatter with file/line info
- **Lines 59-62**: Detailed formatter with function name

**Lines 64-71**: Console handler setup
- **Line 65**: Creates StreamHandler for stdout
- **Lines 66-69**: Uses colored formatter in development
- **Line 70**: Sets handler level
- **Line 71**: Adds to root logger

**Lines 73-82**: File handler setup
- **Lines 74-79**: RotatingFileHandler
  - Max 10MB per file
  - Keeps 5 backup files
  - UTF-8 encoding
- **Line 80**: Uses detailed formatter
- **Line 81**: File handler always at DEBUG level
- **Line 82**: Adds to root logger

**Lines 84-87**: Silence noisy dependencies
- Sets SQLAlchemy, asyncio, httpx loggers to WARNING
- Reduces log noise

**Line 89**: Debug log confirming configuration

**Lines 93-95**: `get_logger()` helper function
- Simple wrapper to get module-specific logger

### `app/middleware/logging.py` (40 lines)

**Lines 1-2**: Module docstring

**Lines 4-7**: Imports
- `time` for performance measurement
- FastAPI Request/Response
- `BaseHTTPMiddleware` from Starlette

**Line 14**: Logger initialization

**Lines 17-39**: `RequestLoggingMiddleware` class
- **Line 20**: `dispatch()` method (required by BaseHTTPMiddleware)
- **Line 21**: Records start time using `perf_counter()` (high precision)
- **Lines 22-27**: Logs incoming request
  - Method and path
  - Client IP in extra context
- **Line 29**: Calls next middleware/handler
- **Line 30**: Calculates duration in milliseconds
- **Lines 31-37**: Logs response
  - Method, path, status code, duration
- **Line 38**: Adds X-Process-Time header to response
- **Line 39**: Returns response

---

## Models

### `app/models/user.py` (17 lines)

**Lines 1-3**: SQLAlchemy imports
- Column types: `Integer`, `String`, `DateTime`
- `func` for SQL functions

**Line 3**: Base import

**Lines 6-14**: `User` model class
- **Line 7**: Table name: "users"
- **Line 9**: Primary key `id` with index
- **Line 10**: `email` - unique, not null, indexed
- **Line 11**: `password_hash` - stores bcrypt hash
- **Line 12**: `role` - default "staff", can be "admin" or "staff"
- **Line 13**: `created_at` - auto-set on insert (timezone-aware)
- **Line 14**: `updated_at` - auto-updated on update (timezone-aware)

### `app/models/feedback.py` (30 lines)

**Lines 1-3**: SQLAlchemy imports
- Additional types: `Text`, `Index`
- `relationship` for ORM relationships

**Lines 5-28**: `Feedback` model
- **Line 9**: Table name: "feedback"
- **Line 11**: Primary key `id`
- **Line 12**: `patient_name` - optional
- **Line 13**: `visit_date` - required, indexed
- **Line 14**: `department` - required, indexed
- **Line 15**: `doctor_name` - optional
- **Line 16**: `feedback_text` - required, Text type (unlimited length)
- **Line 17**: `rating` - integer, required
- **Line 18**: `status` - default "pending_analysis", indexed
- **Line 19**: `created_at` - auto-set, indexed
- **Line 20**: `updated_at` - auto-updated

**Line 22**: Relationship to Analysis (one-to-one)
- `uselist=False` - single analysis per feedback
- `cascade="all, delete-orphan"` - deletes analysis if feedback deleted

**Line 23**: Relationship to Actions (one-to-many)
- `cascade="all, delete-orphan"` - deletes actions if feedback deleted

**Lines 25-28**: Composite indexes
- Index on (department, status) for filtering
- Index on (created_at, status) for time-based queries

### `app/models/analysis.py` (32 lines)

**Lines 1-3**: SQLAlchemy imports
- `JSON` for JSON columns
- `Float` for confidence score
- `ForeignKey` for relationships

**Lines 7-31**: `Analysis` model
- **Line 8**: Table name: "analysis"
- **Line 11**: `feedback_id` - foreign key, unique (one-to-one)
- **Line 12**: `sentiment` - required, indexed
- **Line 13**: `confidence_score` - float, required
- **Line 14**: `emotions` - JSON array, optional
- **Line 15**: `urgency` - required, indexed
- **Line 16**: `urgency_reason` - text, optional
- **Line 17**: `urgency_flags` - JSON array, optional
- **Line 18**: `primary_category` - optional, indexed
- **Line 19**: `subcategories` - JSON array, optional
- **Line 20**: `medical_concerns` - JSON object, optional
- **Line 21**: `actionable_insights` - text, optional
- **Line 22**: `key_points` - JSON array, optional
- **Line 23**: `analyzed_at` - string (ISO format), optional

**Line 25**: Relationship back to Feedback

**Lines 27-30**: Composite indexes
- Index on (urgency, sentiment)
- Index on (primary_category, urgency)

### `app/models/actions.py` (21 lines)

**Lines 1-4**: SQLAlchemy imports

**Lines 8-20**: `Action` model
- **Line 9**: Table name: "actions"
- **Line 12**: `feedback_id` - foreign key to feedback
- **Line 13**: `staff_note` - optional text
- **Line 14**: `status` - required string
- **Line 15**: `assigned_department` - optional
- **Line 16**: `created_at` - auto-set
- **Line 17**: `updated_at` - auto-updated

**Line 19**: Relationship back to Feedback

---

## Services

### `app/services/auth_service.py` (106 lines)

**Lines 1-9**: Imports
- `datetime`, `timedelta` for token expiration
- `secrets` for key generation
- `passlib` for password hashing (bcrypt)
- `jose` for JWT encoding/decoding
- SQLAlchemy async operations

**Line 15**: Password context with bcrypt scheme

**Line 16**: Logger

**Lines 18-20**: JWT configuration constants
- Algorithm: HS256
- Access token: 60 minutes
- Refresh token: 7 days

**Lines 23-40**: `get_secret_key()` function
- **Line 24**: Gets SECRET_KEY from environment
- **Lines 25-29**: Raises if not set with helpful message
- **Lines 30-36**: Rejects common insecure placeholders
- **Lines 38-39**: Requires minimum 32 characters
- **Line 40**: Returns validated secret key

**Lines 43-46**: `generate_secret_key()` function
- Generates 64-byte URL-safe token
- Logs generation
- Returns key string

**Lines 49-50**: `hash_password()` function
- Uses passlib bcrypt context
- Returns hashed password string

**Lines 53-54**: `verify_password()` function
- Verifies plain password against hash
- Returns boolean

**Lines 57-62**: `create_access_token()` function
- **Line 58**: Copies data dict
- **Line 59**: Sets expiration (default 60 minutes)
- **Line 60**: Adds "exp" and "type" claims
- **Line 61**: Encodes JWT with secret key
- **Line 62**: Returns token string

**Lines 65-70**: `create_refresh_token()` function
- Similar to access token but 7-day expiration
- Type: "refresh"

**Lines 73-75**: `get_user_by_email()` function
- Async database query
- Returns User or None

**Lines 78-80**: `get_user_count()` function
- Counts total users in database
- Returns integer

**Lines 83-91**: `create_user()` function
- **Line 84**: Checks if user already exists
- **Line 85-86**: Returns error if exists
- **Line 87**: Creates new User with hashed password
- **Line 88**: Adds to session
- **Line 89**: Commits transaction
- **Line 90**: Refreshes to get ID
- **Line 91**: Returns (User, None) or (None, error_message)

**Lines 94-104**: `ensure_admin_user()` function
- **Lines 98-99**: Returns early if no email/password provided
- **Line 100**: Gets user count
- **Line 101-102**: Returns if users already exist
- **Line 103**: Creates admin user (bootstrap mode)

### `app/services/feedback_service.py` (332 lines)

**Lines 1-18**: Imports
- Business logic imports
- SQLAlchemy query building
- Model imports
- Gemini service
- Helper functions

**Line 20**: Logger

**Lines 23-24**: `FeedbackService` class (static methods only)

**Lines 27-49**: `create_feedback()` method
- **Lines 36-44**: Creates Feedback object
  - Sets status to "pending_analysis"
- **Line 45**: Adds to session
- **Line 46**: Commits
- **Line 47**: Refreshes to get ID
- **Line 48**: Logs creation
- **Line 49**: Returns feedback

**Lines 52-58**: `get_feedback_by_id()` method
- Uses `selectinload` to eagerly load relationships
- Returns Feedback with analysis and actions loaded
- Returns None if not found

**Lines 61-116**: `get_all_feedback()` method
- **Lines 73-74**: Base query and count query
- **Lines 76-84**: Builds filter conditions
  - Department filter
  - Date range filters
  - Status filter
- **Lines 86-99**: Analysis-based filters
  - Joins Analysis table if needed
  - Priority (urgency) filter
  - Sentiment filter
  - Category filter (checks primary and subcategories)
- **Lines 101-103**: Applies conditions to both queries
- **Line 105**: Gets total count
- **Lines 108-113**: Applies ordering, limit, offset
- **Line 115**: Executes query
- **Line 116**: Returns (list, total_count) tuple

**Lines 119-166**: `analyze_feedback_async()` method
- **Lines 120-123**: Gets feedback, returns None if not found
- **Lines 125-126**: Returns existing analysis if present
- **Lines 128-134**: Calls Gemini service with retry
- **Lines 136-140**: Handles analysis errors
- **Lines 142-155**: Creates Analysis object from result
  - Extracts all fields from Gemini response
  - Sets urgency, sentiment, etc.
- **Line 156**: Adds to session
- **Line 157**: Updates feedback status to "reviewed"
- **Line 158**: Commits
- **Line 159**: Refreshes analysis
- **Lines 160-165**: Logs success
- **Line 166**: Returns analysis

**Lines 169-191**: `update_feedback_status()` method
- **Line 176**: Gets feedback
- **Line 177-178**: Returns None if not found
- **Line 180**: Updates status
- **Lines 181-186**: Creates Action record
  - Tracks status change
  - Stores staff note
  - Assigns department
- **Line 187**: Adds action
- **Line 188**: Commits
- **Line 189**: Refreshes feedback
- **Line 190**: Logs update
- **Line 191**: Returns feedback

**Lines 194-199**: `mark_analysis_failed()` method
- Updates feedback status to "analysis_failed"
- Uses SQLAlchemy update statement
- Logs error

**Lines 202-247**: `get_analytics_summary()` method
- **Lines 203-204**: Total feedback count
- **Lines 206-210**: Sentiment breakdown
  - Groups by sentiment, counts
- **Lines 212-228**: Department ratings
  - Groups by department
  - Calculates average rating
  - Counts feedback per department
- **Lines 230-240**: Top issues
  - Groups by primary_category
  - Orders by count descending
  - Limits to top 10
- **Lines 242-247**: Returns summary dict

**Lines 250-315**: `get_analytics_trends()` method
- **Line 251**: Calculates start date (N days ago)
- **Lines 253-268**: Sentiment trends
  - Groups by date and sentiment
  - Returns dict: {date: {sentiment: count}}
- **Lines 270-285**: Category trends
  - Groups by date and category
  - Returns dict: {date: {category: count}}
- **Lines 287-309**: Department performance
  - Groups by department
  - Calculates average rating
  - Counts total feedback
  - Counts critical feedback (using CASE statement)
- **Lines 311-315**: Returns trends dict

**Lines 318-330**: `retry_failed_analyses()` method
- **Line 319**: Queries failed feedback
- **Line 321**: Gets all failed feedbacks
- **Line 323**: Retries up to max_retries
- **Line 324**: Analyzes feedback
- **Lines 325-327**: Updates status if successful
- **Line 328**: Increments counter
- **Line 329**: Commits all changes
- **Line 330**: Returns count of retried

### `app/services/gemini_service.py` (180 lines)

**Lines 1-12**: Imports
- `asyncio` for sleep in retries
- `httpx` for async HTTP requests
- Helper functions for parsing

**Line 24**: Load environment variables

**Line 25**: Logger

**Lines 28-38**: `GeminiService` class initialization
- **Line 32**: Gets API key from env
- **Lines 33-35**: Base URL (defaults to Google's API)
- **Line 37**: Model name (default "gemini-2.5-flash")
- **Line 38**: Timeout in seconds (default 30)

**Lines 40-97**: `analyze_feedback()` method
- **Lines 49-51**: Returns error if API key missing
- **Lines 53-59**: Generates prompt using template
- **Line 62**: Constructs API URL
- **Lines 63-66**: Sets headers with API key
- **Lines 67-70**: Payload with prompt and safety settings
- **Lines 72-76**: Makes async HTTP POST request
  - Uses httpx.AsyncClient
  - Raises on HTTP errors
- **Lines 78-90**: Handles HTTP errors
  - Logs status code and error text
  - Special handling for 429 (rate limit)
  - Returns retry flag for 5xx errors
- **Lines 91-93**: Handles timeout
- **Lines 94-96**: Handles unexpected errors
- **Line 98**: Extracts text from response
- **Lines 99-100**: Returns error if no text
- **Line 102**: Parses JSON from response
- **Lines 103-105**: Returns error if parse fails
- **Lines 107-119**: Builds result dict
  - Extracts sentiment, confidence, emotions
  - Uses helper functions for urgency extraction
  - Extracts categories and medical concerns
- **Lines 121-123**: Extracts category data
- **Lines 124-126**: Extracts medical concerns
- **Lines 128-132**: Logs completion
- **Line 133**: Returns result

**Lines 135-161**: `analyze_feedback_with_retry()` method
- **Line 145**: Initializes last_result
- **Line 146**: Retries up to max_retries times
- **Lines 147-153**: Calls analyze_feedback
- **Lines 154-155**: Returns if successful
- **Line 156**: Stores last result
- **Lines 157-158**: Returns if not retryable
- **Line 159**: Calculates wait time (exponential backoff or retry_after)
- **Line 160**: Sleeps before retry
- **Line 161**: Returns last result (error)

**Lines 163-175**: `_extract_text()` static method
- **Line 165**: Gets candidates from response
- **Line 166**: Returns None if no candidates
- **Lines 168-171**: Extracts parts from first candidate
- **Line 172**: Returns None if no parts
- **Line 175**: Returns text from first part

**Line 178**: Creates singleton instance

---

## Routers

### `app/routers/auth.py` (96 lines)

**Lines 1-18**: Imports
- FastAPI router components
- Pydantic models
- JWT handling
- Auth service functions

**Line 21**: Router with prefix "/auth"

**Lines 24-27**: `RegisterRequest` model
- Email (validated)
- Password (min 6 chars)
- Role (optional, must be "admin" or "staff")

**Lines 30-32**: `LoginRequest` model
- Email and password

**Lines 35-39**: `TokenResponse` model
- Access token, refresh token, type, role

**Lines 42-59**: `/register` endpoint
- **Line 46**: Optional current_user (for bootstrap check)
- **Line 53**: Gets total user count
- **Line 54**: If users exist, requires admin role
- **Line 56**: Creates user
- **Line 57-58**: Handles creation errors
- **Line 59**: Returns user info (no password)

**Lines 62-69**: `/login` endpoint
- **Line 64**: Gets user by email
- **Line 65**: Verifies password
- **Line 66**: Raises 401 if invalid
- **Line 67**: Creates access token
- **Line 68**: Creates refresh token
- **Line 69**: Returns tokens and role

**Lines 72-73**: `decode_token()` helper
- Decodes JWT for /me endpoint

**Lines 76-93**: `/me` endpoint
- **Line 77**: Gets authorization header
- **Lines 81-82**: Validates Bearer scheme
- **Line 83**: Extracts token
- **Lines 84-88**: Decodes and validates token
- **Line 90**: Gets user from database
- **Lines 91-92**: Returns 401 if not found
- **Line 93**: Returns user info

### `app/routers/feedback.py` (410 lines)

**Lines 1-19**: Imports
- Router components
- CSV generation
- Background tasks
- Pydantic models
- Socket.IO events

**Line 22**: Router with prefix "/feedback"

**Lines 26-38**: `FeedbackCreate` model
- All feedback fields
- Validators for rating (1-5)
- Minimum feedback text length (10 chars)

**Lines 41-44**: `FeedbackUpdate` model
- Status (validated pattern)
- Optional staff note
- Optional assigned department

**Lines 47-59**: `FeedbackResponse` model
- All feedback fields
- `from_attributes = True` for ORM conversion

**Lines 62-78**: `AnalysisResponse` model
- All analysis fields

**Lines 81-83**: `FeedbackDetailResponse` model
- Extends FeedbackResponse
- Includes analysis and actions

**Lines 86-117**: `POST /feedback` endpoint
- **Line 89**: BackgroundTasks for async work
- **Lines 94-102**: Creates feedback via service
- **Line 105**: Emits Socket.IO event
- **Lines 108-111**: Adds background analysis task
- **Line 113**: Returns feedback
- **Lines 115-117**: Error handling

**Lines 120-137**: `analyze_feedback_background()` function
- **Line 122**: Creates new database session
- **Lines 124-131**: Analyzes feedback
  - Emits analysis_complete event
  - Emits urgent_alert if critical
- **Lines 132-133**: Marks as failed if analysis fails
- **Lines 135-137**: Exception handling

**Lines 140-213**: `GET /feedback/all` endpoint
- **Lines 141**: Requires admin/staff role
- **Lines 142-151**: Query parameters for filtering
- **Lines 156-167**: Gets feedback via service
- **Lines 170-192**: Converts to response format
  - Handles missing analysis gracefully
  - Skips problematic items
- **Lines 194-199**: Builds response dict
- **Lines 201-207**: CSV export support
  - Streaming response
  - Sets Content-Disposition header
- **Line 209**: Returns JSON response
- **Lines 211-213**: Error handling

**Lines 216-261**: `GET /feedback/urgent` endpoint
- **Lines 217**: Requires admin/staff role
- **Lines 223-227**: Gets critical feedback
- **Lines 230-252**: Converts to response format
  - Includes urgency details
  - Includes actionable insights
- **Lines 255-258**: Returns response
- **Lines 259-261**: Error handling

**Lines 264-319**: `GET /feedback/{id}` endpoint
- **Lines 264**: Requires admin/staff role
- **Line 270**: Gets feedback
- **Lines 272-273**: Returns 404 if not found
- **Lines 276-288**: Builds response dict
- **Lines 290-305**: Adds analysis if present
- **Lines 307-317**: Adds actions if present
- **Line 319**: Returns response

**Lines 322-340**: `POST /feedback/{id}/update` endpoint
- **Lines 322**: Requires admin/staff role
- **Lines 329-335**: Updates feedback via service
- **Lines 337-338**: Returns 404 if not found
- **Line 340**: Returns updated feedback

**Lines 343-365**: `POST /feedback/{id}/retry-analysis` endpoint
- **Lines 343**: Requires admin/staff role
- **Line 350**: Gets feedback
- **Lines 351-352**: Returns 404 if not found
- **Lines 354-357**: Resets status if failed
- **Lines 360-363**: Triggers background analysis
- **Line 365**: Returns success message

**Lines 368-408**: `generate_feedback_csv()` generator
- **Line 370**: Creates StringIO buffer
- **Lines 371-384**: Defines CSV columns
- **Line 385**: Creates DictWriter
- **Line 386**: Writes header
- **Line 387**: Yields header
- **Lines 388-389**: Clears buffer
- **Lines 391-405**: Writes each row
  - Handles None values
  - Yields each row
  - Clears buffer after each row

### `app/routers/analytics.py` (39 lines)

**Lines 1-10**: Imports

**Line 12**: Router with prefix "/analytics"

**Lines 15-24**: `GET /analytics/summary` endpoint
- **Line 15**: Requires admin/staff role
- **Line 21**: Gets summary via service
- **Line 22**: Returns summary
- **Lines 23-24**: Error handling

**Lines 27-37**: `GET /analytics/trends` endpoint
- **Line 27**: Requires admin/staff role
- **Line 29**: Days parameter (1-365, default 30)
- **Line 34**: Gets trends via service
- **Line 35**: Returns trends
- **Lines 36-37**: Error handling

### `app/routers/health.py` (43 lines)

**Lines 1-10**: Imports

**Line 12**: Router with prefix "/health"

**Lines 15-25**: `GET /health` endpoint
- **Line 18**: Checks database connection
- **Line 19**: Gets pool stats
- **Lines 21-25**: Returns health status
  - Service name
  - Status (healthy/degraded)
  - Database connection status
  - Pool statistics

**Lines 28-40**: `GET /health/ping` endpoint
- **Line 31**: Initializes latency
- **Lines 33-36**: Measures database query time
  - Uses perf_counter for precision
  - Executes SELECT 1
- **Line 37**: Calculates latency in milliseconds
- **Lines 38-39**: Handles errors gracefully
- **Line 40**: Returns status and latency

---

## Utilities

### `app/utils/errors.py` (87 lines)

**Lines 1-11**: Imports

**Line 13**: Logger

**Lines 16-30**: `APIError` base class
- **Lines 19-25**: Constructor with message, status_code, code, details
- **Line 30**: Calls parent Exception constructor

**Lines 33-35**: `ValidationError` class
- Extends APIError
- Status 400, code "VALIDATION_ERROR"

**Lines 38-45**: `NotFoundError` class
- Extends APIError
- Status 404, code "NOT_FOUND"
- Includes resource and identifier in details

**Lines 48-50**: `ForbiddenError` class
- Extends APIError
- Status 403, code "FORBIDDEN"

**Lines 53-60**: `RateLimitError` class
- Extends APIError
- Status 429, code "RATE_LIMIT"
- Includes retry_after in details

**Lines 63-73**: `api_error_handler()` function
- **Lines 64-69**: Logs error with context
- **Lines 70-73**: Returns JSON response
  - Structured error format
  - Includes code, message, details

**Lines 76-84**: `generic_error_handler()` function
- **Lines 77-79**: Re-raises HTTPException (let FastAPI handle)
- **Line 80**: Logs unhandled exceptions
- **Lines 81-84**: Returns 500 error
  - Generic message (security: doesn't leak details)

### `app/utils/helpers.py` (92 lines)

**Lines 1-7**: Imports
- Type hints
- JSON parsing
- Regex for cleaning

**Lines 10-12**: `validate_rating()` function
- Checks rating is 1-5
- Returns boolean

**Lines 15-19**: `format_datetime()` function
- Converts datetime to ISO string
- Returns None if input is None

**Lines 22-32**: `parse_json_safely()` function
- **Lines 26-28**: Removes markdown code blocks
- **Line 29**: Strips whitespace
- **Line 30**: Parses JSON
- **Line 31**: Returns None on error

**Lines 35-39**: `extract_urgency_level()` function
- Extracts "level" from urgency dict
- Returns "low" as default

**Lines 42-46**: `extract_urgency_reason()` function
- Extracts "reason" from urgency dict
- Returns None if not found

**Lines 49-54**: `extract_urgency_flags()` function
- Extracts "flags" array from urgency dict
- Returns empty list if not found

**Lines 57-65**: `extract_categories()` function
- Extracts primary and subcategories
- Returns tuple (primary, subcategories)
- Handles missing data

**Lines 68-77**: `extract_medical_concerns()` function
- Extracts structured medical concerns
- Returns dict with symptoms, complications, etc.
- Returns None if not found

**Lines 80-82**: `is_critical_urgency()` function
- Checks if urgency is "critical"
- Case-insensitive

**Lines 85-90**: `format_error_response()` function
- Formats error for API response
- Includes message and optional details

### `app/utils/prompts.py` (64 lines)

**Lines 5-51**: `FEEDBACK_ANALYSIS_PROMPT` template
- Multi-line string with placeholders
- Instructions for Gemini AI
- JSON structure specification
- Guidelines for analysis

**Lines 54-62**: `get_analysis_prompt()` function
- **Line 56**: Formats prompt template
- **Lines 57-61**: Fills in placeholders
  - feedback_text
  - department
  - doctor_name (defaults to "Not specified")
  - visit_date (defaults to "Not specified")
  - rating (defaults to "Not specified")
- **Line 62**: Returns formatted prompt

---

## Socket.IO Events

### `app/sockets/events.py` (124 lines)

**Lines 1-14**: Imports
- Socket.IO server
- JWT handling
- Model imports
- Auth service

**Line 18**: Creates AsyncServer
- `async_mode="asgi"` for ASGI compatibility
- `cors_allowed_origins="*"` - WIDE OPEN (security risk!)

**Line 20**: Tracks connected client IDs

**Line 21**: Staff room name constant

**Lines 24-30**: `_extract_token()` helper
- **Line 25**: Checks if auth is dict
- **Line 27**: Gets token from "token" or "Authorization" key
- **Line 28**: Checks Bearer scheme
- **Line 29**: Extracts token string
- **Line 30**: Returns token or None

**Lines 33-48**: `connect` event handler
- **Line 35**: Extracts token from auth
- **Lines 37-45**: Validates token and role
  - Decodes JWT
  - Checks role is admin or staff
  - Joins staff_room
  - Adds to connected_clients
  - Emits welcome message
- **Lines 46-47**: Handles JWT errors
- **Line 48**: Disconnects if invalid

**Lines 51-54**: `disconnect` event handler
- Removes client from tracking set
- Logs disconnection

**Lines 57-59**: `request_updates` event handler
- Confirms updates are enabled
- Emits to specific client

**Lines 62-70**: `staff_action` event handler
- Broadcasts staff actions to all staff
- Includes feedback_id, action, staff_id

**Lines 73-86**: `emit_new_feedback()` function
- **Lines 74-84**: Builds feedback data dict
  - Includes id, patient_name, department, rating, status
  - Truncates feedback_text to 100 chars
- **Line 85**: Emits to staff_room
- **Line 86**: Logs emission

**Lines 89-105**: `emit_urgent_alert()` function
- **Lines 90-103**: Builds alert data dict
  - Includes feedback and analysis details
  - Truncates feedback_text to 200 chars
- **Line 104**: Emits to staff_room
- **Line 105**: Logs warning

**Lines 108-117**: `emit_analysis_complete()` function
- **Lines 109-115**: Builds analysis data dict
  - Includes sentiment, urgency, category, confidence
- **Line 116**: Emits to staff_room
- **Line 117**: Logs emission

**Lines 120-122**: `emit_dashboard_stats_update()` function
- Emits stats update to staff_room
- Logs emission

---

## Frontend Files

### `frontend/index.html` (309 lines)

**Lines 1-10**: HTML head
- Meta tags for charset and viewport
- Title
- CSS links (styles.css, Google Fonts, Font Awesome)

**Lines 12-20**: Header section
- Title with icon
- Subtitle
- Auth controls container (populated by JS)

**Lines 23-36**: Navigation tabs
- Submit Feedback tab
- Dashboard tab
- Urgent Feedback tab (with urgent indicator)
- Analytics tab

**Line 39**: Alert container

**Lines 42-54**: Confirmation message (hidden by default)
- Success icon
- Thank you message
- Reset form button

**Lines 57-113**: Feedback form
- Patient name (optional)
- Visit date (required)
- Department dropdown (required)
- Doctor name (optional)
- Feedback text (required, min 10 chars)
- Rating slider (1-5)
- Submit button

**Lines 117-194**: Dashboard tab
- Header with filters
  - Department filter
  - Status filter
  - Urgency filter
  - Refresh button
- Critical alerts banner container
- Feedback table
  - Columns: ID, Patient, Department, Feedback, Rating, Status, Sentiment, Urgency, Actions
- Stats bar
  - Total count
  - Critical count
  - Pending count

**Lines 197-205**: Urgent Feedback tab
- Header
- Feedback list container

**Lines 208-253**: Analytics tab
- Stats grid
  - Total feedback card
  - Positive sentiment card
  - Negative sentiment card
  - Critical issues card
- Department performance section
- Top issues section

**Lines 256-262**: Feedback detail modal
- Close button
- Modal body (populated by JS)

**Lines 265-302**: Staff action modal
- Form with:
  - Hidden feedback ID
  - Status dropdown
  - Staff note textarea
  - Assigned department dropdown
  - Save button

**Lines 304-305**: Script tags
- Socket.IO client library
- app.js

### `frontend/staff_login.html` (77 lines)

**Lines 1-7**: HTML head
- Meta tags
- Title
- Google Fonts

**Lines 8-22**: Inline CSS
- Dark theme styling
- Card layout
- Form styling
- Button styling
- Alert styling

**Lines 24-41**: Body
- Login card
  - Title
  - Description
  - Form with email and password
  - Submit button
  - Alert container
  - Hint text with link to home

**Lines 42-72**: JavaScript
- **Line 43**: Gets API base URL
- **Line 44**: Gets form element
- **Line 45**: Gets alert box
- **Lines 46-70**: Form submit handler
  - Prevents default
  - Hides alert
  - Gets email and password
  - **Lines 52-56**: POSTs to /auth/login
  - **Lines 57-59**: Handles errors
  - **Lines 61-66**: On success:
    - Stores access_token in localStorage
    - Stores role in localStorage
    - Redirects to home page
  - **Lines 67-69**: On error:
    - Shows error message

### `frontend/app.js` (716 lines)

**Lines 1-6**: Constants
- API_BASE from window.location.origin
- Socket.IO connection with token auth
- Sentiment and urgency class arrays

**Lines 11-20**: SecurityUtils object
- `escapeHtml()`: XSS prevention
- `safeClass()`: Validates CSS classes

**Lines 22-26**: `redirectToLogin()` function
- Removes token
- Shows alert
- Redirects after 1 second

**Lines 28-41**: `renderAuthControls()` function
- Renders logout button if authenticated
- Renders login link if not authenticated

**Lines 44-106**: DOMContentLoaded handler
- **Line 45**: Checks if staff (has token)
- **Line 47**: Renders auth controls
- **Lines 50-58**: Gets tab elements
- **Lines 60-83**: Shows/hides tabs based on role
  - Staff: hides submit tab
  - Patient: hides staff tabs
- **Lines 86-88**: Sets default visit date to today
- **Lines 91-99**: Loads initial data based on active tab
- **Lines 102-106**: Auto-refreshes urgent tab every 30 seconds

**Lines 108-143**: Socket.IO event listeners
- **Lines 109-112**: Connect event
- **Lines 114-120**: new_feedback event
  - Shows alert
  - Refreshes dashboard if active
- **Lines 122-132**: urgent_alert event
  - Shows critical alert banner
  - Shows alert
  - Refreshes dashboard and urgent tab
- **Lines 134-143**: analysis_complete event
  - Shows alert
  - Refreshes active tabs

**Lines 146-169**: `showTab()` function
- Hides all tabs
- Shows selected tab
- Loads data for tab

**Lines 172-176**: `updateRatingDisplay()` function
- Updates rating value and stars

**Lines 179-211**: Feedback form submit handler
- **Lines 182-189**: Gets form data
- **Lines 192-198**: POSTs to /feedback
- **Lines 200-203**: On success, shows confirmation
- **Lines 204-210**: On error, shows alert

**Lines 214-217**: `showConfirmation()` function
- Hides form, shows confirmation

**Lines 220-228**: `resetForm()` function
- Resets form
- Hides confirmation
- Resets date to today

**Lines 231-275**: `loadFeedback()` function
- **Line 232**: Gets table body
- **Line 233**: Shows loading message
- **Lines 235-237**: Gets filter values
- **Lines 240-243**: Builds URL with filters
- **Lines 245-247**: Adds auth header if token exists
- **Line 248**: Fetches data
- **Lines 249-251**: Handles 401 (redirects to login)
- **Lines 253-263**: Renders feedback rows
  - Counts critical and pending
- **Lines 265-268**: Updates stats
- **Lines 270-274**: Error handling

**Lines 278-331**: `createFeedbackTableRow()` function
- **Line 279**: Creates table row
- **Line 280**: Adds critical-row class if urgent
- **Lines 284-286**: Truncates feedback text
- **Lines 287-288**: Validates CSS classes
- **Lines 290-328**: Builds row HTML
  - Escapes all user input
  - Shows badges for status, sentiment, urgency
  - Adds action buttons
  - Shows retry button if analysis failed

**Lines 334-386**: `loadUrgentFeedback()` function
- **Line 335**: Gets container
- **Lines 336-339**: Error handling if container missing
- **Line 341**: Shows loading
- **Lines 344-350**: Checks for token
- **Line 353**: Fetches urgent feedback
- **Lines 356-359**: Handles 401
- **Lines 361-366**: Handles non-OK responses
- **Line 368**: Parses JSON
- **Lines 371-377**: Renders urgent items
- **Lines 378-380**: Shows "no urgent" message
- **Lines 382-385**: Error handling

**Lines 389-435**: `createUrgentFeedbackItem()` function
- **Line 390**: Creates div element
- **Line 391**: Adds critical class
- **Lines 393-395**: Formats urgency flags
- **Line 396**: Validates sentiment class
- **Lines 398-432**: Builds HTML
  - Escapes all user input
  - Shows critical badge
  - Shows urgency reason
  - Shows actionable insights
  - Shows action buttons

**Lines 438-459**: `showCriticalAlert()` function
- **Line 439**: Gets container
- **Line 440**: Creates alert element
- **Line 441**: Adds critical-alert-banner class
- **Lines 442-452**: Builds HTML
  - Escapes user input
  - Shows preview
  - Shows view button
- **Line 453**: Appends to container
- **Lines 456-458**: Auto-removes after 10 seconds

**Lines 462-465**: `openActionModal()` function
- Sets feedback ID
- Shows modal

**Lines 468-471**: `closeActionModal()` function
- Hides modal
- Resets form

**Lines 474-511**: Action form submit handler
- **Lines 477-480**: Gets form data
- **Lines 483-493**: POSTs to /feedback/{id}/update
- **Lines 495-502**: On success:
  - Shows alert
  - Closes modal
  - Refreshes feedback
  - Refreshes urgent tab if active
- **Lines 503-510**: Error handling

**Lines 514-587**: `viewFeedback()` function
- **Lines 516-518**: Adds auth header
- **Line 519**: Fetches feedback details
- **Lines 520-522**: Handles 401
- **Lines 524-525**: Gets modal elements
- **Lines 527-565**: Builds analysis HTML
  - Shows sentiment with confidence
  - Shows urgency level
  - Shows urgency reason
  - Shows actionable insights
  - Shows key points
- **Lines 568-580**: Builds feedback HTML
  - Escapes all user input
  - Shows all feedback fields
- **Line 581**: Adds analysis HTML
- **Line 583**: Shows modal
- **Lines 584-586**: Error handling

**Lines 590-592**: `closeModal()` function
- Hides feedback modal

**Lines 595-604**: Window click handler
- Closes modals when clicking outside

**Lines 607-663**: `loadAnalytics()` function
- **Lines 609-610**: Adds auth header
- **Lines 611-614**: Fetches summary and trends in parallel
- **Line 615**: Handles 401
- **Lines 617-618**: Parses JSON
- **Lines 621-626**: Updates stats
  - Total feedback
  - Positive count
  - Negative count
  - Critical count (N/A - not in summary)
- **Lines 629-645**: Renders department ratings
- **Lines 648-658**: Renders top issues
- **Lines 659-662**: Error handling

**Lines 666-682**: `showAlert()` function
- **Line 667**: Gets container
- **Line 668**: Creates alert element
- **Line 669**: Adds type class
- **Lines 670-673**: Creates icon based on type
- **Lines 674-675**: Creates message span
- **Lines 676-677**: Appends icon and message
- **Line 677**: Appends to container
- **Lines 679-681**: Auto-removes after 5 seconds

**Lines 685-711**: `retryAnalysis()` function
- **Lines 687-688**: Adds auth header
- **Lines 690-693**: POSTs to /feedback/{id}/retry-analysis
- **Lines 695-702**: On success:
  - Shows alert
  - Refreshes after 3 seconds
- **Lines 703-710**: Error handling

**Line 714**: Initializes rating display

### `frontend/styles.css` (764 lines)

**Lines 1-5**: CSS reset
- Margin, padding, box-sizing

**Lines 7-21**: CSS variables (root)
- Color scheme
- Background colors
- Text colors
- Border colors
- Shadow definitions

**Lines 23-28**: Body styles
- Font family (Inter)
- Background color
- Text color
- Line height

**Lines 30-34**: Container
- Max width 1400px
- Centered
- Padding

**Lines 36-44**: Header
- Gradient background
- White text
- Padding
- Border radius
- Shadow

**Lines 46-55**: Header content
- Large title
- Subtitle styling

**Lines 57-66**: Tabs container
- Flex layout
- Gap
- Background
- Padding
- Border radius
- Shadow

**Lines 68-83**: Tab button
- Flex layout
- Padding
- Transparent background
- Hover effects
- Active state (blue background)

**Lines 96-102**: Tab content
- Hidden by default
- Shown when active

**Lines 104-120**: Card
- White background
- Padding
- Border radius
- Shadow
- Margin

**Lines 122-164**: Forms
- Form group spacing
- Form row grid (2 columns)
- Label styling
- Input/select/textarea styling
- Focus states

**Lines 166-206**: Rating
- Container flex layout
- Range input styling
- Rating display
- Stars styling

**Lines 208-244**: Buttons
- Base button styles
- Primary button (blue)
- Secondary button (gray)
- Hover effects

**Lines 246-274**: Dashboard
- Header flex layout
- Filters flex layout
- Select styling

**Lines 276-377**: Feedback list
- Grid layout
- Item styling
- Critical/high urgency styling
- Badge styling
- Footer layout

**Lines 379-460**: Analytics
- Stats grid (responsive)
- Stat card layout
- Stat icon colors
- Analytics sections
- Department/issue lists

**Lines 462-496**: Modal
- Fixed positioning
- Backdrop
- Content centering
- Close button

**Lines 498-542**: Alerts
- Padding
- Border radius
- Flex layout
- Animation
- Color variants (success, error, warning, info)

**Lines 544-548**: Loading
- Centered text
- Padding
- Light text color

**Lines 550-587**: Confirmation
- Centered content
- Large success icon
- Animation
- Note styling

**Lines 589-627**: Table
- Container styling
- Table layout
- Header styling
- Row hover
- Critical row highlighting

**Lines 629-662**: Critical alerts
- Banner styling
- Gradient background
- Flex layout
- Animation

**Lines 664-695**: Stats bar
- Flex layout
- Centered
- Stat item layout
- Critical value color

**Lines 697-742**: Action buttons
- Flex layout
- Small button sizing
- View button (blue)
- Action button (green)
- Urgent tab indicator (pulsing dot)

**Lines 744-762**: Responsive
- Mobile breakpoint (768px)
- Single column forms
- Single column stats
- Vertical tabs

---

## Summary

### Architecture
- **Backend**: FastAPI with async SQLAlchemy
- **Database**: PostgreSQL with asyncpg driver
- **AI**: Google Gemini API via httpx
- **Real-time**: Socket.IO for WebSocket communication
- **Frontend**: Vanilla JavaScript with Socket.IO client
- **Authentication**: JWT tokens with role-based access control

### Key Features
1. **Feedback Submission**: Patients can submit feedback with ratings
2. **AI Analysis**: Automatic sentiment and urgency analysis using Gemini
3. **Real-time Alerts**: Socket.IO notifications for critical feedback
4. **Analytics Dashboard**: Comprehensive analytics and trends
5. **Staff Actions**: Track and manage feedback resolution
6. **CSV Export**: Export feedback data

### Security Considerations
- ⚠️ CORS is wide open (`allow_origins=["*"]`) - should be restricted in production
- ⚠️ Socket.IO CORS is wide open - should be restricted
- ✅ Password hashing with bcrypt
- ✅ JWT token authentication
- ✅ Role-based access control
- ✅ XSS prevention in frontend (escapeHtml)
- ✅ SQL injection prevention (SQLAlchemy ORM)
- ⚠️ SECRET_KEY validation (good)
- ⚠️ No rate limiting implemented

### Performance Considerations
- ✅ Async/await throughout
- ✅ Connection pooling configured
- ✅ Streaming CSV export
- ✅ Background tasks for AI analysis
- ✅ Database indexes on frequently queried columns
- ⚠️ No caching layer
- ⚠️ No task queue (Celery/Redis) for heavy workloads

### Code Quality
- ✅ Good separation of concerns
- ✅ Comprehensive logging
- ✅ Error handling
- ✅ Type hints (mostly)
- ✅ Docstrings (some files)
- ⚠️ Some magic numbers/strings could be constants
- ⚠️ Some error messages could be more specific

### Testing
- ❌ No test files found
- ⚠️ Some `# pragma: no cover` comments indicate untested code

### Deployment Readiness
- ✅ Environment variable configuration
- ✅ Health check endpoints
- ✅ Logging configured
- ⚠️ CORS needs restriction
- ⚠️ No HTTPS enforcement
- ⚠️ No monitoring/alerting setup
- ⚠️ Database migrations not automated (Alembic)

