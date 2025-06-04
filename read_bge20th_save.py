import sys
import binascii
import cbor2
import io
import logging
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QTreeWidget, QTreeWidgetItem,
    QLabel, QVBoxLayout, QWidget, QScrollArea, QMessageBox, QInputDialog,
    QSplitter, QStatusBar, QTabWidget, QAction, QTextEdit, QLineEdit, QHBoxLayout
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage, QFont, QIcon
from PIL import Image

from config import Config
from exceptions import SaveFileError, CBORParsingError, ValueValidationError
from backup_manager import BackupManager
from validators import ValueValidator
from translations import translator
from ui_components import (
    TranslatedTreeWidget, SmartSearchWidget, ValueEditorDialog,
    StatsWidget, EnhancedDetailView
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bge_save_editor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CBORViewerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{Config.APP_NAME} v{Config.VERSION}")
        self.setGeometry(100, 100, Config.WINDOW_WIDTH, Config.WINDOW_HEIGHT)
        
        # Set icon if it exists
        if Config.ICON_PATH.exists():
            self.setWindowIcon(QIcon(str(Config.ICON_PATH)))
        
        # Initialize managers
        self.backup_manager = BackupManager()
        self.validator = ValueValidator()

        self.original_data = None
        self.cbor_data = None
        self.human_readable_data = None
        self.changes = {}  # Track all changes here
        self.current_file_path = None

        self.init_ui()
        self.apply_theme()
        
        logger.info(f"Application started: {Config.APP_NAME} v{Config.VERSION}")

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Enhanced search widget
        self.search_widget = SmartSearchWidget()
        self.search_widget.searchChanged.connect(self.filter_tree_advanced)
        layout.addWidget(self.search_widget)

        # Main splitter
        main_splitter = QSplitter(Qt.Horizontal)
        
        # Left side: Tree and stats
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # Tree widget with translation support
        self.tree = TranslatedTreeWidget()
        self.tree.itemClicked.connect(self.on_item_clicked)
        self.tree.itemDoubleClicked.connect(self.on_item_double_click)
        left_layout.addWidget(self.tree)
        
        # Stats widget
        self.stats_widget = StatsWidget()
        left_layout.addWidget(self.stats_widget)
        
        main_splitter.addWidget(left_widget)
        main_splitter.setSizes([600, 400])  # Give more space to tree

        # Right side: Tabs for details and image viewer
        tabs = QTabWidget()

        # Enhanced detail view
        self.detail_view = EnhancedDetailView()
        tabs.addTab(self.detail_view, "Details")

        # Image viewer
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.scroll_area.setWidget(self.image_label)
        tabs.addTab(self.scroll_area, "Image Viewer")

        main_splitter.addWidget(tabs)
        layout.addWidget(main_splitter)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("File")

        open_action = QAction("Open", self)
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)

        save_action = QAction("Save Changes", self)
        save_action.triggered.connect(self.save_changes)
        file_menu.addAction(save_action)

    def apply_theme(self):
        """Apply Beyond Good and Evil inspired theme with gradients and custom panel colors."""
        colors = Config.THEME_COLORS
        self.setStyleSheet(f"""
            QMainWindow {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                            stop:0 {colors['background_main']}, stop:1 {colors['background_secondary']});
            }}
            QTreeWidget {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                            stop:0 {colors['background_widget']}, stop:1 #2b2b2b);
                color: {colors['text_primary']};
                border: 1px solid {colors['border']};
                font-family: 'Verdana';
                font-size: 12pt;
            }}
            QTreeWidget::item {{
                color: {colors['text_primary']};
            }}
            QTreeWidget::item:selected {{
                background-color: {colors['background_selected']};
                color: {colors['text_selected']};
            }}
            QTabWidget::pane {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                            stop:0 #444444, stop:1 #333333);
                border: 1px solid {colors['border']};
            }}
            QScrollArea {{
                background-color: {colors['background_widget']};
                border: 1px solid {colors['border']};
            }}
            QTextEdit {{
                background-color: {colors['background_widget']};
                color: {colors['text_primary']};
                border: 1px solid {colors['border']};
            }}
            QLineEdit {{
                background-color: {colors['background_widget']};
                color: {colors['text_primary']};
                border: 1px solid {colors['border']};
                padding: 5px;
            }}
            QLabel {{
                color: {colors['text_primary']};
            }}
            QMenuBar {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                            stop:0 {colors['background_main']}, stop:1 {colors['background_secondary']});
                color: {colors['primary']};
            }}
            QMenuBar::item {{
                background: transparent;
                color: {colors['primary']};
            }}
            QMenuBar::item:selected {{
                background-color: {colors['primary']};
                color: {colors['text_selected']};
            }}
            QStatusBar {{
                background-color: {colors['background_main']};
                color: {colors['primary']};
            }}
            QMessageBox {{
                background-color: {colors['background_widget']};
                color: {colors['text_primary']};
            }}
        """)

        # Set the font for the whole application
        font = QFont('Verdana', 10)
        QApplication.setFont(font)

    def open_file(self):
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Select a .sav file", "", "SAV files (*.sav)"
            )
            if not file_path:
                return

            # Create backup before opening
            try:
                backup_path = self.backup_manager.create_backup(file_path)
                logger.info(f"Backup created: {backup_path}")
                self.status_bar.showMessage(f"Backup created: {backup_path.name}", 3000)
            except Exception as e:
                logger.warning(f"Failed to create backup: {e}")
                reply = QMessageBox.question(
                    self, "Backup Failed", 
                    f"Failed to create backup: {e}\n\nContinue without backup?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.No:
                    return

            self.current_file_path = file_path

            with open(file_path, 'rb') as f:
                self.original_data = f.read()

            _, _, self.split_data, self.dump_data = read_and_split_sav_file(file_path)
            self.cbor_data = parse_cbor_dump(self.dump_data)

            if not self.cbor_data:
                raise CBORParsingError("Failed to parse CBOR data from save file")

            self.human_readable_data = make_human_readable(self.cbor_data)
            self.populate_tree(self.human_readable_data)
            self.status_bar.showMessage("File loaded successfully.", 5000)
            logger.info(f"Successfully loaded save file: {file_path}")
            
        except SaveFileError as e:
            QMessageBox.critical(self, "Save File Error", str(e))
            self.status_bar.showMessage("Failed to load file.", 5000)
            logger.error(f"Save file error: {e}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open file: {e}")
            self.status_bar.showMessage("Failed to load file.", 5000)
            logger.error(f"Unexpected error opening file: {e}")

    def populate_tree(self, data, parent=None):
        if parent is None:
            self.tree.clear()
            parent = self.tree.invisibleRootItem()
            # Update stats when populating root
            if hasattr(self, 'stats_widget'):
                self.stats_widget.update_stats(data)

        if isinstance(data, dict):
            for key, value in data.items():
                # Translate the key
                translated_key = translator.translate_key(key)
                display_key = translated_key if translated_key != key else key
                
                # Create item with translated key, value, and original key
                item = QTreeWidgetItem([display_key, "", key])
                parent.addChild(item)
                
                # Add tooltip with translation info
                if translated_key != key:
                    description = translator.get_description(key)
                    tooltip = f"Original: {key}"
                    if description:
                        tooltip += f"\nDescription: {description}"
                    item.setToolTip(0, tooltip)
                
                self.populate_tree(value, item)
        elif isinstance(data, list):
            for index, value in enumerate(data):
                item = QTreeWidgetItem([f"[{index}]", "", f"[{index}]"])
                parent.addChild(item)
                self.populate_tree(value, item)
        else:
            if isinstance(data, QPixmap):
                item = QTreeWidgetItem([f"Image {parent.childCount()}", "Double-click to view", "image_data"])
                item.setData(0, Qt.UserRole, data)
                parent.addChild(item)
            else:
                # Set the value in the second column
                value_str = str(data)
                if len(value_str) > 100:
                    value_str = value_str[:100] + "..."
                parent.setText(1, value_str)

    def on_item_clicked(self, item, column):
        """Show details when an item is clicked."""
        if item:  # Ensure the item is valid
            if not isinstance(item.data(0, Qt.UserRole), QPixmap):
                # Get the original key (from third column) or displayed key
                original_key = item.text(2) if item.text(2) else item.text(0)
                keys = self.get_item_path(item)
                value = self.get_value(self.cbor_data, keys)
                
                # Use enhanced detail view
                self.detail_view.display_item_details(original_key, value, keys)

    def get_detailed_information(self, item):
        """Retrieve detailed information for the selected item."""
        keys = []
        while item is not None:
            keys.append(item.text(0))
            item = item.parent()
        keys = list(reversed(keys))

        value = self.get_value(self.cbor_data, keys)
        value_type = type(value).__name__
        details = f"Key Path: {' > '.join(keys)}\nValue: {value}\nType: {value_type}"

        if isinstance(value, (dict, list)):
            details += f"\n\nExpanded View:\n{value}"

        return details

    def on_item_double_click(self, item, column):
        """Handle double-clicks to edit or view items."""
        if item:  # Ensure the item is valid
            if isinstance(item.data(0, Qt.UserRole), QPixmap):
                pixmap = item.data(0, Qt.UserRole)
                self.image_label.setPixmap(pixmap)
                self.status_bar.showMessage("Image displayed.", 5000)
            else:
                current_value = item.text(1)
                keys = self.get_item_path(item)
                original_key = item.text(2) if item.text(2) else item.text(0)
                value = self.get_value(self.cbor_data, keys)
                value_type = type(value).__name__
                
                # Use enhanced value editor dialog
                dialog = ValueEditorDialog(original_key, current_value, value_type, self)
                
                if dialog.exec_() == QDialog.Accepted:
                    new_value = dialog.get_value()
                    
                    if str(new_value) != current_value:
                        try:
                            # Validate the new value
                            validated_value = self.validator.validate(keys, new_value, value_type)
                            item.setText(1, str(validated_value))
                            self.update_cbor_data(item, validated_value, value_type)
                            self.status_bar.showMessage("Value updated successfully.", 5000)
                            logger.info(f"Updated {' > '.join(keys)}: {current_value} -> {validated_value}")
                            
                            # Update stats if needed
                            if hasattr(self, 'stats_widget'):
                                self.stats_widget.update_stats(self.cbor_data)
                            
                        except ValueValidationError as e:
                            QMessageBox.warning(self, "Validation Error", str(e))
                            self.status_bar.showMessage("Validation failed.", 5000)
                        except Exception as e:
                            QMessageBox.critical(self, "Error", f"Failed to update value: {e}")
                            self.status_bar.showMessage("Update failed.", 5000)
                            logger.error(f"Failed to update value: {e}")

    def get_value(self, d, keys):
        """Retrieve value from nested dictionary using a list of keys."""
        for key in keys:
            if key.startswith("[") and key.endswith("]"):
                d = d[int(key[1:-1])]
            else:
                d = d[key]
        return d

    def update_cbor_data(self, item, new_value, value_type):
        if item:  # Ensure the item is valid
            keys = []
            while item is not None:
                keys.append(item.text(0))
                item = item.parent()
            keys = list(reversed(keys))

            def set_value(d, keys, value):
                for key in keys[:-1]:
                    if key.startswith("[") and key.endswith("]"):
                        d = d[int(key[1:-1])]
                    else:
                        d = d[key]

                if keys[-1].startswith("[") and keys[-1].endswith("]"):
                    original_value = d[int(keys[-1][1:-1])]
                    d[int(keys[-1][1:-1])] = self.cast_to_correct_type(value, value_type)
                else:
                    original_value = d[keys[-1]]
                    d[keys[-1]] = self.cast_to_correct_type(value, value_type)

            self.changes[tuple(keys)] = {"original": self.get_value(self.cbor_data, keys), "new": new_value, "type": value_type}
            set_value(self.cbor_data, keys, new_value)

    def cast_to_correct_type(self, value, value_type):
        try:
            if value_type == 'int':
                return int(value)
            elif value_type == 'float':
                return float(value)
            elif value_type == 'bool':
                return value.lower() in ['true', '1']
            else:
                return str(value)
        except ValueError:
            return value

    def save_changes(self):
        try:
            if not self.changes:
                QMessageBox.information(self, "No Changes", "No user-made changes to save.")
                return

            # Open the original file data
            with open(self.current_file_path, 'rb') as f:
                original_file_data = f.read()

            # Apply only the changes from self.changes dictionary
            for keys, change in self.changes.items():
                original_value = change["original"]
                new_value = change["new"]
                value_type = change["type"]

                original_bytes = cbor2.dumps(original_value)
                new_bytes = cbor2.dumps(self.cast_to_correct_type(new_value, value_type))

                index = original_file_data.find(original_bytes)

                if index != -1:
                    original_file_data = original_file_data[:index] + new_bytes + original_file_data[index + len(original_bytes):]

            # Update dump size (recalculate based on modified data)
            new_cbor_data = original_file_data[26:-1]  # The new CBOR data section
            new_dump_size = len(new_cbor_data)  # Calculate the new dump size based on CBOR section
            new_dump_size_hex = f'{new_dump_size:08x}'.encode('ascii')  # Convert to hex and encode to ASCII

            # Rebuild the original data with updated dump size
            original_file_data = (
                original_file_data[:8]  # Signature part
                + new_dump_size_hex  # Updated dump size
                + original_file_data[16:]  # Rest of the file
            )

            # Write the updated data back to the file
            with open(self.current_file_path, 'wb') as f:
                f.write(original_file_data)

            self.status_bar.showMessage("Changes saved successfully.", 5000)
            QMessageBox.information(self, "Success", "Data successfully saved to file.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save changes: {e}")
            self.status_bar.showMessage("Failed to save changes.", 5000)

    def get_item_path(self, item):
        """Retrieve the path of keys to the current item."""
        keys = []
        while item is not None:
            keys.append(item.text(0))
            item = item.parent()
        return list(reversed(keys))
    
    def filter_tree_advanced(self, search_text, filters):
        """Advanced filtering with translation support and multiple options"""
        if not search_text:
            # Show all items if search is empty
            self._show_all_items(self.tree.invisibleRootItem())
            return
        
        # Prepare search terms
        search_terms = [search_text]
        if not filters['case_sensitive']:
            search_terms = [term.lower() for term in search_terms]
        
        # Add French translations if enabled
        if filters['french_terms']:
            # Try to find French equivalents
            for french_key, english_key in translator.DIRECT_TRANSLATIONS.items():
                if english_key in search_text.lower():
                    search_terms.append(french_key if filters['case_sensitive'] else french_key.lower())
                elif french_key in search_text.lower():
                    search_terms.append(english_key if filters['case_sensitive'] else english_key.lower())
        
        self._filter_items_advanced(self.tree.invisibleRootItem(), search_terms, filters)
    
    def filter_tree(self, search_text):
        """Simple filter for backward compatibility"""
        filters = {
            'case_sensitive': False,
            'exact_match': False,
            'search_values': True,
            'french_terms': True
        }
        self.filter_tree_advanced(search_text, filters)
    
    def _show_all_items(self, parent):
        """Recursively show all items"""
        for i in range(parent.childCount()):
            child = parent.child(i)
            child.setHidden(False)
            self._show_all_items(child)
    
    def _filter_items(self, parent, search_text):
        """Recursively filter items based on search text"""
        for i in range(parent.childCount()):
            child = parent.child(i)
            
            # Check if this item or any of its children match
            should_show = self._item_matches_search(child, search_text)
            
            # Recursively check children
            child_matches = self._filter_items(child, search_text)
            
            # Show item if it matches or any child matches
            child.setHidden(not (should_show or child_matches))
            
            if should_show or child_matches:
                # Expand parent to show matching children
                child.setExpanded(True)
        
        # Return True if any child was shown
        return any(not parent.child(i).isHidden() for i in range(parent.childCount()))
    
    def _filter_items_advanced(self, parent, search_terms, filters):
        """Advanced recursive filtering with multiple search terms and options"""
        for i in range(parent.childCount()):
            child = parent.child(i)
            
            # Check if this item or any of its children match
            should_show = self._item_matches_search_advanced(child, search_terms, filters)
            
            # Recursively check children
            child_matches = self._filter_items_advanced(child, search_terms, filters)
            
            # Show item if it matches or any child matches
            child.setHidden(not (should_show or child_matches))
            
            if should_show or child_matches:
                # Expand parent to show matching children
                child.setExpanded(True)
        
        # Return True if any child was shown
        return any(not parent.child(i).isHidden() for i in range(parent.childCount()))
    
    def _item_matches_search_advanced(self, item, search_terms, filters):
        """Check if an item matches the advanced search criteria"""
        # Get text to search
        key_text = item.text(0)  # Translated key
        original_key = item.text(2) if item.text(2) else item.text(0)  # Original key
        value_text = item.text(1) if filters['search_values'] else ""
        
        # Apply case sensitivity
        if not filters['case_sensitive']:
            key_text = key_text.lower()
            original_key = original_key.lower()
            value_text = value_text.lower()
        
        # Check all search terms
        for search_term in search_terms:
            if filters['exact_match']:
                # Exact match
                if (search_term == key_text or 
                    search_term == original_key or 
                    (filters['search_values'] and search_term == value_text)):
                    return True
            else:
                # Partial match
                if (search_term in key_text or 
                    search_term in original_key or 
                    (filters['search_values'] and search_term in value_text)):
                    return True
        
        return False
    
    def _item_matches_search(self, item, search_text):
        """Check if an item matches the search criteria (simple version)"""
        key_text = item.text(0).lower()
        original_key = item.text(2).lower() if item.text(2) else ""
        value_text = item.text(1).lower()
        
        return (search_text in key_text or 
                search_text in original_key or 
                search_text in value_text)

def read_and_split_sav_file(file_path):
    with open(file_path, 'rb') as f:
        data = f.read()

    hex_dump, ascii_dump = hex_ascii_display(data)

    signature = data[:8]
    ascii_dump_size = data[8:16]
    separator_1 = data[16:17]
    ascii_unk = data[17:25]
    separator_2 = data[25:26]
    dump_data = data[26:-1]
    separator_3 = data[-1:]

    split_data = {
        "Signature": signature.hex(),
        "ASCII Dump Size": ascii_dump_size.hex(),
        "Separator 1": separator_1.hex(),
        "ASCII Unk": ascii_unk.hex(),
        "Separator 2": separator_2.hex(),
        "Dump Data (first 64 bytes)": dump_data[:64].hex(),
        "Separator 3": separator_3.hex()
    }

    return hex_dump, ascii_dump, split_data, dump_data

def parse_cbor_dump(dump_data):
    """
    Parse CBOR data from save file dump section.
    
    Args:
        dump_data: Raw bytes from save file dump section
        
    Returns:
        Parsed CBOR data as dictionary
        
    Raises:
        CBORParsingError: If CBOR data is malformed
    """
    try:
        cbor_data = cbor2.loads(dump_data)
        logger.info("Successfully parsed CBOR data")
        return cbor_data
    except Exception as e:
        logger.error(f"Error parsing CBOR data: {e}")
        raise CBORParsingError(f"Failed to parse CBOR data: {e}")

def hex_ascii_display(data):
    hex_data = binascii.hexlify(data).decode('utf-8')
    ascii_data = ''.join([chr(byte) if 32 <= byte < 127 else '.' for byte in data])

    hex_dump = ""
    ascii_dump = ""

    for i in range(0, len(hex_data), 32):
        hex_chunk = hex_data[i:i + 32]
        ascii_chunk = ascii_data[i // 2:(i // 2) + (len(hex_chunk) // 2)]
        hex_dump += f"{hex_chunk:32} {ascii_chunk}\n"
        ascii_dump += ascii_chunk

    return hex_dump, ascii_dump

def make_human_readable(data):
    readable_data = []
    if isinstance(data, bytes):
        start = 0
        while True:
            start = data.find(b'\xff\xd8', start)
            if start == -1:
                break
            end = data.find(b'\xff\xd9', start) + 2
            if end == 1:
                break
            jpeg_data = data[start:end]
            try:
                image = Image.open(io.BytesIO(jpeg_data))
                pixmap = pil_image_to_qt_pixmap(image)
                readable_data.append(pixmap)
            except Exception as e:
                readable_data.append(f"Image could not be displayed: {e}")
            start = end
        if not readable_data:
            readable_data = binascii.hexlify(data).decode('utf-8')
    elif isinstance(data, list):
        readable_data = [make_human_readable(item) for item in data]
    elif isinstance(data, dict):
        readable_data = {make_human_readable(key): make_human_readable(value) for key, value in data.items()}
    else:
        readable_data = data
    return readable_data

def pil_image_to_qt_pixmap(image):
    if image.mode != "RGB":
        image = image.convert("RGB")
    image_bytes = image.tobytes("raw", "RGB")
    qimage = QImage(image_bytes, image.width, image.height, QImage.Format_RGB888)
    return QPixmap.fromImage(qimage)

def main():
    """Main entry point for the application"""
    try:
        # Ensure directories exist
        Config.ensure_directories()
        
        app = QApplication(sys.argv)
        viewer = CBORViewerApp()
        viewer.show()
        
        logger.info("Application started successfully")
        sys.exit(app.exec_())
        
    except Exception as e:
        logger.critical(f"Failed to start application: {e}")
        print(f"Critical error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
