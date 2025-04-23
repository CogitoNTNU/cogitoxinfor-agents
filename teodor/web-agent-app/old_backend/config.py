import os

# Get the app directory path
APP_DIR = os.path.dirname(os.path.abspath(__file__))
# Get the backend directory path
BACKEND_DIR = os.path.dirname(APP_DIR)
# Set history directory in backend folder
HISTORY_DIR = os.path.join(BACKEND_DIR, "history")

# Create history directory if it doesn't exist
os.makedirs(HISTORY_DIR, exist_ok=True)