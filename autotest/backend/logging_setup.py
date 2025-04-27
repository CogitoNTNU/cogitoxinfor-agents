import os
import base64
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from queue import Queue
from threading import Lock
from datetime import datetime
import threading

# Create global queues for real-time messages
log_queue = Queue()
log_lock = Lock()
screenshot_queue = Queue()
screenshot_lock = Lock()

# Define common directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGS_DIR = os.path.join(BASE_DIR, 'logs')
DATA_DIR = os.path.join(BASE_DIR, 'data')
STATIC_DIR = os.path.join(BASE_DIR, 'static')
PROFILES_DIR = os.path.join(BASE_DIR, 'profiles')

# Create necessary directories
for directory in [LOGS_DIR, DATA_DIR, STATIC_DIR, PROFILES_DIR]:
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
        
        # Ensure data directory exists
        self.data_dir = Path(DATA_DIR)
        
    def emit(self, record):
        # Format the log entry
        log_entry = self.format(record)
        
        # Put in queue for streaming (existing functionality)
        with log_lock:
            log_queue.put(log_entry)
        
        # Save to file
        try:
            # Determine agent ID (check multiple sources in priority order)
            agent_id = None
            
            # 1. Check if record has agent_id attribute (added by filter)
            if hasattr(record, 'agent_id'):
                agent_id = record.agent_id
                print(f"Agent ID from record: {agent_id}")
            # 2. Use handler's agent_id if set
            if not agent_id and self.agent_id:
                agent_id = self.agent_id
                print(f"Agent ID from handler: {agent_id}")
            # 3. Check thread-local storage
            if not agent_id:
                agent_id = get_current_agent_id()
                print(f"Agent ID from thread-local storage: {agent_id}")
            # 4. Try to extract from message as last resort
            if not agent_id and hasattr(record, 'msg'):
                msg = str(record.msg)
                if "Agent " in msg and ":" in msg:
                    agent_id = msg.split("Agent ")[1].split(":")[0].strip()
                    print(f"Extracted Agent ID from message: {agent_id}")
            # Fall back to general if all else fails
            agent_id = agent_id or "general"
            
            # Create directory structure
            agent_dir = self.data_dir / agent_id
            agent_dir.mkdir(exist_ok=True)
            
            logs_dir = agent_dir / "logs"
            logs_dir.mkdir(exist_ok=True)
            
            # Get current date for log file naming
            current_date = datetime.now().strftime("%Y-%m-%d")
            log_file = logs_dir / f"{current_date}.log"
            
            # Append log entry to file
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"{log_entry}\n")
                
        except Exception as e:
            # Don't let log saving errors propagate
            print(f"Error saving log to file: {e}")

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

def setup_agent_logger(agent_id):
    """Create and configure a logger for a specific agent"""
    # Create a logger with the agent's ID as the name
    set_current_agent_id(agent_id)
    agent_logger = logging.getLogger('browser_use')
    agent_logger.setLevel(logging.INFO)
    
    # Create a log handler for this specific agent
    agent_log_handler = LogHandler()
    agent_log_handler.setFormatter(logging.Formatter('%(asctime)s - [%(name)s] - %(levelname)s - %(message)s'))
    agent_logger.addHandler(agent_log_handler)
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