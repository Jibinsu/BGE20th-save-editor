"""
Enhanced UI components for the BGE Save Editor.
Provides custom widgets and improved user interface elements.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTreeWidget, QTreeWidgetItem, QTabWidget, QTextEdit, QScrollArea,
    QGroupBox, QSpinBox, QDoubleSpinBox, QCheckBox, QComboBox,
    QProgressBar, QSlider, QFrame, QSplitter, QDialog, QDialogButtonBox,
    QFormLayout, QMessageBox, QToolTip, QApplication
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QPixmap, QIcon, QPalette, QColor
from typing import Dict, Any, Optional, List
import logging

from config import Config
from translations import translator

logger = logging.getLogger(__name__)

class TranslatedTreeWidget(QTreeWidget):
    """Enhanced tree widget with translation support and improved features"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderLabels(["Key (English)", "Value", "Original Key"])
        self.setColumnWidth(0, 250)
        self.setColumnWidth(1, 150)
        self.setColumnWidth(2, 200)
        self.setAlternatingRowColors(True)
        self.setRootIsDecorated(True)
        self.setSortingEnabled(True)
        
        # Enable tooltips
        self.setMouseTracking(True)
        self.itemEntered.connect(self._show_tooltip)
    
    def _show_tooltip(self, item, column):
        """Show tooltip with translation information"""
        if item and column == 0:  # Only for key column
            original_key = item.text(2) if item.text(2) else item.text(0)
            description = translator.get_description(original_key)
            if description:
                tooltip = f"Original: {original_key}\nDescription: {description}"
                QToolTip.showText(self.mapToGlobal(self.visualItemRect(item).center()), tooltip)

class SmartSearchWidget(QWidget):
    """Enhanced search widget with filters and suggestions"""
    
    searchChanged = pyqtSignal(str, dict)  # text, filters
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self._emit_search)
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Main search bar
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search save data... (e.g., 'credits', 'pearls', 'fric')")
        self.search_input.textChanged.connect(self._on_search_changed)
        search_layout.addWidget(self.search_input)
        
        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self.clear_search)
        search_layout.addWidget(self.clear_button)
        
        layout.addLayout(search_layout)
        
        # Filter options
        filter_group = QGroupBox("Search Filters")
        filter_layout = QHBoxLayout(filter_group)
        
        self.case_sensitive = QCheckBox("Case Sensitive")
        filter_layout.addWidget(self.case_sensitive)
        
        self.exact_match = QCheckBox("Exact Match")
        filter_layout.addWidget(self.exact_match)
        
        self.search_values = QCheckBox("Search Values")
        self.search_values.setChecked(True)
        filter_layout.addWidget(self.search_values)
        
        self.french_terms = QCheckBox("Include French Terms")
        self.french_terms.setChecked(True)
        filter_layout.addWidget(self.french_terms)
        
        filter_layout.addStretch()
        layout.addWidget(filter_group)
        
        # Connect filter changes
        for checkbox in [self.case_sensitive, self.exact_match, self.search_values, self.french_terms]:
            checkbox.toggled.connect(self._on_filter_changed)
    
    def _on_search_changed(self):
        """Handle search text changes with debouncing"""
        self.search_timer.stop()
        self.search_timer.start(300)  # 300ms delay
    
    def _on_filter_changed(self):
        """Handle filter changes"""
        self._emit_search()
    
    def _emit_search(self):
        """Emit search signal with current text and filters"""
        filters = {
            'case_sensitive': self.case_sensitive.isChecked(),
            'exact_match': self.exact_match.isChecked(),
            'search_values': self.search_values.isChecked(),
            'french_terms': self.french_terms.isChecked()
        }
        self.searchChanged.emit(self.search_input.text(), filters)
    
    def clear_search(self):
        """Clear search input"""
        self.search_input.clear()

class ValueEditorDialog(QDialog):
    """Enhanced dialog for editing values with validation and suggestions"""
    
    def __init__(self, key: str, current_value: str, value_type: str, parent=None):
        super().__init__(parent)
        self.key = key
        self.current_value = current_value
        self.value_type = value_type
        self.validated_value = None
        
        self.setup_ui()
        self.setModal(True)
        self.resize(400, 300)
    
    def setup_ui(self):
        """Setup the dialog UI"""
        layout = QVBoxLayout(self)
        
        # Title and description
        title = QLabel(f"Edit Value: {translator.translate_key(self.key)}")
        title.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(title)
        
        # Show original key if translated
        translated_key = translator.translate_key(self.key)
        if translated_key != self.key:
            original_label = QLabel(f"Original key: {self.key}")
            original_label.setStyleSheet("color: #888888; font-style: italic;")
            layout.addWidget(original_label)
        
        # Description
        description = translator.get_description(self.key)
        if description:
            desc_label = QLabel(f"Description: {description}")
            desc_label.setWordWrap(True)
            desc_label.setStyleSheet("color: #666666; margin: 5px 0;")
            layout.addWidget(desc_label)
        
        # Value editing area
        form_layout = QFormLayout()
        
        form_layout.addRow("Type:", QLabel(self.value_type))
        form_layout.addRow("Current Value:", QLabel(str(self.current_value)))
        
        # Create appropriate input widget based on type
        self.input_widget = self._create_input_widget()
        form_layout.addRow("New Value:", self.input_widget)
        
        layout.addLayout(form_layout)
        
        # Validation info
        self.validation_info = QLabel()
        self.validation_info.setWordWrap(True)
        self.validation_info.setStyleSheet("color: #0066cc; font-size: 10px;")
        layout.addWidget(self.validation_info)
        
        # Show validation limits if available
        self._show_validation_info()
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def _create_input_widget(self):
        """Create appropriate input widget based on value type"""
        if 'int' in self.value_type.lower():
            widget = QSpinBox()
            widget.setRange(-2147483648, 2147483647)
            try:
                widget.setValue(int(self.current_value))
            except ValueError:
                widget.setValue(0)
            return widget
        
        elif 'float' in self.value_type.lower():
            widget = QDoubleSpinBox()
            widget.setRange(-999999.99, 999999.99)
            widget.setDecimals(6)
            try:
                widget.setValue(float(self.current_value))
            except ValueError:
                widget.setValue(0.0)
            return widget
        
        elif 'bool' in self.value_type.lower():
            widget = QCheckBox()
            widget.setChecked(str(self.current_value).lower() in ['true', '1', 'yes'])
            return widget
        
        else:
            widget = QLineEdit()
            widget.setText(str(self.current_value))
            return widget
    
    def _show_validation_info(self):
        """Show validation information for the field"""
        from validators import ValueValidator
        validator = ValueValidator()
        
        # Get validation info
        key_parts = self.key.split('_')
        info_parts = []
        
        # Check for known validation rules
        if any(term in self.key.lower() for term in ['credit', 'fric', 'argent']):
            info_parts.append("Credits: 0 - 999,999")
        elif any(term in self.key.lower() for term in ['pearl', 'perle']):
            info_parts.append("Pearls: 0 - 88 (total collectible pearls)")
        elif any(term in self.key.lower() for term in ['health', 'vie', 'sante']):
            info_parts.append("Health: 0 - 100")
        
        if info_parts:
            self.validation_info.setText("Validation limits: " + ", ".join(info_parts))
    
    def get_value(self):
        """Get the entered value"""
        if isinstance(self.input_widget, QSpinBox):
            return self.input_widget.value()
        elif isinstance(self.input_widget, QDoubleSpinBox):
            return self.input_widget.value()
        elif isinstance(self.input_widget, QCheckBox):
            return self.input_widget.isChecked()
        else:
            return self.input_widget.text()

class StatsWidget(QWidget):
    """Widget to display save file statistics"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.stats = {}
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        title = QLabel("Save File Statistics")
        title.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(title)
        
        self.stats_layout = QFormLayout()
        layout.addLayout(self.stats_layout)
        
        # Progress bars for key stats
        self.progress_bars = {}
        
    def update_stats(self, data: Dict[str, Any]):
        """Update statistics from save data"""
        # Clear existing stats
        for i in reversed(range(self.stats_layout.count())):
            self.stats_layout.itemAt(i).widget().setParent(None)
        
        self.stats = self._calculate_stats(data)
        
        # Display stats
        for key, value in self.stats.items():
            if isinstance(value, (int, float)):
                if key in ['credits', 'pearls', 'health']:
                    # Create progress bar for important stats
                    progress = QProgressBar()
                    max_val = self._get_max_value(key)
                    progress.setMaximum(max_val)
                    progress.setValue(min(int(value), max_val))
                    progress.setFormat(f"{value} / {max_val}")
                    self.stats_layout.addRow(f"{key.title()}:", progress)
                else:
                    self.stats_layout.addRow(f"{key.title()}:", QLabel(str(value)))
            else:
                self.stats_layout.addRow(f"{key.title()}:", QLabel(str(value)))
    
    def _calculate_stats(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate statistics from save data"""
        stats = {
            'total_fields': 0,
            'translated_fields': 0,
            'credits': 0,
            'pearls': 0,
            'health': 0,
        }
        
        def count_fields(obj, path=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    stats['total_fields'] += 1
                    
                    # Check if field is translated
                    translated = translator.translate_key(key)
                    if translated != key:
                        stats['translated_fields'] += 1
                    
                    # Extract specific stats
                    key_lower = key.lower()
                    if 'credit' in key_lower or 'fric' in key_lower:
                        try:
                            stats['credits'] = max(stats['credits'], int(value))
                        except (ValueError, TypeError):
                            pass
                    elif 'pearl' in key_lower or 'perle' in key_lower:
                        try:
                            stats['pearls'] = max(stats['pearls'], int(value))
                        except (ValueError, TypeError):
                            pass
                    elif 'health' in key_lower or 'vie' in key_lower:
                        try:
                            stats['health'] = max(stats['health'], int(value))
                        except (ValueError, TypeError):
                            pass
                    
                    count_fields(value, f"{path}.{key}" if path else key)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    count_fields(item, f"{path}[{i}]")
        
        count_fields(data)
        return stats
    
    def _get_max_value(self, key: str) -> int:
        """Get maximum expected value for a stat"""
        max_values = {
            'credits': 999999,
            'pearls': 88,
            'health': 100,
        }
        return max_values.get(key, 100)

class EnhancedDetailView(QTextEdit):
    """Enhanced detail view with syntax highlighting and better formatting"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setFont(QFont("Consolas", 10))
    
    def display_item_details(self, key: str, value: Any, item_path: List[str]):
        """Display detailed information about an item"""
        details = []
        
        # Header
        details.append("=" * 50)
        details.append(f"ITEM DETAILS")
        details.append("=" * 50)
        details.append("")
        
        # Key information
        translated_key = translator.translate_key(key)
        details.append(f"Key: {key}")
        if translated_key != key:
            details.append(f"English: {translated_key}")
        
        description = translator.get_description(key)
        if description:
            details.append(f"Description: {description}")
        
        details.append(f"Path: {' > '.join(item_path)}")
        details.append("")
        
        # Value information
        details.append(f"Value: {value}")
        details.append(f"Type: {type(value).__name__}")
        
        if isinstance(value, (int, float)):
            details.append(f"Numeric value: {value:,}")
        elif isinstance(value, str):
            details.append(f"String length: {len(value)} characters")
        elif isinstance(value, (list, dict)):
            details.append(f"Container size: {len(value)} items")
        
        details.append("")
        
        # Search terms
        search_terms = translator.get_search_terms(key)
        details.append(f"Search terms: {', '.join(search_terms)}")
        
        # Validation info
        details.append("")
        details.append("VALIDATION INFO:")
        details.append("-" * 20)
        
        if 'credit' in key.lower() or 'fric' in key.lower():
            details.append("• Credits field - Range: 0 to 999,999")
        elif 'pearl' in key.lower() or 'perle' in key.lower():
            details.append("• Pearl collectible - Range: 0 to 88")
        elif 'health' in key.lower() or 'vie' in key.lower():
            details.append("• Health value - Range: 0 to 100")
        else:
            details.append("• No specific validation rules")
        
        self.setPlainText("\n".join(details))