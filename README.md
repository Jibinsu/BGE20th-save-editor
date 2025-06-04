# BGE 20th Anniversary Save Editor

A comprehensive save file editor for **Beyond Good and Evil 20th Anniversary Edition** with enhanced safety features, search functionality, and automatic backups.

## 🚀 Version 2.0.0 - Major Update!

### ✨ New Features
- **🔒 Automatic Backup System** - Never lose your saves again!
- **🔍 Search Functionality** - Quickly find specific save data
- **✅ Value Validation** - Prevents invalid edits that could corrupt saves
- **📝 Enhanced Logging** - Detailed logs for troubleshooting
- **🎨 Improved UI** - Better themes and user experience

## 📋 Requirements

- Python 3.7+
- PyQt5
- cbor2
- Pillow

Install dependencies:
```bash
pip install -r requirements.txt
```

## 🎮 Usage

### Quick Start
1. **Run the application**:
   ```bash
   python read_bge20th_save.py
   ```

2. **Open your save file** (File → Open)
   - The app automatically creates a backup before opening
   - Navigate to your BGE save file (usually `.sav` extension)

3. **Edit your save data**:
   - Use the search bar to find specific values (e.g., "credits", "pearls")
   - Double-click any value to edit it
   - The app validates your changes to prevent corruption

4. **Save your changes** (File → Save Changes)
   - Only modified values are updated
   - Original file structure is preserved

### 🔍 Search Tips
- Search for "credits" to find currency values
- Search for "pearl" to find collectibles
- Search for "health" to find player stats
- Use partial matches (e.g., "fric" finds "f_sally_fric")

## ✅ Confirmed Working Features

- **💰 Credits Editing** - `f_sally_fric` field (confirmed working)
- **🖼️ Image Viewing** - View embedded screenshots from saves
- **🔍 Data Search** - Find any field quickly
- **💾 Safe Saving** - Automatic backups and validation
- **📊 Data Visualization** - Tree view of all save data

## 🚧 In Development

- **🔮 Pearls Management** - Collectible pearl editing
- **🎒 Inventory Management** - Item and equipment editing  
- **🤝 Companion Features** - Pet and companion data
- **🔄 Undo/Redo** - Reverse changes easily

## 🛡️ Safety Features

### Automatic Backups
- Creates timestamped backups before any edits
- Keeps last 10 backups automatically
- Located in `backups/` folder

### Value Validation
- Prevents invalid values that could corrupt saves
- Game-specific limits (e.g., max credits: 999,999)
- Type checking for all data fields

### Error Handling
- Graceful handling of corrupted save files
- Detailed error messages and logging
- Recovery options for failed operations

## 🏗️ Project Structure

```
BGE20th-save-editor/
├── read_bge20th_save.py    # Main application
├── config.py               # Settings and configuration
├── exceptions.py           # Custom error handling
├── backup_manager.py       # Backup functionality
├── validators.py           # Value validation
├── requirements.txt        # Dependencies
├── backups/               # Auto-created backup folder
└── bge_save_editor.log    # Application logs
```

## 🤝 Contributing

This project is **fully open source** for the community! 

### How to Contribute
1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes** and test thoroughly
4. **Submit a pull request** with detailed description

### Areas Needing Help
- 🔮 Pearl collection data structures
- 🎒 Inventory and item management
- 🤝 Companion/pet data analysis
- 🧪 Testing with different save files
- 📚 Documentation improvements

## 🐛 Troubleshooting

### Common Issues

**"Failed to parse CBOR data"**
- Your save file may be corrupted
- Try with a different save file
- Check the logs in `bge_save_editor.log`

**"Backup creation failed"**
- Check folder permissions
- Ensure enough disk space
- Manually create `backups/` folder

**"Validation failed"**
- Value is outside acceptable range
- Check the error message for specific limits
- Try a different value within the suggested range

### Getting Help
- Check the log file: `bge_save_editor.log`
- Open an issue on GitHub with:
  - Error message
  - Steps to reproduce
  - Log file contents (remove personal info)

## 📜 Credits

- **Original Creator**: Jibinsu
- **Special Thanks**: Zeli for troubleshooting assistance
- **Community Contributors**: Everyone who helps improve this tool!

## 📄 License

Open source - feel free to modify, distribute, and improve!

---

**⚠️ Important**: Always backup your save files before editing! While this tool includes automatic backups, it's always good to have your own copies. 
