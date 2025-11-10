"""
Socket.IO event handlers for real-time alerts
"""
import socketio
from typing import Optional
from jose import jwt, JWTError
import os
from app.models.feedback import Feedback
from app.models.analysis import Analysis

# Create Socket.IO server
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins="*"  # Configure appropriately for production
)

# Store for connected clients (for broadcasting)
connected_clients = set()
STAFF_ROOM = "staff_room"
SECRET_KEY = os.getenv("SECRET_KEY", "change-this-in-production")


@sio.event
async def connect(sid, environ, auth):
    """Handle client connection"""
    # Expect auth like { token: "Bearer <jwt>" }
    token = None
    try:
        if isinstance(auth, dict):
            bearer = auth.get("token") or auth.get("Authorization")
            if bearer and bearer.lower().startswith("bearer "):
                token = bearer.split(" ", 1)[1]
        if token:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            role = payload.get("role", "")
            if role in ("admin", "staff"):
                await sio.enter_room(sid, STAFF_ROOM)
                connected_clients.add(sid)
                print(f"Staff connected: {sid} (role={role})")
                await sio.emit('connected', {'message': 'Connected to staff updates'}, room=sid)
                return
    except JWTError:
        pass

    # No/invalid token → reject connection (patients don't need sockets)
    print(f"Rejected socket connection (no/invalid auth): {sid}")
    await sio.disconnect(sid)


@sio.event
async def disconnect(sid):
    """Handle client disconnection"""
    connected_clients.discard(sid)
    print(f"Client disconnected: {sid}")


@sio.event
async def request_updates(sid, data):
    """Handle client request for real-time updates"""
    # Client can request to receive updates
    await sio.emit('updates_enabled', {'message': 'You will receive real-time updates'}, room=sid)


@sio.event
async def staff_action(sid, data):
    """Handle staff action on feedback"""
    # Staff can send actions (reviewed/resolved)
    feedback_id = data.get('feedback_id')
    action = data.get('action')
    
    # Broadcast action to all connected clients
    await sio.emit('staff_action_update', {
        'feedback_id': feedback_id,
        'action': action,
        'staff_id': sid
    }, room=STAFF_ROOM)


async def emit_new_feedback(feedback: Feedback):
    """Emit new feedback event to all connected clients"""
    feedback_data = {
        'id': feedback.id,
        'patient_name': feedback.patient_name,
        'department': feedback.department,
        'rating': feedback.rating,
        'status': feedback.status,
        'created_at': feedback.created_at.isoformat() if feedback.created_at else None,
        'preview': feedback.feedback_text[:100] + '...' if len(feedback.feedback_text) > 100 else feedback.feedback_text
    }
    
    await sio.emit('new_feedback', feedback_data, room=STAFF_ROOM)
    print(f"Emitted new_feedback event for feedback {feedback.id}")


async def emit_urgent_alert(feedback: Feedback, analysis: Analysis):
    """Emit urgent alert for critical feedback"""
    alert_data = {
        'feedback_id': feedback.id,
        'patient_name': feedback.patient_name,
        'department': feedback.department,
        'urgency': analysis.urgency,
        'urgency_reason': analysis.urgency_reason,
        'urgency_flags': analysis.urgency_flags,
        'sentiment': analysis.sentiment,
        'primary_category': analysis.primary_category,
        'feedback_preview': feedback.feedback_text[:200] + '...' if len(feedback.feedback_text) > 200 else feedback.feedback_text,
        'created_at': feedback.created_at.isoformat() if feedback.created_at else None
    }
    
    await sio.emit('urgent_alert', alert_data, room=STAFF_ROOM)
    print(f"Emitted urgent_alert for critical feedback {feedback.id}")


async def emit_analysis_complete(feedback_id: int, analysis: Analysis):
    """Emit analysis complete event"""
    analysis_data = {
        'feedback_id': feedback_id,
        'sentiment': analysis.sentiment,
        'urgency': analysis.urgency,
        'primary_category': analysis.primary_category,
        'confidence_score': analysis.confidence_score
    }
    
    await sio.emit('analysis_complete', analysis_data, room=STAFF_ROOM)
    print(f"Emitted analysis_complete for feedback {feedback_id}")


async def emit_dashboard_stats_update(stats: dict):
    """Emit dashboard stats update"""
    await sio.emit('dashboard_stats_update', stats, room=STAFF_ROOM)
    print("Emitted dashboard_stats_update")

