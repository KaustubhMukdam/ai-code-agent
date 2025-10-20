"""
Real-time notifications via WebSocket
"""
import socketio
from src.api.auth import decode_jwt_token
from src.api.models import get_db, Job
import asyncio

# Create Socket.IO server
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins="*")

# Store active connections
active_connections = {}

@sio.event
async def connect(sid, environ, auth):
    """Handle client connection"""
    try:
        # Authenticate user via token
        token = auth.get('token') if auth else None
        if not token:
            await sio.disconnect(sid)
            return False
            
        payload = decode_jwt_token(token)
        if not payload:
            await sio.disconnect(sid)
            return False
            
        user_id = payload.get("sub")
        active_connections[sid] = user_id
        
        # Join user to their personal room
        await sio.enter_room(sid, f"user_{user_id}")
        await sio.emit('connected', {'status': 'Connected to notifications'}, room=sid)
        
        print(f"User {user_id} connected via WebSocket")
        return True
        
    except Exception as e:
        print(f"Connection error: {e}")
        await sio.disconnect(sid)
        return False

@sio.event
async def disconnect(sid):
    """Handle client disconnect"""
    user_id = active_connections.pop(sid, None)
    if user_id:
        await sio.leave_room(sid, f"user_{user_id}")
        print(f"User {user_id} disconnected")

async def notify_job_status(user_id: int, job_id: str, status: str, message: str = None):
    """Send job status notification to user"""
    notification = {
        'job_id': job_id,
        'status': status,
        'message': message,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    await sio.emit('job_status', notification, room=f"user_{user_id}")

async def notify_system_alert(message: str, level: str = "info"):
    """Send system-wide notification"""
    alert = {
        'message': message,
        'level': level,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    await sio.emit('system_alert', alert)

# Create ASGI app
socket_app = socketio.ASGIApp(sio)
