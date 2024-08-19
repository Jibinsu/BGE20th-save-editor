import sys
import binascii
import cbor2
import io
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QTreeWidget, QTreeWidgetItem,
    QLabel, QVBoxLayout, QWidget, QScrollArea, QMessageBox, QInputDialog,
    QSplitter, QStatusBar, QTabWidget, QAction, QTextEdit
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage
from PIL import Image

class CBORViewerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BGE 20th Anniversary Save Editor")
        self.setGeometry(100, 100, 1000, 700)

        self.original_data = None
        self.cbor_data = None
        self.human_readable_data = None
        self.changes = {}  # Track all changes here
        self.current_file_path = None

        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        splitter = QSplitter(Qt.Horizontal)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Key", "Value"])
        self.tree.itemClicked.connect(self.on_item_clicked)
        self.tree.itemDoubleClicked.connect(self.on_item_double_click)
        splitter.addWidget(self.tree)

        tabs = QTabWidget()

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.scroll_area.setWidget(self.image_label)
        tabs.addTab(self.scroll_area, "Image Viewer")

        self.detail_view = QTextEdit()
        self.detail_view.setReadOnly(True)
        tabs.addTab(self.detail_view, "Details")

        splitter.addWidget(tabs)

        layout.addWidget(splitter)

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

    def open_file(self):
        try:
            file_path, _ = QFileDialog.getOpenFileName(self, "Select a .sav file", "", "SAV files (*.sav)")
            if not file_path:
                return

            self.current_file_path = file_path  # Store the current file path

            with open(file_path, 'rb') as f:
                self.original_data = f.read()

            _, _, self.split_data, self.dump_data = read_and_split_sav_file(file_path)
            self.cbor_data = parse_cbor_dump(self.dump_data)

            if not self.cbor_data:
                QMessageBox.critical(self, "Error", "Failed to parse CBOR data.")
                return

            self.human_readable_data = make_human_readable(self.cbor_data)
            self.populate_tree(self.human_readable_data)
            self.status_bar.showMessage("File loaded successfully.", 5000)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open file: {e}")
            self.status_bar.showMessage("Failed to load file.", 5000)

    def populate_tree(self, data, parent=None):
        if parent is None:
            self.tree.clear()
            parent = self.tree.invisibleRootItem()

        if isinstance(data, dict):
            for key, value in data.items():
                item = QTreeWidgetItem([str(key), ""])
                parent.addChild(item)
                self.populate_tree(value, item)
        elif isinstance(data, list):
            for index, value in enumerate(data):
                item = QTreeWidgetItem([f"[{index}]", ""])
                parent.addChild(item)
                self.populate_tree(value, item)
        else:
            if isinstance(data, QPixmap):
                item = QTreeWidgetItem([f"Image {parent.childCount()}", "Double-click to view"])
                item.setData(0, Qt.UserRole, data)
                parent.addChild(item)
            else:
                parent.setText(1, str(data))

    def on_item_clicked(self, item, column):
        """Show details when an item is clicked."""
        if item:  # Ensure the item is valid
            if not isinstance(item.data(0, Qt.UserRole), QPixmap):
                details = self.get_detailed_information(item)
                self.detail_view.setText(details)

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
                current_details = self.get_detailed_information(item)
                value_type = current_details.split('Type: ')[1].strip()
                new_value, ok = QInputDialog.getText(self, "Edit Value", f"New Value (Type: {value_type}):", text=current_value)
                if ok and new_value != current_value:
                    item.setText(1, new_value)
                    self.update_cbor_data(item, new_value, value_type)
                    self.status_bar.showMessage("Value updated.", 5000)

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
    try:
        cbor_data = cbor2.loads(dump_data)
        return cbor_data
    except Exception as e:
        print(f"Error parsing CBOR data: {e}")
        return None

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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = CBORViewerApp()
    viewer.show()
    sys.exit(app.exec_())
