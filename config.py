"""
Configuration settings for BGE 20th Anniversary Save Editor
"""
import os
from pathlib import Path

class Config:
    # Application settings
    APP_NAME = "BGE 20th Anniversary Save Editor"
    VERSION = "3.0.0"
    
    # Paths
    BASE_DIR = Path(__file__).parent
    ASSETS_DIR = BASE_DIR / "assets"
    BACKUP_DIR = BASE_DIR / "backups"
    
    # Icon path (fallback if not found)
    ICON_PATH = ASSETS_DIR / "icon.ico"
    
    # UI Settings
    WINDOW_WIDTH = 1000
    WINDOW_HEIGHT = 700
    MAX_RECENT_FILES = 10
    
    # Theme colors
    THEME_COLORS = {
        'primary': '#00cc66',
        'background_main': '#2e2e2e',
        'background_secondary': '#1e1e1e',
        'background_widget': '#3a3a3a',
        'background_selected': '#00cc66',
        'text_primary': '#e0e0e0',
        'text_selected': '#000000',
        'border': '#00cc66'
    }
    
    # File settings
    SUPPORTED_EXTENSIONS = ['.sav']
    BACKUP_TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"
    
    # Validation limits
    VALIDATION_LIMITS = {
        'credits': {'min': 0, 'max': 999999},
        'pearls': {'min': 0, 'max': 88},
        'health': {'min': 0.0, 'max': 100.0}
    }
    
    @classmethod
    def ensure_directories(cls):
        """Create necessary directories if they don't exist"""
        cls.ASSETS_DIR.mkdir(exist_ok=True)
        cls.BACKUP_DIR.mkdir(exist_ok=True)