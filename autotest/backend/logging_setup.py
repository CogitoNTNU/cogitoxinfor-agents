import os
import base64
import logging
from logging.handlers import RotatingFileHandler
from queue import Queue
from threading import Lock
from datetime import datetime
import threading
import requests
from pathlib import Path

# Create global queues for real-time messages
log_queue = Queue()
log_lock = Lock()
screenshot_queue = Queue()
screenshot_lock = Lock()

# Dictionary to track which logs have been sent to which agents
# Format: {log_hash: set(agent_ids)}
sent_logs = {}
sent_logs_lock = Lock()

# Define common directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGS_DIR = os.path.join(BASE_DIR, 'logs')
DATA_DIR = os.path.join(BASE_DIR, 'data')
STATIC_DIR = os.path.join(BASE_DIR, 'static')
PROFILES_DIR = os.path.join(BASE_DIR, 'profiles')
SCREENSHOTS_DIR = os.path.join(BASE_DIR, 'screenshots')

# Create necessary directories
for directory in [LOGS_DIR, DATA_DIR, STATIC_DIR, PROFILES_DIR, SCREENSHOTS_DIR]:
    os.makedirs(directory, exist_ok=True)

# Thread-local storage for agent context (move from agent_context.py if it exists there)
_agent_context = threading.local()

def get_current_agent_id():
    """Get the agent ID from thread-local storage"""
    return getattr(_agent_context, "agent_id", None)

def set_current_agent_id(agent_id):
    """Set the agent ID in thread-local storage"""
    _agent_context.agent_id = agent_id

class AgentIdFilter(logging.Filter):
    """Filter that adds agent_id to log records"""
    def filter(self, record):
        record.agent_id = get_current_agent_id()
        return True

class LogHandler(logging.Handler):
    """Handler for agent-specific log files"""
    def __init__(self, agent_id=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.agent_id = agent_id
        
    def emit(self, record):
        # Format the log entry
        log_entry = self.format(record)
        
        # Determine agent ID (check multiple sources in priority order)
        agent_id = None
        
        # 1. Check if record has agent_id attribute (added by filter)
        if hasattr(record, 'agent_id'):
            agent_id = record.agent_id
        
        # 2. Use handler's agent_id if set
        if not agent_id and self.agent_id:
            agent_id = self.agent_id
        
        # 3. Check thread-local storage
        if not agent_id:
            agent_id = get_current_agent_id()
        
        # 4. Try to extract from message as last resort
        if not agent_id and hasattr(record, 'msg'):
            msg = str(record.msg)
            if "Agent " in msg and ":" in msg:
                agent_id = msg.split("Agent ")[1].split(":")[0].strip()

        # Fall back to general if all else fails
        agent_id = agent_id or "general"
        
        # Create a unique hash for this log entry to prevent duplicates
        import hashlib
        log_hash = hashlib.md5(f"{log_entry}:{datetime.now().timestamp()}".encode()).hexdigest()
        
        # Create a structured log entry with agent_id
        try:
            # Try to parse the log entry as JSON
            import json
            structured_entry = json.loads(log_entry)
            # Add agent_id and log_hash if not already present
            if 'agent_id' not in structured_entry:
                structured_entry['agent_id'] = agent_id
            structured_entry['log_hash'] = log_hash
            # Convert back to string
            structured_log = json.dumps(structured_entry)
        except:
            # If not JSON, create a simple structured format
            structured_log = json.dumps({
                'message': log_entry,
                'agent_id': agent_id,
                'log_hash': log_hash,
                'timestamp': datetime.now().isoformat()
            })
        
        # Put in queue for streaming with agent_id, but only once per agent
        with sent_logs_lock:
            # Check if this log has been sent to this agent before
            if log_hash not in sent_logs:
                sent_logs[log_hash] = set()
            
            # Only add to queue if this agent hasn't seen this log yet
            if agent_id not in sent_logs[log_hash]:
                sent_logs[log_hash].add(agent_id)
                with log_lock:
                    log_queue.put(structured_log)
        
        try:
            # Send the log to the API
            response = requests.post(
                "http://127.0.0.1:9000/save_log",
                json={"agent_id": agent_id, "log_entry": log_entry}
            )
            
            if response.status_code != 200:
                print(f"Error sending log to API: {response.text}")
                
        except Exception as e:
            # Don't let log saving errors propagate
            print(f"Error saving log to API: {e}")

def setup_logging():
    """Configure the root logger with console and file handlers"""
    # Configure root logger
    logging.basicConfig(level=logging.INFO)
    root_logger = logging.getLogger()
    
    # Create a rotating file handler (10MB per file, keep 5 backup files)
    file_handler = RotatingFileHandler(
        os.path.join(LOGS_DIR, 'application.log'),
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8',
    )
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    root_logger.addHandler(file_handler)
    
    return root_logger

def get_logger(name):
    """Get a logger with the specified name"""
    logger = logging.getLogger(name)
    return logger

# Dictionary to track agent loggers and handlers
agent_loggers = {}
agent_loggers_lock = Lock()

def setup_agent_logger(agent_id):
    """Create and configure a logger for a specific agent"""
    # Set the agent ID in thread-local storage
    set_current_agent_id(agent_id)
    
    # Use a lock to prevent race conditions when creating loggers
    with agent_loggers_lock:
        # Check if a logger already exists for this agent
        if agent_id in agent_loggers:
            return agent_loggers[agent_id]
        
        # Create a new logger for this agent
        agent_logger = logging.getLogger('browser_use')
        agent_logger.setLevel(logging.INFO)
        
        # Remove any existing handlers to prevent duplicates
        for handler in list(agent_logger.handlers):
            agent_logger.removeHandler(handler)
        
        # Create a log handler for this specific agent
        agent_log_handler = LogHandler(agent_id=agent_id)
        agent_log_handler.setFormatter(logging.Formatter('%(asctime)s - [%(name)s] - %(levelname)s - %(message)s'))
        agent_logger.addHandler(agent_log_handler)
        
        # Store the logger for future use
        agent_loggers[agent_id] = agent_logger
        
        return agent_logger

def b64_to_png(base64_str: str, output_path: Path) -> bool:
    """Convert base64 string to PNG file"""
    logger = get_logger("utils")
    try:
        img_data = base64.b64decode(base64_str)
        with open(output_path, 'wb') as f:
            f.write(img_data)
        logger.info(f"Saved screenshot to {output_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to save screenshot: {str(e)}")
        return False

def get_agent_screenshot_path(agent_id: str, step_number: int = None) -> tuple:
    """Get the path for an agent's screenshot"""
    # Create agent-specific directory
    agent_dir = Path(SCREENSHOTS_DIR) / agent_id
    agent_dir.mkdir(exist_ok=True)
    
    # Generate filename based on timestamp and step number
    import time
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    step_info = f"_step{step_number}" if step_number is not None else ""
    filename = f"{timestamp}{step_info}.png"
    
    return agent_dir / filename, f"/screenshots/{agent_id}/{filename}"

# Initialize logging
setup_logging()
