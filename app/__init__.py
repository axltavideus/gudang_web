import logging
from flask import Flask
import os

app = Flask(__name__)

# Base directory of the app folder
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Configuration
UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", os.path.join(BASE_DIR, "uploads"))
PROCESSED_FOLDER = os.getenv("PROCESSED_FOLDER", os.path.join(BASE_DIR, "processed"))

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from app import routes  # Import routes to register with app
