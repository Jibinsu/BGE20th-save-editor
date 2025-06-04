"""
Enhanced UI Components for BGE Save Editor v4.0.0
Specialized widgets for pearls, inventory, companions, and undo/redo
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QTabWidget,
    QTreeWidget, QTreeWidgetItem, QLabel, QPushButton, QProgressBar,
    QSpinBox, QDoubleSpinBox, QComboBox, QCheckBox, QTextEdit,
    QGroupBox, QSplitter, QFrame, QScrollArea, QListWidget,
    QListWidgetItem, QDialog, QDialogButtonBox, QFormLayout,
    QSlider, QToolButton, QMenu, QAction, QHeaderView
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QIcon, QPixmap, QFont, QPalette, QColor

from pearls_manager import pearls_manager, PearlType, PearlInfo
from inventory_manager import inventory_manager, ItemType, ItemRarity, InventoryItem
from companion_manager import companion_manager, CompanionType, CompanionStatus, CompanionData
from undo_system import undo_system

class UndoRedoWidget(QWidget):
    """Widget for undo/redo functionality"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.setup_connections()
        self.update_buttons()
        
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Undo button
        self.undo_button = QPushButton("↶ Undo")
        self.undo_button.setToolTip("Undo last action")
        self.undo_button.setEnabled(False)
        
        # Redo button
        self.redo_button = QPushButton("↷ Redo")
        self.redo_button.setToolTip("Redo last undone action")
        self.redo_button.setEnabled(False)
        
        # History button
        self.history_button = QPushButton("📋 History")
        self.history_button.setToolTip("View action history")
        
        # Clear history button
        self.clear_button = QPushButton("🗑️ Clear")
        self.clear_button.setToolTip("Clear all history")
        
        layout.addWidget(self.undo_button)
        layout.addWidget(self.redo_button)
        layout.addWidget(self.history_button)
        layout.addWidget(self.clear_button)
        layout.addStretch()
        
    def setup_connections(self):
        self.undo_button.clicked.connect(self.undo_action)
        self.redo_button.clicked.connect(self.redo_action)
        self.history_button.clicked.connect(self.show_history)
        self.clear_button.clicked.connect(self.clear_history)
        
        # Listen for undo system changes
        undo_system.add_change_callback(self.update_buttons)
        
    def update_buttons(self):
        """Update button states based on undo system"""
        info = undo_system.get_history_info()
        
        self.undo_button.setEnabled(info["can_undo"])
        self.redo_button.setEnabled(info["can_redo"])
        
        # Update tooltips with action descriptions
        if info["undo_description"]:
            self.undo_button.setToolTip(f"Undo: {info['undo_description']}")
        else:
            self.undo_button.setToolTip("No actions to undo")
            
        if info["redo_description"]:
            self.redo_button.setToolTip(f"Redo: {info['redo_description']}")
        else:
            self.redo_button.setToolTip("No actions to redo")
    
    def undo_action(self):
        """Perform undo action"""
        # This will be connected to the main application's undo method
        pass
    
    def redo_action(self):
        """Perform redo action"""
        # This will be connected to the main application's redo method
        pass
    
    def show_history(self):
        """Show action history dialog"""
        dialog = UndoHistoryDialog(self)
        dialog.exec_()
    
    def clear_history(self):
        """Clear all history"""
        undo_system.clear_history()

class UndoHistoryDialog(QDialog):
    """Dialog showing undo/redo history"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Action History")
        self.setModal(True)
        self.resize(500, 400)
        self.setup_ui()
        self.load_history()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # History list
        self.history_list = QListWidget()
        layout.addWidget(self.history_list)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
    def load_history(self):
        """Load history into the list"""
        self.history_list.clear()
        
        # Add undo stack (in reverse order)
        for i, action in enumerate(reversed(undo_system.undo_stack)):
            item = QListWidgetItem(f"[{len(undo_system.undo_stack) - i}] {action.description}")
            item.setToolTip(f"Type: {action.action_type.value}\nTime: {action.timestamp}")
            self.history_list.addItem(item)
        
        # Add current position indicator
        if undo_system.undo_stack:
            current_item = QListWidgetItem("--- Current Position ---")
            current_item.setBackground(QColor(200, 200, 200))
            self.history_list.addItem(current_item)
        
        # Add redo stack
        for i, action in enumerate(undo_system.redo_stack):
            item = QListWidgetItem(f"[Redo {i+1}] {action.description}")
            item.setToolTip(f"Type: {action.action_type.value}\nTime: {action.timestamp}")
            item.setForeground(QColor(128, 128, 128))
            self.history_list.addItem(item)

class PearlsWidget(QWidget):
    """Widget for managing pearls"""
    
    pearl_changed = pyqtSignal(str, bool)  # pearl_id, collected
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.setup_connections()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header with stats
        header_layout = QHBoxLayout()
        
        self.stats_label = QLabel("Pearls: 0/0 (0%)")
        self.stats_label.setFont(QFont("Arial", 10, QFont.Bold))
        
        # Action buttons
        self.collect_all_button = QPushButton("Collect All")
        self.uncollect_all_button = QPushButton("Uncollect All")
        self.refresh_button = QPushButton("🔄 Refresh")
        
        header_layout.addWidget(self.stats_label)
        header_layout.addStretch()
        header_layout.addWidget(self.collect_all_button)
        header_layout.addWidget(self.uncollect_all_button)
        header_layout.addWidget(self.refresh_button)
        
        layout.addLayout(header_layout)
        
        # Pearl tree
        self.pearl_tree = QTreeWidget()
        self.pearl_tree.setHeaderLabels(["Pearl", "Status", "Type", "Location", "Value"])
        self.pearl_tree.setAlternatingRowColors(True)
        self.pearl_tree.setSortingEnabled(True)
        
        layout.addWidget(self.pearl_tree)
        
        # Progress bars by type
        progress_group = QGroupBox("Collection Progress by Type")
        progress_layout = QGridLayout(progress_group)
        
        self.progress_bars = {}
        for i, pearl_type in enumerate(PearlType):
            label = QLabel(f"{pearl_type.value.title()}:")
            progress_bar = QProgressBar()
            progress_bar.setFormat("%v/%m (%p%)")
            
            progress_layout.addWidget(label, i, 0)
            progress_layout.addWidget(progress_bar, i, 1)
            
            self.progress_bars[pearl_type] = progress_bar
        
        layout.addWidget(progress_group)
        
    def setup_connections(self):
        self.collect_all_button.clicked.connect(self.collect_all_pearls)
        self.uncollect_all_button.clicked.connect(self.uncollect_all_pearls)
        self.refresh_button.clicked.connect(self.refresh_pearls)
        self.pearl_tree.itemChanged.connect(self.on_pearl_item_changed)
        
    def refresh_pearls(self):
        """Refresh the pearl display"""
        self.pearl_tree.clear()
        
        # Group pearls by type
        pearl_groups = {}
        for pearl_type in PearlType:
            pearls = pearls_manager.get_pearls_by_type(pearl_type)
            if pearls:
                pearl_groups[pearl_type] = pearls
        
        # Add pearls to tree
        for pearl_type, pearls in pearl_groups.items():
            type_item = QTreeWidgetItem([pearl_type.value.title(), "", "", "", ""])
            type_item.setFont(0, QFont("Arial", 9, QFont.Bold))
            self.pearl_tree.addTopLevelItem(type_item)
            
            for pearl in pearls:
                pearl_item = QTreeWidgetItem([
                    pearl.name,
                    "✓ Collected" if pearl.collected else "✗ Not Collected",
                    pearl.pearl_type.value,
                    pearl.location,
                    str(pearl.value)
                ])
                
                # Add checkbox
                pearl_item.setFlags(pearl_item.flags() | Qt.ItemIsUserCheckable)
                pearl_item.setCheckState(0, Qt.Checked if pearl.collected else Qt.Unchecked)
                pearl_item.setData(0, Qt.UserRole, pearl.id)
                
                # Color coding
                if pearl.collected:
                    pearl_item.setBackground(0, QColor(200, 255, 200))
                
                type_item.addChild(pearl_item)
            
            type_item.setExpanded(True)
        
        # Update stats
        self.update_stats()
        
    def update_stats(self):
        """Update statistics display"""
        stats = pearls_manager.get_pearl_stats()
        
        # Main stats
        self.stats_label.setText(
            f"Pearls: {stats['collected_pearls']}/{stats['total_pearls']} "
            f"({stats['collection_percentage']:.1f}%) - "
            f"Value: {stats['total_value']}"
        )
        
        # Progress bars by type
        for pearl_type, progress_bar in self.progress_bars.items():
            type_stats = stats["by_type"][pearl_type.value]
            progress_bar.setMaximum(type_stats["total"])
            progress_bar.setValue(type_stats["collected"])
    
    def on_pearl_item_changed(self, item, column):
        """Handle pearl item check state change"""
        if column == 0 and item.data(0, Qt.UserRole):
            pearl_id = item.data(0, Qt.UserRole)
            collected = item.checkState(0) == Qt.Checked
            
            if pearls_manager.set_pearl_collected(pearl_id, collected):
                self.pearl_changed.emit(pearl_id, collected)
                self.update_stats()
    
    def collect_all_pearls(self):
        """Collect all pearls"""
        count = pearls_manager.collect_all_pearls()
        self.refresh_pearls()
        
    def uncollect_all_pearls(self):
        """Uncollect all pearls"""
        count = pearls_manager.uncollect_all_pearls()
        self.refresh_pearls()

class InventoryWidget(QWidget):
    """Widget for managing inventory"""
    
    inventory_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.setup_connections()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header with stats
        header_layout = QHBoxLayout()
        
        self.stats_label = QLabel("Items: 0 (Total: 0)")
        self.stats_label.setFont(QFont("Arial", 10, QFont.Bold))
        
        # Filter combo
        self.filter_combo = QComboBox()
        self.filter_combo.addItem("All Items", None)
        for item_type in ItemType:
            self.filter_combo.addItem(item_type.value.title(), item_type)
        
        # Action buttons
        self.add_all_button = QPushButton("Add All Items")
        self.clear_button = QPushButton("Clear Inventory")
        self.refresh_button = QPushButton("🔄 Refresh")
        
        header_layout.addWidget(self.stats_label)
        header_layout.addWidget(QLabel("Filter:"))
        header_layout.addWidget(self.filter_combo)
        header_layout.addStretch()
        header_layout.addWidget(self.add_all_button)
        header_layout.addWidget(self.clear_button)
        header_layout.addWidget(self.refresh_button)
        
        layout.addLayout(header_layout)
        
        # Inventory tree
        self.inventory_tree = QTreeWidget()
        self.inventory_tree.setHeaderLabels(["Item", "Quantity", "Equipped", "Type", "Rarity", "Value"])
        self.inventory_tree.setAlternatingRowColors(True)
        self.inventory_tree.setSortingEnabled(True)
        
        layout.addWidget(self.inventory_tree)
        
        # Stats by type
        stats_group = QGroupBox("Inventory Statistics")
        stats_layout = QGridLayout(stats_group)
        
        self.type_labels = {}
        for i, item_type in enumerate(ItemType):
            label = QLabel(f"{item_type.value.title()}:")
            count_label = QLabel("0")
            
            stats_layout.addWidget(label, i // 2, (i % 2) * 2)
            stats_layout.addWidget(count_label, i // 2, (i % 2) * 2 + 1)
            
            self.type_labels[item_type] = count_label
        
        layout.addWidget(stats_group)
        
    def setup_connections(self):
        self.filter_combo.currentIndexChanged.connect(self.refresh_inventory)
        self.add_all_button.clicked.connect(self.add_all_items)
        self.clear_button.clicked.connect(self.clear_inventory)
        self.refresh_button.clicked.connect(self.refresh_inventory)
        self.inventory_tree.itemDoubleClicked.connect(self.edit_item)
        
    def refresh_inventory(self):
        """Refresh the inventory display"""
        self.inventory_tree.clear()
        
        # Get filter
        filter_type = self.filter_combo.currentData()
        
        # Get items
        if filter_type:
            items = inventory_manager.get_items_by_type(filter_type)
        else:
            items = inventory_manager.get_all_items()
        
        # Group items by type
        item_groups = {}
        for item in items:
            item_type = item.item_info.item_type
            if item_type not in item_groups:
                item_groups[item_type] = []
            item_groups[item_type].append(item)
        
        # Add items to tree
        for item_type, type_items in item_groups.items():
            if filter_type and item_type != filter_type:
                continue
                
            type_item = QTreeWidgetItem([item_type.value.title(), "", "", "", "", ""])
            type_item.setFont(0, QFont("Arial", 9, QFont.Bold))
            self.inventory_tree.addTopLevelItem(type_item)
            
            for item in type_items:
                item_widget = QTreeWidgetItem([
                    item.item_info.name,
                    str(item.quantity),
                    "✓ Equipped" if item.equipped else "✗ Not Equipped",
                    item.item_info.item_type.value,
                    item.item_info.rarity.value,
                    str(item.item_info.value * item.quantity)
                ])
                
                item_widget.setData(0, Qt.UserRole, item.item_info.id)
                
                # Color coding by rarity
                rarity_colors = {
                    ItemRarity.COMMON: QColor(255, 255, 255),
                    ItemRarity.UNCOMMON: QColor(200, 255, 200),
                    ItemRarity.RARE: QColor(200, 200, 255),
                    ItemRarity.EPIC: QColor(255, 200, 255),
                    ItemRarity.LEGENDARY: QColor(255, 215, 0)
                }
                
                color = rarity_colors.get(item.item_info.rarity, QColor(255, 255, 255))
                item_widget.setBackground(0, color)
                
                type_item.addChild(item_widget)
            
            type_item.setExpanded(True)
        
        # Update stats
        self.update_stats()
        
    def update_stats(self):
        """Update statistics display"""
        stats = inventory_manager.get_inventory_stats()
        
        # Main stats
        self.stats_label.setText(
            f"Items: {stats['total_items']} "
            f"(Total Quantity: {stats['total_quantity']}) - "
            f"Value: {stats['total_value']}"
        )
        
        # Type stats
        for item_type, label in self.type_labels.items():
            type_stats = stats["by_type"][item_type.value]
            label.setText(f"{type_stats['count']} ({type_stats['total_quantity']})")
    
    def edit_item(self, item, column):
        """Edit an inventory item"""
        item_id = item.data(0, Qt.UserRole)
        if item_id:
            dialog = ItemEditDialog(item_id, self)
            if dialog.exec_() == QDialog.Accepted:
                self.refresh_inventory()
                self.inventory_changed.emit()
    
    def add_all_items(self):
        """Add all known items to inventory"""
        count = inventory_manager.add_all_items()
        self.refresh_inventory()
        
    def clear_inventory(self):
        """Clear all items from inventory"""
        count = inventory_manager.clear_inventory()
        self.refresh_inventory()

class ItemEditDialog(QDialog):
    """Dialog for editing inventory items"""
    
    def __init__(self, item_id, parent=None):
        super().__init__(parent)
        self.item_id = item_id
        self.setWindowTitle(f"Edit Item: {item_id}")
        self.setModal(True)
        self.setup_ui()
        self.load_item_data()
        
    def setup_ui(self):
        layout = QFormLayout(self)
        
        # Quantity
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setRange(0, 999)
        layout.addRow("Quantity:", self.quantity_spin)
        
        # Equipped
        self.equipped_check = QCheckBox()
        layout.addRow("Equipped:", self.equipped_check)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addRow(button_box)
        
    def load_item_data(self):
        """Load current item data"""
        items = inventory_manager.get_all_items()
        for item in items:
            if item.item_info.id == self.item_id:
                self.quantity_spin.setValue(item.quantity)
                self.equipped_check.setChecked(item.equipped)
                break
    
    def accept(self):
        """Apply changes and close"""
        quantity = self.quantity_spin.value()
        equipped = self.equipped_check.isChecked()
        
        # Update item
        if quantity > 0:
            # Set quantity (this is complex, would need new methods)
            inventory_manager.set_item_equipped(self.item_id, equipped)
        else:
            inventory_manager.remove_item(self.item_id)
        
        super().accept()

class CompanionsWidget(QWidget):
    """Widget for managing companions"""
    
    companion_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.setup_connections()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header with stats
        header_layout = QHBoxLayout()
        
        self.stats_label = QLabel("Companions: 0 (Active: 0)")
        self.stats_label.setFont(QFont("Arial", 10, QFont.Bold))
        
        # Action buttons
        self.heal_all_button = QPushButton("Heal All")
        self.activate_all_button = QPushButton("Activate All")
        self.max_loyalty_button = QPushButton("Max Loyalty")
        self.refresh_button = QPushButton("🔄 Refresh")
        
        header_layout.addWidget(self.stats_label)
        header_layout.addStretch()
        header_layout.addWidget(self.heal_all_button)
        header_layout.addWidget(self.activate_all_button)
        header_layout.addWidget(self.max_loyalty_button)
        header_layout.addWidget(self.refresh_button)
        
        layout.addLayout(header_layout)
        
        # Companion tree
        self.companion_tree = QTreeWidget()
        self.companion_tree.setHeaderLabels([
            "Companion", "Status", "Health", "Energy", "Level", "Loyalty", "Type"
        ])
        self.companion_tree.setAlternatingRowColors(True)
        
        layout.addWidget(self.companion_tree)
        
    def setup_connections(self):
        self.heal_all_button.clicked.connect(self.heal_all_companions)
        self.activate_all_button.clicked.connect(self.activate_all_companions)
        self.max_loyalty_button.clicked.connect(self.max_loyalty_all)
        self.refresh_button.clicked.connect(self.refresh_companions)
        self.companion_tree.itemDoubleClicked.connect(self.edit_companion)
        
    def refresh_companions(self):
        """Refresh the companion display"""
        self.companion_tree.clear()
        
        # Group companions by type
        companion_groups = {}
        for comp_type in CompanionType:
            companions = companion_manager.get_companions_by_type(comp_type)
            if companions:
                companion_groups[comp_type] = companions
        
        # Add companions to tree
        for comp_type, companions in companion_groups.items():
            type_item = QTreeWidgetItem([comp_type.value.title(), "", "", "", "", "", ""])
            type_item.setFont(0, QFont("Arial", 9, QFont.Bold))
            self.companion_tree.addTopLevelItem(type_item)
            
            for companion in companions:
                comp_item = QTreeWidgetItem([
                    companion.companion_info.name,
                    companion.status.value,
                    f"{companion.health:.1f}/{companion.companion_info.max_health:.1f}",
                    f"{companion.energy:.1f}/{companion.companion_info.max_energy:.1f}",
                    str(companion.level),
                    f"{companion.loyalty:.1f}%",
                    companion.companion_info.companion_type.value
                ])
                
                comp_item.setData(0, Qt.UserRole, companion.companion_info.id)
                
                # Color coding by status
                status_colors = {
                    CompanionStatus.ACTIVE: QColor(200, 255, 200),
                    CompanionStatus.INACTIVE: QColor(255, 255, 200),
                    CompanionStatus.INJURED: QColor(255, 200, 200),
                    CompanionStatus.MISSING: QColor(200, 200, 200)
                }
                
                color = status_colors.get(companion.status, QColor(255, 255, 255))
                comp_item.setBackground(0, color)
                
                type_item.addChild(comp_item)
            
            type_item.setExpanded(True)
        
        # Update stats
        self.update_stats()
        
    def update_stats(self):
        """Update statistics display"""
        stats = companion_manager.get_companion_stats()
        
        self.stats_label.setText(
            f"Companions: {stats['total_companions']} "
            f"(Active: {stats['active_companions']}) - "
            f"Avg Health: {stats['average_health']:.1f}% - "
            f"Avg Loyalty: {stats['average_loyalty']:.1f}%"
        )
    
    def edit_companion(self, item, column):
        """Edit a companion"""
        comp_id = item.data(0, Qt.UserRole)
        if comp_id:
            dialog = CompanionEditDialog(comp_id, self)
            if dialog.exec_() == QDialog.Accepted:
                self.refresh_companions()
                self.companion_changed.emit()
    
    def heal_all_companions(self):
        """Heal all companions"""
        count = companion_manager.heal_all_companions()
        self.refresh_companions()
        
    def activate_all_companions(self):
        """Activate all companions"""
        count = companion_manager.activate_all_companions()
        self.refresh_companions()
        
    def max_loyalty_all(self):
        """Set all companions to max loyalty"""
        count = companion_manager.max_loyalty_all_companions()
        self.refresh_companions()

class CompanionEditDialog(QDialog):
    """Dialog for editing companions"""
    
    def __init__(self, comp_id, parent=None):
        super().__init__(parent)
        self.comp_id = comp_id
        self.companion = None
        self.setWindowTitle(f"Edit Companion: {comp_id}")
        self.setModal(True)
        self.setup_ui()
        self.load_companion_data()
        
    def setup_ui(self):
        layout = QFormLayout(self)
        
        # Status
        self.status_combo = QComboBox()
        for status in CompanionStatus:
            self.status_combo.addItem(status.value, status)
        layout.addRow("Status:", self.status_combo)
        
        # Health
        self.health_spin = QDoubleSpinBox()
        self.health_spin.setRange(0.0, 1000.0)
        self.health_spin.setDecimals(1)
        layout.addRow("Health:", self.health_spin)
        
        # Energy
        self.energy_spin = QDoubleSpinBox()
        self.energy_spin.setRange(0.0, 1000.0)
        self.energy_spin.setDecimals(1)
        layout.addRow("Energy:", self.energy_spin)
        
        # Level
        self.level_spin = QSpinBox()
        self.level_spin.setRange(1, 50)
        layout.addRow("Level:", self.level_spin)
        
        # Loyalty
        self.loyalty_spin = QDoubleSpinBox()
        self.loyalty_spin.setRange(0.0, 100.0)
        self.loyalty_spin.setDecimals(1)
        self.loyalty_spin.setSuffix("%")
        layout.addRow("Loyalty:", self.loyalty_spin)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addRow(button_box)
        
    def load_companion_data(self):
        """Load current companion data"""
        companions = companion_manager.get_all_companions()
        for companion in companions:
            if companion.companion_info.id == self.comp_id:
                self.companion = companion
                
                # Set current values
                for i in range(self.status_combo.count()):
                    if self.status_combo.itemData(i) == companion.status:
                        self.status_combo.setCurrentIndex(i)
                        break
                
                self.health_spin.setValue(companion.health)
                self.health_spin.setMaximum(companion.companion_info.max_health)
                
                self.energy_spin.setValue(companion.energy)
                self.energy_spin.setMaximum(companion.companion_info.max_energy)
                
                self.level_spin.setValue(companion.level)
                self.loyalty_spin.setValue(companion.loyalty)
                break
    
    def accept(self):
        """Apply changes and close"""
        if not self.companion:
            return
        
        # Apply changes
        status = self.status_combo.currentData()
        health = self.health_spin.value()
        energy = self.energy_spin.value()
        level = self.level_spin.value()
        loyalty = self.loyalty_spin.value()
        
        companion_manager.set_companion_status(self.comp_id, status)
        companion_manager.set_companion_health(self.comp_id, health)
        companion_manager.set_companion_energy(self.comp_id, energy)
        companion_manager.set_companion_level(self.comp_id, level)
        companion_manager.set_companion_loyalty(self.comp_id, loyalty)
        
        super().accept()

class V4TabWidget(QTabWidget):
    """Main tab widget for v4 features"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_tabs()
        
    def setup_tabs(self):
        """Setup all v4 feature tabs"""
        
        # Undo/Redo tab
        self.undo_widget = UndoRedoWidget()
        
        # Pearls tab
        self.pearls_widget = PearlsWidget()
        self.addTab(self.pearls_widget, "🔮 Pearls")
        
        # Inventory tab
        self.inventory_widget = InventoryWidget()
        self.addTab(self.inventory_widget, "🎒 Inventory")
        
        # Companions tab
        self.companions_widget = CompanionsWidget()
        self.addTab(self.companions_widget, "🤝 Companions")
    
    def set_save_data(self, save_data):
        """Set save data for all managers"""
        pearls_manager.set_save_data(save_data)
        inventory_manager.set_save_data(save_data)
        companion_manager.set_save_data(save_data)
        
        # Refresh all widgets
        self.pearls_widget.refresh_pearls()
        self.inventory_widget.refresh_inventory()
        self.companions_widget.refresh_companions()
    
    def get_undo_widget(self):
        """Get the undo/redo widget for toolbar"""
        return self.undo_widget