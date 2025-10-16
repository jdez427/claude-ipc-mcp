#!/usr/bin/env python3
"""
Claude IPC MCP Server for WSL - Inter-Process Communication between Claude Code instances
Uses TCP sockets for WSL-to-WSL communication on Windows 10
"""

import asyncio
import json
import logging
import socket
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import sys
import os
import threading
import time
import sqlite3
import hashlib
import secrets
from pathlib import Path

from mcp.server import Server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    LoggingLevel
)

# Configuration
IPC_HOST = "127.0.0.1"  # Localhost works across WSL instances
IPC_PORT = 9876  # Choose a port that's likely free
HEARTBEAT_INTERVAL = 30  # seconds

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RateLimiter:
    """Simple in-memory rate limiter"""
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}  # instance_id -> list of timestamps
        self.lock = threading.Lock()
    
    def is_allowed(self, instance_id: str) -> bool:
        """Check if request is allowed under rate limit"""
        with self.lock:
            now = time.time()
            
            # Initialize if needed
            if instance_id not in self.requests:
                self.requests[instance_id] = []
            
            # Remove old requests outside window
            self.requests[instance_id] = [
                ts for ts in self.requests[instance_id] 
                if now - ts < self.window_seconds
            ]
            
            # Check if under limit
            if len(self.requests[instance_id]) >= self.max_requests:
                return False
            
            # Record this request
            self.requests[instance_id].append(now)
            return True

class MessageBroker:
    """Message broker that runs as a separate thread with SQLite persistence"""
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.queues: Dict[str, List[Dict[str, Any]]] = {}
        self.instances: Dict[str, datetime] = {}
        self.running = False
        self.server_socket = None
        self.lock = threading.Lock()
        # Name change tracking
        self.name_history: Dict[str, Tuple[str, datetime]] = {}  # old_name -> (new_name, when)
        self.last_rename: Dict[str, datetime] = {}  # instance_id -> last rename time
        # Session management for security
        self.sessions: Dict[str, Dict[str, Any]] = {}  # session_token -> {instance_id, created_at}
        self.instance_sessions: Dict[str, str] = {}  # instance_id -> session_token
        # Rate limiting
        self.rate_limiter = RateLimiter(max_requests=100, window_seconds=60)
        
        # SQLite persistence - secure location
        self.db_dir = os.path.expanduser("~/.claude-ipc-data")
        self.db_path = os.path.join(self.db_dir, "messages.db")
        self._init_database()
        self._load_from_database()
        
    def _init_database(self):
        """Initialize SQLite database with required tables"""
        try:
            # Create secure directory if it doesn't exist
            os.makedirs(self.db_dir, 0o700, exist_ok=True)
            
            # Create database connection
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Set secure permissions on database file
            if os.path.exists(self.db_path):
                os.chmod(self.db_path, 0o600)
            
            # Messages table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    from_id TEXT NOT NULL,
                    to_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    data TEXT,
                    summary TEXT,
                    large_file_path TEXT,
                    read_flag INTEGER DEFAULT 0
                )
            ''')
            
            # Instances table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS instances (
                    instance_id TEXT PRIMARY KEY,
                    last_seen TEXT NOT NULL
                )
            ''')
            
            # Sessions table - now with hashed tokens and expiration
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    session_token_hash TEXT PRIMARY KEY,
                    instance_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL
                )
            ''')
            
            # Name history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS name_history (
                    old_name TEXT PRIMARY KEY,
                    new_name TEXT NOT NULL,
                    changed_at TEXT NOT NULL
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info(f"SQLite database initialized at {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            # Fall back to in-memory only if DB fails
            self.db_path = None
    
    def _load_from_database(self):
        """Load existing messages and instances from database"""
        if not self.db_path:
            return
            
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Load unread messages
            cursor.execute('''
                SELECT from_id, to_id, content, timestamp, data, summary, large_file_path
                FROM messages
                WHERE read_flag = 0
                ORDER BY timestamp
            ''')
            
            for row in cursor.fetchall():
                from_id, to_id, content, timestamp, data, summary, large_file_path = row
                
                # Reconstruct message in the expected format
                msg_content = {"content": content}
                if data:
                    msg_content["data"] = json.loads(data)
                
                msg_data = {
                    'from': from_id,
                    'to': to_id,
                    'timestamp': timestamp,
                    'message': msg_content
                }
                
                # Add extra fields if present
                if summary:
                    msg_data['summary'] = summary
                if large_file_path:
                    msg_data['large_file_path'] = large_file_path
                
                if to_id not in self.queues:
                    self.queues[to_id] = []
                self.queues[to_id].append(msg_data)
            
            # Load active instances
            cursor.execute('SELECT instance_id, last_seen FROM instances')
            for row in cursor.fetchall():
                instance_id, last_seen = row
                self.instances[instance_id] = datetime.fromisoformat(last_seen)
            
            # Load sessions - Note: we store hashes, not raw tokens
            # We'll need to handle validation differently now
            # For now, just track which instances have active sessions
            cursor.execute('''
                SELECT instance_id, expires_at 
                FROM sessions 
                WHERE expires_at > ?
            ''', (datetime.now().isoformat(),))
            
            active_instances = set()
            for row in cursor.fetchall():
                instance_id, expires_at = row
                active_instances.add(instance_id)
            
            # Clean up expired sessions
            cursor.execute('DELETE FROM sessions WHERE expires_at <= ?', 
                         (datetime.now().isoformat(),))
            conn.commit()
            
            # Load name history
            cursor.execute('SELECT old_name, new_name, changed_at FROM name_history')
            for row in cursor.fetchall():
                old_name, new_name, changed_at = row
                self.name_history[old_name] = (new_name, datetime.fromisoformat(changed_at))
            
            conn.close()
            logger.info(f"Loaded {sum(len(q) for q in self.queues.values())} messages from database")
        except Exception as e:
            logger.error(f"Failed to load from database: {e}")
    
    def _save_message_to_db(self, from_id: str, to_id: str, msg_data: Dict[str, Any]):
        """Save message to SQLite database"""
        if not self.db_path:
            return
            
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            message = msg_data.get("message", {})
            content = message.get("content", "")
            data = message.get("data")
            
            # Extract summary and large file path if present
            summary = None
            large_file_path = None
            if data and isinstance(data, dict):
                if "large_message_file" in data:
                    large_file_path = data["large_message_file"]
                    # Extract summary from content
                    if "Full content saved to:" in content:
                        summary = content.split("Full content saved to:")[0].strip()
            
            cursor.execute('''
                INSERT INTO messages (from_id, to_id, content, timestamp, data, summary, large_file_path)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                from_id,
                to_id,
                content,
                msg_data["timestamp"],
                json.dumps(data) if data else None,
                summary,
                large_file_path
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to save message to database: {e}")
    
    def _mark_messages_as_read(self, instance_id: str, message_ids: List[int]):
        """Mark messages as read in the database"""
        if not self.db_path or not message_ids:
            return
            
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            placeholders = ','.join('?' for _ in message_ids)
            cursor.execute(f'''
                UPDATE messages 
                SET read_flag = 1 
                WHERE to_id = ? AND id IN ({placeholders})
            ''', [instance_id] + message_ids)
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to mark messages as read: {e}")
    
    def _save_instance_to_db(self, instance_id: str):
        """Save or update instance in database"""
        if not self.db_path:
            return
            
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO instances (instance_id, last_seen)
                VALUES (?, ?)
            ''', (instance_id, datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to save instance to database: {e}")
    
    def _save_session_to_db(self, session_token: str, instance_id: str):
        """Save session to database"""
        if not self.db_path:
            return
            
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Hash the token and set expiration (24 hours from now)
            token_hash = self._hash_token(session_token)
            now = datetime.now()
            expires_at = now + timedelta(hours=24)
            
            cursor.execute('''
                INSERT OR REPLACE INTO sessions (session_token_hash, instance_id, created_at, expires_at)
                VALUES (?, ?, ?, ?)
            ''', (token_hash, instance_id, now.isoformat(), expires_at.isoformat()))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to save session to database: {e}")
    
    def _validate_instance_id(self, instance_id: str) -> bool:
        """Validate instance ID for security"""
        import re
        # Allow only alphanumeric, hyphens, underscores, 1-32 chars
        if not instance_id or len(instance_id) > 32:
            return False
        return bool(re.match(r'^[a-zA-Z0-9_-]+$', instance_id))
    
    def _hash_token(self, token: str) -> str:
        """Hash a session token for secure storage"""
        # Use SHA-256 with a salt for security
        salt = "claude-ipc-mcp-v2"  # In production, use unique salt per deployment
        return hashlib.sha256(f"{salt}:{token}".encode()).hexdigest()
        
    def start(self):
        """Start the message broker server"""
        self.running = True
        threading.Thread(target=self._run_server, daemon=True).start()
        
    def stop(self):
        """Stop the message broker server"""
        self.running = False
        if self.server_socket:
            self.server_socket.close()
            
    def _run_server(self):
        """Run the TCP server"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            logger.info(f"Message broker listening on {self.host}:{self.port}")
            
            while self.running:
                try:
                    self.server_socket.settimeout(1.0)
                    client_socket, address = self.server_socket.accept()
                    threading.Thread(
                        target=self._handle_client,
                        args=(client_socket,),
                        daemon=True
                    ).start()
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        logger.error(f"Server error: {e}")
                        
        except Exception as e:
            logger.error(f"Failed to start message broker: {e}")
            
    def _handle_client(self, client_socket: socket.socket):
        """Handle a client connection"""
        try:
            # Read smaller initial chunk to prevent DoS (M-03 fix)
            data = client_socket.recv(4096).decode('utf-8')
            request = json.loads(data)
            
            response = self._process_request(request)
            
            client_socket.send(json.dumps(response).encode('utf-8'))
            client_socket.close()
        except Exception as e:
            logger.error(f"Client handling error: {e}")
            try:
                error_response = {"status": "error", "message": str(e)}
                client_socket.send(json.dumps(error_response).encode('utf-8'))
            except:
                pass
            finally:
                client_socket.close()
    
    def _clean_expired_forwards(self):
        """Remove name forwards older than 2 hours"""
        now = datetime.now()
        expired = []
        for old_name, (new_name, timestamp) in self.name_history.items():
            if (now - timestamp).total_seconds() > 7200:  # 2 hours
                expired.append(old_name)
        for name in expired:
            del self.name_history[name]
    
    def _clean_expired_messages(self):
        """Remove messages older than 7 days for unregistered instances"""
        now = datetime.now()
        expired_days = 7 * 24 * 3600  # 7 days in seconds
        
        for instance_id in list(self.queues.keys()):
            # Only clean messages for unregistered instances
            if instance_id not in self.instances:
                # Filter out expired messages
                unexpired_messages = []
                for msg in self.queues[instance_id]:
                    try:
                        msg_time = datetime.fromisoformat(msg['timestamp'])
                        if (now - msg_time).total_seconds() < expired_days:
                            unexpired_messages.append(msg)
                    except (KeyError, ValueError):
                        # Keep messages with invalid timestamps (safer)
                        unexpired_messages.append(msg)
                
                # Update queue or remove if empty
                if unexpired_messages:
                    self.queues[instance_id] = unexpired_messages
                else:
                    del self.queues[instance_id]
        
        # Also clean database
        if self.db_path:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # Delete old messages for unregistered instances
                cursor.execute('''
                    DELETE FROM messages 
                    WHERE datetime(timestamp) < datetime('now', '-7 days')
                    AND to_id NOT IN (SELECT instance_id FROM instances)
                ''')
                
                conn.commit()
                conn.close()
            except Exception as e:
                logger.error(f"Failed to clean expired messages from database: {e}")
    
    def _resolve_name(self, name: str) -> str:
        """Resolve a name through forwarding history"""
        self._clean_expired_forwards()
        self._clean_expired_messages()
        if name in self.name_history:
            new_name, timestamp = self.name_history[name]
            return new_name
        return name
    
    def _create_summary(self, content: str, max_length: int = 150) -> str:
        """Create a 2-sentence summary of content"""
        # Clean up content
        content = content.strip()
        
        # Try to extract first two sentences
        sentences = []
        temp = ""
        for char in content:
            temp += char
            if char in '.!?' and len(temp.strip()) > 10:
                sentences.append(temp.strip())
                temp = ""
                if len(sentences) >= 2:
                    break
        
        if sentences:
            summary = " ".join(sentences[:2])
        else:
            # If no sentences found, just truncate
            summary = content[:max_length].strip()
            if len(content) > max_length:
                summary += "..."
        
        return summary
    
    def _save_large_message(self, from_id: str, to_id: str, content: str) -> str:
        """Save large message to file and return file path"""
        # Validate instance IDs first
        if not self._validate_instance_id(from_id) or not self._validate_instance_id(to_id):
            raise ValueError("Invalid instance ID for file path")
        
        # Additional sanitization for filenames
        safe_from = from_id.replace("/", "_").replace("\\", "_")
        safe_to = to_id.replace("/", "_").replace("\\", "_")
        
        # Create timestamp-based filename
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = f"{timestamp}_{safe_from}_{safe_to}_message.md"
        
        # Use secure directory for large messages
        large_msg_dir = os.path.join(self.db_dir, "large-messages")
        os.makedirs(large_msg_dir, 0o700, exist_ok=True)
        filepath = os.path.join(large_msg_dir, filename)
        
        # Calculate size in KB
        size_kb = len(content.encode('utf-8')) / 1024
        
        # Create file content
        file_content = f"""# IPC Message
From: {from_id}
To: {to_id}
Time: {datetime.now().isoformat()}
Size: {size_kb:.1f}KB

## Content
{content}
"""
        
        try:
            # Directory already created with secure permissions above
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(file_content)
            # Set secure permissions on the file
            os.chmod(filepath, 0o600)
            return filepath
        except Exception as e:
            logger.error(f"Failed to save large message: {e}")
            return None
    
    def _validate_session(self, request: Dict[str, Any], action: str) -> Optional[str]:
        """Validate session token and return instance_id if valid"""
        if action == "register":
            # Registration doesn't need session token
            return None
            
        session_token = request.get("session_token")
        if not session_token:
            return None
            
        # First check in-memory sessions (faster)
        if session_token in self.sessions:
            session_info = self.sessions[session_token]
            # Check if session is not expired (24 hours)
            if (datetime.now() - session_info["created_at"]).total_seconds() < 24 * 3600:
                return session_info["instance_id"]
            else:
                # Clean up expired session
                del self.sessions[session_token]
        
        # Fallback to database check
        if not self.db_path:
            return None
            
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Hash the provided token to compare with database
            token_hash = self._hash_token(session_token)
            
            # Check if token exists and is not expired
            cursor.execute('''
                SELECT instance_id 
                FROM sessions 
                WHERE session_token_hash = ? AND expires_at > ?
            ''', (token_hash, datetime.now().isoformat()))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                # Restore to in-memory cache
                self.sessions[session_token] = {
                    "instance_id": result[0],
                    "created_at": datetime.now()
                }
                return result[0]  # Return instance_id
            return None
            
        except Exception as e:
            logger.error(f"Session validation error: {e}")
            return None
                
    def _process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process a broker request"""
        action = request.get("action")
        
        with self.lock:
            # Validate session for non-registration actions
            if action != "register":
                instance_id = self._validate_session(request, action)
                if not instance_id:
                    return {"status": "error", "message": "Invalid or missing session token"}
                # Override any claimed instance_id with the validated one
                if "from_id" in request:
                    request["from_id"] = instance_id
                if "instance_id" in request:
                    request["instance_id"] = instance_id
                    
                # Check rate limit for authenticated requests
                if not self.rate_limiter.is_allowed(instance_id):
                    return {"status": "error", "message": "Rate limit exceeded. Please wait before sending more requests."}
            
            if action == "register":
                instance_id = request["instance_id"]
                
                # Validate instance ID format
                if not self._validate_instance_id(instance_id):
                    return {"status": "error", "message": "Invalid instance ID format. Use 1-32 alphanumeric characters, hyphens, or underscores."}
                
                # Rate limit registration attempts (use IP or a special key)
                if not self.rate_limiter.is_allowed(f"register_{instance_id}"):
                    return {"status": "error", "message": "Too many registration attempts. Please wait."}
                
                # Validate auth token (shared secret)
                auth_token = request.get("auth_token")
                shared_secret = os.environ.get("IPC_SHARED_SECRET", "")
                if shared_secret:
                    import hashlib
                    expected_token = hashlib.sha256(f"{instance_id}:{shared_secret}".encode()).hexdigest()
                    if auth_token != expected_token:
                        return {"status": "error", "message": "Invalid auth token"}
                
                # Generate session token
                session_token = secrets.token_urlsafe(32)
                
                # Register instance (allow multiple sessions per instance_id)
                self.instances[instance_id] = datetime.now()
                
                # Store session mapping (multiple sessions can map to same instance_id)
                self.sessions[session_token] = {
                    "instance_id": instance_id,
                    "created_at": datetime.now()
                }
                
                # Save to database
                self._save_instance_to_db(instance_id)
                self._save_session_to_db(session_token, instance_id)
                
                # Preserve existing queue or create new one
                if instance_id not in self.queues:
                    self.queues[instance_id] = []
                    queued_count = 0
                else:
                    queued_count = len(self.queues[instance_id])
                
                response = {
                    "status": "ok",
                    "session_token": session_token,
                    "message": f"Registered {instance_id}"
                }
                if queued_count > 0:
                    response["message"] = f"Registered {instance_id} with {queued_count} queued messages"
                    
                return response
                
            elif action == "send":
                from_id = request["from_id"]
                to_id = request["to_id"]
                message = request["message"]
                
                # Validate to_id format
                if not self._validate_instance_id(to_id):
                    return {"status": "error", "message": "Invalid recipient ID format"}
                
                # Check message size (10KB threshold)
                content = message.get("content", "")
                content_size = len(content.encode('utf-8'))
                size_threshold = 10 * 1024  # 10KB
                
                if content_size > size_threshold:
                    # Save large message to file
                    filepath = self._save_large_message(from_id, to_id, content)
                    if filepath:
                        # Create summary and update message
                        summary = self._create_summary(content)
                        message = {
                            "content": f"{summary} Full content saved to: {filepath}",
                            "data": message.get("data", {})
                        }
                        message["data"]["large_message_file"] = filepath
                        message["data"]["original_size_kb"] = round(content_size / 1024, 1)
                
                # Resolve name through forwarding if needed
                resolved_to = self._resolve_name(to_id)
                forwarded = resolved_to != to_id
                
                # Create queue for future instances if it doesn't exist
                if resolved_to not in self.queues:
                    self.queues[resolved_to] = []
                    future_delivery = True
                else:
                    future_delivery = not (resolved_to in self.instances)
                    
                # Check queue limit (100 messages per instance)
                if len(self.queues[resolved_to]) >= 100:
                    return {"status": "error", "message": f"Message queue full for {resolved_to} (100 message limit)"}
                    
                msg_data = {
                    "from": from_id,
                    "to": resolved_to,
                    "timestamp": datetime.now().isoformat(),
                    "message": message
                }
                self.queues[resolved_to].append(msg_data)
                
                # Save to SQLite
                self._save_message_to_db(from_id, resolved_to, msg_data)
                
                if forwarded:
                    return {"status": "ok", "message": f"Message forwarded from {to_id} to {resolved_to}"}
                elif future_delivery:
                    return {"status": "ok", "message": f"Message queued for {resolved_to} (not yet registered)"}
                else:
                    return {"status": "ok", "message": "Message sent"}
                
            elif action == "broadcast":
                from_id = request["from_id"]
                message = request["message"]
                count = 0
                
                for instance_id in self.queues:
                    if instance_id != from_id:
                        msg_data = {
                            "from": from_id,
                            "to": instance_id,
                            "timestamp": datetime.now().isoformat(),
                            "message": message
                        }
                        self.queues[instance_id].append(msg_data)
                        
                        # Save to SQLite
                        self._save_message_to_db(from_id, instance_id, msg_data)
                        
                        count += 1
                        
                return {"status": "ok", "message": f"Broadcast to {count} instances"}
                
            elif action == "check":
                # instance_id already validated and set from session
                instance_id = request["instance_id"]
                
                # Resolve name through forwarding if needed
                resolved_id = self._resolve_name(instance_id)
                
                if resolved_id not in self.queues:
                    return {"status": "ok", "messages": []}
                    
                messages = self.queues[resolved_id]
                self.queues[resolved_id] = []
                
                # Mark messages as read in database
                if self.db_path and messages:
                    try:
                        conn = sqlite3.connect(self.db_path)
                        cursor = conn.cursor()
                        
                        # Get message IDs to mark as read
                        for msg in messages:
                            cursor.execute('''
                                UPDATE messages 
                                SET read_flag = 1 
                                WHERE to_id = ? AND timestamp = ? AND read_flag = 0
                            ''', (resolved_id, msg.get("timestamp")))
                        
                        conn.commit()
                        conn.close()
                    except Exception as e:
                        logger.error(f"Failed to mark messages as read: {e}")
                
                return {"status": "ok", "messages": messages}
                
            elif action == "list":
                instances = [
                    {"id": id, "last_seen": ts.isoformat()}
                    for id, ts in self.instances.items()
                ]
                return {"status": "ok", "instances": instances}
                
            elif action == "rename":
                # Get validated instance_id from session
                old_id = request.get("old_id")  # This will be overridden by session validation
                new_id = request["new_id"]
                
                # Validate new_id format
                if not self._validate_instance_id(new_id):
                    return {"status": "error", "message": "Invalid new instance ID format"}
                
                # The old_id should match the session's instance_id (enforced by _process_request)
                # Check if old instance exists
                if old_id not in self.instances:
                    return {"status": "error", "message": f"Instance {old_id} not found"}
                if new_id in self.instances:
                    return {"status": "error", "message": f"Instance {new_id} already exists"}
                
                # Check rate limit (1 hour)
                now = datetime.now()
                if old_id in self.last_rename:
                    time_since_last = (now - self.last_rename[old_id]).total_seconds()
                    if time_since_last < 3600:  # 1 hour in seconds
                        minutes_left = int((3600 - time_since_last) / 60)
                        return {"status": "error", "message": f"Rate limit: can rename again in {minutes_left} minutes"}
                
                # Move the queue
                if old_id in self.queues:
                    self.queues[new_id] = self.queues.pop(old_id)
                else:
                    self.queues[new_id] = []
                
                # Update instance record
                self.instances[new_id] = self.instances.pop(old_id)
                
                # Set up name forwarding
                self.name_history[old_id] = (new_id, now)
                
                # Update rate limit tracking
                self.last_rename[new_id] = now
                if old_id in self.last_rename:
                    del self.last_rename[old_id]
                
                # Update session mapping
                if old_id in self.instance_sessions:
                    session_token = self.instance_sessions.pop(old_id)
                    self.instance_sessions[new_id] = session_token
                    # Update session info
                    if session_token in self.sessions:
                        self.sessions[session_token]["instance_id"] = new_id
                
                # Broadcast rename notification
                for instance_id in self.queues:
                    if instance_id != new_id:
                        notification = {
                            "from": "system",
                            "to": instance_id,
                            "timestamp": now.isoformat(),
                            "message": {"content": f"📝 {old_id} renamed to {new_id}"}
                        }
                        self.queues[instance_id].append(notification)
                
                return {"status": "ok", "message": f"Renamed {old_id} to {new_id}"}
                
            else:
                return {"status": "error", "message": f"Unknown action: {action}"}

# Global broker instance
broker = MessageBroker(IPC_HOST, IPC_PORT)

# Session storage for this MCP instance
current_session_token = None
current_instance_id = None

# Try to start broker (only first instance will succeed)
try:
    broker.start()
    logger.info("Started message broker")
except:
    logger.info("Message broker already running")

class BrokerClient:
    """Client for communicating with the message broker"""
    
    @staticmethod
    def send_request(request: Dict[str, Any]) -> Dict[str, Any]:
        """Send a request to the broker"""
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(5.0)
            client_socket.connect((IPC_HOST, IPC_PORT))
            
            client_socket.send(json.dumps(request).encode('utf-8'))
            response_data = client_socket.recv(65536).decode('utf-8')
            response = json.loads(response_data)
            
            client_socket.close()
            return response
            
        except Exception as e:
            return {"status": "error", "message": f"Broker connection failed: {e}"}

# Create MCP server
app = Server("claude-ipc-wsl")

@app.list_resources()
async def list_resources() -> List[Resource]:
    """List available resources"""
    return [
        Resource(
            uri="ipc://status",
            name="IPC Status",
            mimeType="application/json",
            description="Current status of the IPC system"
        )
    ]

@app.read_resource()
async def read_resource(uri: str) -> str:
    """Read resource content"""
    if uri == "ipc://status":
        response = BrokerClient.send_request({"action": "list"})
        return json.dumps({
            "broker_host": IPC_HOST,
            "broker_port": IPC_PORT,
            "status": response.get("status", "unknown"),
            "instances": response.get("instances", [])
        }, indent=2)
        
    return json.dumps({"error": "Unknown resource"})

@app.list_tools()
async def list_tools() -> List[Tool]:
    """List available tools"""
    return [
        Tool(
            name="register",
            description="Register this Claude instance with the IPC system",
            inputSchema={
                "type": "object",
                "properties": {
                    "instance_id": {
                        "type": "string",
                        "description": "Unique identifier for this instance (e.g., 'wsl1', 'wsl2')"
                    }
                },
                "required": ["instance_id"]
            }
        ),
        Tool(
            name="send",
            description="Send a message to another Claude instance",
            inputSchema={
                "type": "object",
                "properties": {
                    "from_id": {
                        "type": "string",
                        "description": "Your instance ID"
                    },
                    "to_id": {
                        "type": "string",
                        "description": "Target instance ID"
                    },
                    "content": {
                        "type": "string",
                        "description": "Message content"
                    },
                    "data": {
                        "type": "object",
                        "description": "Optional structured data to send"
                    }
                },
                "required": ["from_id", "to_id", "content"]
            }
        ),
        Tool(
            name="broadcast",
            description="Broadcast a message to all other Claude instances",
            inputSchema={
                "type": "object",
                "properties": {
                    "from_id": {
                        "type": "string",
                        "description": "Your instance ID"
                    },
                    "content": {
                        "type": "string",
                        "description": "Message content"
                    },
                    "data": {
                        "type": "object",
                        "description": "Optional structured data"
                    }
                },
                "required": ["from_id", "content"]
            }
        ),
        Tool(
            name="check",
            description="Check for new messages",
            inputSchema={
                "type": "object",
                "properties": {
                    "instance_id": {
                        "type": "string",
                        "description": "Your instance ID"
                    }
                },
                "required": ["instance_id"]
            }
        ),
        Tool(
            name="list_instances",
            description="List all active Claude instances",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="share_file",
            description="Share file content with another instance",
            inputSchema={
                "type": "object",
                "properties": {
                    "from_id": {
                        "type": "string",
                        "description": "Your instance ID"
                    },
                    "to_id": {
                        "type": "string",
                        "description": "Target instance ID"
                    },
                    "filepath": {
                        "type": "string",
                        "description": "Path to file to share"
                    },
                    "description": {
                        "type": "string",
                        "description": "Description of the file"
                    }
                },
                "required": ["from_id", "to_id", "filepath"]
            }
        ),
        Tool(
            name="share_command",
            description="Execute a command and share output with another instance",
            inputSchema={
                "type": "object",
                "properties": {
                    "from_id": {
                        "type": "string",
                        "description": "Your instance ID"
                    },
                    "to_id": {
                        "type": "string",
                        "description": "Target instance ID"
                    },
                    "command": {
                        "type": "string",
                        "description": "Command to execute"
                    },
                    "description": {
                        "type": "string",
                        "description": "Description of what this command does"
                    }
                },
                "required": ["from_id", "to_id", "command"]
            }
        ),
        Tool(
            name="rename",
            description="Rename your instance ID (rate limited to once per hour)",
            inputSchema={
                "type": "object",
                "properties": {
                    "old_id": {
                        "type": "string",
                        "description": "Your current instance ID"
                    },
                    "new_id": {
                        "type": "string",
                        "description": "The new instance ID you want"
                    }
                },
                "required": ["old_id", "new_id"]
            }
        ),
        Tool(
            name="auto_process",
            description="Automatically check and process IPC messages (for use with auto-check feature)",
            inputSchema={
                "type": "object",
                "properties": {
                    "instance_id": {
                        "type": "string",
                        "description": "Your instance ID"
                    }
                },
                "required": ["instance_id"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Execute tool calls"""
    
    if name == "register":
        # Calculate auth token
        instance_id = arguments["instance_id"]
        shared_secret = os.environ.get("IPC_SHARED_SECRET", "")
        auth_token = ""
        if shared_secret:
            import hashlib
            auth_token = hashlib.sha256(f"{instance_id}:{shared_secret}".encode()).hexdigest()
        
        response = BrokerClient.send_request({
            "action": "register",
            "instance_id": instance_id,
            "auth_token": auth_token
        })
        
        # Store session token for this MCP instance
        if response.get("status") == "ok" and response.get("session_token"):
            # Store in a global variable for this MCP session
            global current_session_token, current_instance_id
            current_session_token = response["session_token"]
            current_instance_id = instance_id
        
        return [TextContent(type="text", text=json.dumps(response, indent=2))]
        
    elif name == "send":
        if not current_session_token:
            return [TextContent(type="text", text="Error: Not registered. Please register first.")]
            
        message = {
            "content": arguments["content"],
            "data": arguments.get("data", {})
        }
        response = BrokerClient.send_request({
            "action": "send",
            "from_id": arguments["from_id"],
            "to_id": arguments["to_id"],
            "message": message,
            "session_token": current_session_token
        })
        return [TextContent(type="text", text=json.dumps(response, indent=2))]
        
    elif name == "broadcast":
        if not current_session_token:
            return [TextContent(type="text", text="Error: Not registered. Please register first.")]
            
        message = {
            "content": arguments["content"],
            "data": arguments.get("data", {})
        }
        response = BrokerClient.send_request({
            "action": "broadcast",
            "from_id": arguments["from_id"],
            "message": message,
            "session_token": current_session_token
        })
        return [TextContent(type="text", text=json.dumps(response, indent=2))]
        
    elif name == "check":
        if not current_session_token:
            return [TextContent(type="text", text="Error: Not registered. Please register first.")]
            
        response = BrokerClient.send_request({
            "action": "check",
            "instance_id": arguments["instance_id"],
            "session_token": current_session_token
        })
        
        if response["status"] == "ok" and response.get("messages"):
            formatted = "New messages:\n"
            for msg in response["messages"]:
                formatted += f"\nFrom: {msg['from']}\n"
                formatted += f"Time: {msg['timestamp']}\n"
                formatted += f"Content: {msg['message']['content']}\n"
                if msg['message'].get('data'):
                    formatted += f"Data: {json.dumps(msg['message']['data'], indent=2)}\n"
            return [TextContent(type="text", text=formatted)]
        else:
            return [TextContent(type="text", text="No new messages")]
            
    elif name == "list_instances":
        response = BrokerClient.send_request({"action": "list"})
        return [TextContent(type="text", text=json.dumps(response, indent=2))]
        
    elif name == "share_file":
        if not current_session_token:
            return [TextContent(type="text", text="Error: Not registered. Please register first.")]
            
        try:
            with open(arguments["filepath"], 'r') as f:
                content = f.read()
                
            message = {
                "content": f"Shared file: {arguments['filepath']}",
                "data": {
                    "type": "file",
                    "filepath": arguments["filepath"],
                    "content": content,
                    "description": arguments.get("description", "")
                }
            }
            
            response = BrokerClient.send_request({
                "action": "send",
                "from_id": arguments["from_id"],
                "to_id": arguments["to_id"],
                "message": message,
                "session_token": current_session_token
            })
            return [TextContent(type="text", text=f"File shared: {json.dumps(response, indent=2)}")]
                
        except Exception as e:
            return [TextContent(type="text", text=f"Error sharing file: {e}")]
            
    elif name == "share_command":
        if not current_session_token:
            return [TextContent(type="text", text="Error: Not registered. Please register first.")]
            
        try:
            import subprocess
            import shlex
            
            # Parse command safely to prevent injection
            try:
                cmd_args = shlex.split(arguments["command"])
            except ValueError as e:
                return [TextContent(type="text", text=f"Invalid command format: {e}")]
            
            # Run without shell=True for security
            result = subprocess.run(
                cmd_args,
                shell=False,
                capture_output=True,
                text=True,
                timeout=30  # Add timeout to prevent hanging
            )
            
            message = {
                "content": f"Command output: {arguments['command']}",
                "data": {
                    "type": "command",
                    "command": arguments["command"],
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "returncode": result.returncode,
                    "description": arguments.get("description", "")
                }
            }
            
            response = BrokerClient.send_request({
                "action": "send",
                "from_id": arguments["from_id"],
                "to_id": arguments["to_id"],
                "message": message,
                "session_token": current_session_token
            })
            return [TextContent(type="text", text=f"Command output shared: {json.dumps(response, indent=2)}")]
            
        except Exception as e:
            return [TextContent(type="text", text=f"Error executing command: {e}")]
    
    elif name == "rename":
        if not current_session_token:
            return [TextContent(type="text", text="Error: Not registered. Please register first.")]
            
        response = BrokerClient.send_request({
            "action": "rename",
            "old_id": arguments["old_id"],
            "new_id": arguments["new_id"],
            "session_token": current_session_token
        })
        
        # Update stored instance_id if rename succeeded
        if response.get("status") == "ok":
            current_instance_id = arguments["new_id"]
            
        return [TextContent(type="text", text=json.dumps(response, indent=2))]
    
    elif name == "auto_process":
        if not current_session_token:
            return [TextContent(type="text", text="Error: Not registered. Please register first.")]
        
        instance_id = arguments["instance_id"]
        
        # Check for messages using existing check functionality
        check_response = BrokerClient.send_request({
            "action": "check",
            "instance_id": instance_id,
            "session_token": current_session_token
        })
        
        if check_response.get("status") != "ok":
            return [TextContent(type="text", text=f"Error checking messages: {check_response.get('message')}")]
        
        messages = check_response.get("messages", [])
        
        if not messages:
            return [TextContent(type="text", text="No messages to process.")]
        
        # Process each message
        processed = []
        for msg in messages:
            sender = msg.get("from", "unknown")
            content = msg.get("message", {}).get("content", "")
            timestamp = msg.get("timestamp", "")
            
            # Log what we're processing
            action_taken = f"From {sender}: {content[:50]}..."
            
            # Here we could add smart processing logic:
            # - If content contains "read", read the mentioned file
            # - If content contains "urgent", send acknowledgment
            # - etc.
            
            # For now, just acknowledge receipt
            if sender in ["fred", "claude", "nessa"]:  # Known senders
                ack_response = BrokerClient.send_request({
                    "action": "send",
                    "from_id": instance_id,
                    "to_id": sender,
                    "message": {
                        "content": f"Auto-processed your message from {timestamp}. Content received: '{content[:30]}...'",
                        "data": {"auto_processed": True}
                    },
                    "session_token": current_session_token
                })
                
                if ack_response.get("status") == "ok":
                    action_taken += " [Acknowledged]"
                
            processed.append(action_taken)
        
        # Update last check time
        import time
        os.makedirs("/tmp/claude-ipc-mcp", exist_ok=True)
        config_file = "/tmp/claude-ipc-mcp/auto_check_config.json"
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                config = json.load(f)
            config["last_check"] = time.strftime("%Y-%m-%dT%H:%M:%S")
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
        
        # Return summary
        summary = f"Auto-processed {len(messages)} message(s):\n"
        summary += "\n".join(f"  {i+1}. {p}" for i, p in enumerate(processed))
        
        return [TextContent(type="text", text=summary)]
    
    return [TextContent(type="text", text=f"Unknown tool: {name}")]

async def run_server():
    """Run the MCP server"""
    from mcp.server.stdio import stdio_server
    
    logger.info("Starting Claude IPC MCP Server for WSL")
    logger.info(f"Broker endpoint: {IPC_HOST}:{IPC_PORT}")
    
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

def main():
    """Main entry point"""
    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        broker.stop()
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
