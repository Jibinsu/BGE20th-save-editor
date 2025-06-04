# Changelog

## Version 2.0.0 - Major Improvements

### 🚀 New Features
- **Automatic Backup System**: Creates timestamped backups before editing save files
- **Search Functionality**: Search through save data with real-time filtering
- **Value Validation**: Validates edits with game-specific constraints
- **Enhanced Error Handling**: Better error messages and logging
- **Configuration Management**: Centralized settings and theme configuration

### 🔧 Technical Improvements
- **Modular Architecture**: Split code into logical modules (config, exceptions, validators, backup manager)
- **Logging System**: Comprehensive logging to file and console
- **Type Safety**: Better type hints and validation
- **Requirements Management**: Added requirements.txt for easy dependency installation

### 🎨 UI/UX Improvements
- **Search Bar**: Added search functionality to quickly find specific save data
- **Better Themes**: Configurable color scheme using centralized theme settings
- **Enhanced Dialogs**: More informative edit dialogs with field context
- **Status Updates**: Better status bar messages and user feedback

### 🛡️ Safety & Reliability
- **Automatic Backups**: Never lose your save files again
- **Input Validation**: Prevents invalid values that could corrupt saves
- **Error Recovery**: Graceful handling of file parsing errors
- **Backup Management**: Automatic cleanup of old backup files

### 📁 File Structure
```
BGE20th-save-editor/
├── read_bge20th_save.py    # Main application (updated)
├── config.py               # Configuration settings
├── exceptions.py           # Custom exception classes
├── backup_manager.py       # Backup functionality
├── validators.py           # Value validation
├── requirements.txt        # Python dependencies
├── README.md              # Updated documentation
└── CHANGELOG.md           # This file
```

### 🔄 Migration from v1.x
- No breaking changes to save file format
- All existing functionality preserved
- New features are additive and optional
- Automatic backup creation provides safety net

### 🐛 Bug Fixes
- Removed hardcoded file paths for better portability
- Improved memory management for large save files
- Better handling of malformed CBOR data
- Fixed potential crashes during file operations

### 📋 Known Limitations
- Pearls, inventory management, and companion features still in development
- Some advanced save file structures may not be fully supported
- Large save files may take longer to load due to enhanced processing

### 🔮 Future Plans
- Plugin system for game-specific modifications
- Undo/Redo functionality
- Batch editing capabilities
- Export/Import save modifications
- Advanced hex editor view