# Changelog

## [Unreleased]

### Added
- Security-focused environment template (`env.example`) and git ignore rules.
- Centralized logging configuration with console and file handlers.
- Structured error handling utilities and request logging middleware.
- Health endpoint with database connectivity and pool statistics.

### Changed
- Replaced Gemini analysis calls with true async HTTP client implementation.
- Refactored background tasks to create independent database sessions.
- Hardened authentication by validating `SECRET_KEY` and tightening Socket.IO auth handling.
- Optimized SQL queries with server-side filtering and added database indexes.
- Updated frontend to escape user-provided content to prevent XSS.
- Streamed CSV exports to avoid high memory usage.

### Fixed
- Database connection leaks, pool exhaustion, and fake async design.
- Multiple cross-site scripting vectors and insecure frontend rendering.
- Production readiness gaps around logging, configuration, and documentation accuracy.


