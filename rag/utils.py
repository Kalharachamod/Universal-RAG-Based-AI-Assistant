import os
from pathlib import Path
import uuid
from werkzeug.utils import secure_filename

UPLOAD_DIR = "storage/uploads"
CHROMA_DIR = "storage/chroma"


def ensure_dirs():
    Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    Path(CHROMA_DIR).mkdir(parents=True, exist_ok=True)
    Path("data").mkdir(parents=True, exist_ok=True)


def save_uploaded_file(uploaded_file, session_id):
    """
    Save uploaded file to the appropriate directory for the session
    """
    # Get original filename
    filename = getattr(uploaded_file, 'name', f"temp_file_{uuid.uuid4()}.bin")
    
    # Sanitize filename to prevent path traversal attacks
    filename = secure_filename(filename)
    
    # Create session directory
    session_dir = Path(UPLOAD_DIR) / session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    
    # Create full file path
    file_path = session_dir / filename
    
    # Save file
    with open(file_path, 'wb') as f:
        # Handle both file objects and raw content
        if hasattr(uploaded_file, 'seek'):
            uploaded_file.seek(0)  # Reset file pointer to beginning
            f.write(uploaded_file.read())
        else:
            f.write(uploaded_file)
    
    return str(file_path)


def clear_session_storage(session_id: str):
    # Optional: you can add deletion logic for session dirs if needed
    pass
