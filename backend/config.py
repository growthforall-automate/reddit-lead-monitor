import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "mintos.db")
BRAIN_DIR = os.path.join(BASE_DIR, "backend", "brain")
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
