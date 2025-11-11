"""Storage service for managing sessions and files"""
import json
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional
from uuid import uuid4

from loguru import logger


class StorageService:
    """Service for managing file storage and sessions"""
    
    def __init__(self, base_path: str = "temp"):
        self.base_path = Path(base_path)
        self.sessions_path = self.base_path / "sessions"
        self.uploads_path = self.base_path / "uploads"
    
    def initialize(self):
        """Initialize storage directories"""
        self.base_path.mkdir(exist_ok=True)
        self.sessions_path.mkdir(exist_ok=True)
        self.uploads_path.mkdir(exist_ok=True)
        logger.info(f"Storage initialized at: {self.base_path}")
    
    def create_session(self, session_type: str, metadata: Optional[Dict] = None) -> str:
        """Create a new session"""
        session_id = str(uuid4())
        session_dir = self.sessions_path / session_id
        session_dir.mkdir(exist_ok=True)
        
        (session_dir / "audio").mkdir(exist_ok=True)
        (session_dir / "video").mkdir(exist_ok=True)
        
        session_data = {
            "id": session_id,
            "type": session_type,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "status": "active",
            "metadata": metadata or {}
        }
        
        self._save_metadata(session_id, session_data)
        logger.info(f"Created session: {session_id}")
        return session_id
    
    def get_session_path(self, session_id: str) -> Path:
        """Get session directory path"""
        return self.sessions_path / session_id
    
    def save_file(self, session_id: str, file_data: bytes, filename: str, subdir: str = "") -> str:
        """Save file to session directory"""
        session_dir = self.get_session_path(session_id)
        
        if subdir:
            save_dir = session_dir / subdir
            save_dir.mkdir(exist_ok=True)
        else:
            save_dir = session_dir
        
        file_path = save_dir / filename
        with open(file_path, "wb") as f:
            f.write(file_data)
        
        logger.info(f"Saved file: {file_path}")
        return str(file_path)
    
    def _save_metadata(self, session_id: str, data: Dict):
        """Save session metadata"""
        metadata_path = self.get_session_path(session_id) / "metadata.json"
        with open(metadata_path, "w") as f:
            json.dump(data, f, indent=2)
    
    def get_metadata(self, session_id: str) -> Optional[Dict]:
        """Get session metadata"""
        metadata_path = self.get_session_path(session_id) / "metadata.json"
        if metadata_path.exists():
            with open(metadata_path, "r") as f:
                return json.load(f)
        return None
    
    def update_metadata(self, session_id: str, updates: Dict):
        """Update session metadata"""
        metadata = self.get_metadata(session_id) or {}
        metadata.update(updates)
        metadata["updated_at"] = datetime.now().isoformat()
        self._save_metadata(session_id, metadata)
    
    def save_results(self, session_id: str, results: Dict):
        """Save evaluation results"""
        results_path = self.get_session_path(session_id) / "results.json"
        with open(results_path, "w") as f:
            json.dump(results, f, indent=2)
        logger.info(f"Saved results for session: {session_id}")
    
    def get_results(self, session_id: str) -> Optional[Dict]:
        """Get evaluation results"""
        results_path = self.get_session_path(session_id) / "results.json"
        if results_path.exists():
            with open(results_path, "r") as f:
                return json.load(f)
        return None
    
    def delete_session(self, session_id: str):
        """Delete session and all its files"""
        session_dir = self.get_session_path(session_id)
        if session_dir.exists():
            shutil.rmtree(session_dir)
            logger.info(f"Deleted session: {session_id}")
    
    def cleanup_old_sessions(self, max_age_hours: int = 24):
        """Delete sessions older than specified hours"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        deleted_count = 0
        
        for session_dir in self.sessions_path.iterdir():
            if session_dir.is_dir():
                metadata = self.get_metadata(session_dir.name)
                if metadata:
                    created_at = datetime.fromisoformat(metadata["created_at"])
                    if created_at < cutoff_time:
                        self.delete_session(session_dir.name)
                        deleted_count += 1
        
        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} old sessions")
    
    def list_sessions(self) -> list:
        """List all sessions"""
        sessions = []
        for session_dir in self.sessions_path.iterdir():
            if session_dir.is_dir():
                metadata = self.get_metadata(session_dir.name)
                if metadata:
                    sessions.append(metadata)
        return sessions
    
    def get_temp_path(self, filename: str) -> Path:
        """Get path in temp directory for a file"""
        return self.base_path / filename
    
    def save_temp_file(self, source_path: str, filename: str) -> str:
        """Copy file to temp directory and return path"""
        dest_path = self.get_temp_path(filename)
        shutil.copy(source_path, dest_path)
        logger.info(f"Saved temp file: {dest_path}")
        return str(dest_path)
