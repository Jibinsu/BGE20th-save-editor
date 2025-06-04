"""
Backup management for save files
"""
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional
import logging

from config import Config
from exceptions import BackupError

logger = logging.getLogger(__name__)

class BackupManager:
    """Manages automatic backups of save files"""
    
    def __init__(self):
        Config.ensure_directories()
        self.backup_dir = Config.BACKUP_DIR
    
    def create_backup(self, file_path: str) -> Path:
        """
        Create a timestamped backup of the save file
        
        Args:
            file_path: Path to the original save file
            
        Returns:
            Path to the created backup file
            
        Raises:
            BackupError: If backup creation fails
        """
        try:
            source_path = Path(file_path)
            if not source_path.exists():
                raise BackupError(f"Source file does not exist: {file_path}")
            
            timestamp = datetime.now().strftime(Config.BACKUP_TIMESTAMP_FORMAT)
            backup_filename = f"{source_path.stem}_{timestamp}{source_path.suffix}"
            backup_path = self.backup_dir / backup_filename
            
            shutil.copy2(source_path, backup_path)
            logger.info(f"Backup created: {backup_path}")
            
            # Clean old backups (keep last 10)
            self._cleanup_old_backups(source_path.stem)
            
            return backup_path
            
        except Exception as e:
            raise BackupError(f"Failed to create backup: {e}")
    
    def _cleanup_old_backups(self, base_name: str, keep_count: int = 10):
        """Remove old backup files, keeping only the most recent ones"""
        try:
            pattern = f"{base_name}_*.sav"
            backup_files = list(self.backup_dir.glob(pattern))
            
            if len(backup_files) > keep_count:
                # Sort by modification time, newest first
                backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                
                # Remove oldest files
                for old_backup in backup_files[keep_count:]:
                    old_backup.unlink()
                    logger.info(f"Removed old backup: {old_backup}")
                    
        except Exception as e:
            logger.warning(f"Failed to cleanup old backups: {e}")
    
    def list_backups(self, base_name: Optional[str] = None) -> list[Path]:
        """List all backup files, optionally filtered by base name"""
        if base_name:
            pattern = f"{base_name}_*.sav"
        else:
            pattern = "*.sav"
            
        backup_files = list(self.backup_dir.glob(pattern))
        backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        return backup_files
    
    def restore_backup(self, backup_path: Path, target_path: str) -> bool:
        """
        Restore a backup file to the target location
        
        Args:
            backup_path: Path to the backup file
            target_path: Where to restore the backup
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not backup_path.exists():
                raise BackupError(f"Backup file does not exist: {backup_path}")
            
            shutil.copy2(backup_path, target_path)
            logger.info(f"Backup restored from {backup_path} to {target_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to restore backup: {e}")
            return False