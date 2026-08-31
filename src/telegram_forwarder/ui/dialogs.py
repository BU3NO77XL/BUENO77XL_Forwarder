from PyQt6.QtWidgets import QDialog, QLineEdit, QDialogButtonBox, QVBoxLayout, QLabel, QPushButton, QMessageBox, QHBoxLayout, QStyle, QApplication, QListWidget, QListWidgetItem
from PyQt6.QtCore import Qt
from ..core.i18n import t, get_lang

_DARK_QSS = """
QDialog { background-color: #252525; color: #e0e0e0; }
QLabel { color: #e0e0e0; background: transparent; }
QLineEdit { background-color: #333; color: white; border: 1px solid #555; border-radius: 8px; padding: 8px; }
QLineEdit:focus { border: 2px solid #4a90ff; }
QListWidget, QListView { background-color: #2b2b2b; color: #e0e0e0; border: 1px solid #444; border-radius: 8px; }
QListWidget::item:selected { background: #357abd; color: white; }
QDialogButtonBox QPushButton { min-width: 80px; }
"""

class CodeDialog(QDialog):
    def __init__(self, title="Enter Code", label="Code:", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)

        self.input = QLineEdit(self)
        self.input.setPlaceholderText(label)

        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        # Traduz OK/Cancel conforme o idioma
        self.buttons.button(QDialogButtonBox.StandardButton.Ok).setText(t('code_ok'))
        self.buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(t('code_cancel'))

        self.setStyleSheet(_DARK_QSS)
        layout = QVBoxLayout()
        layout.addWidget(self.input)
        layout.addWidget(self.buttons)
        self.setLayout(layout)

    def get_value(self):
        return self.input.text()


class AsyncMessageBox(QDialog):
    def __init__(self, title, message, icon=QMessageBox.Icon.Information, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.result = None
        self.setModal(True)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.Dialog)

        self.setStyleSheet(_DARK_QSS)
        layout = QVBoxLayout(self)

        # Left icon
        icon_label = QLabel()
        style = QApplication.style()
        if icon == QMessageBox.Icon.Critical:
            std_icon = QStyle.StandardPixmap.SP_MessageBoxCritical
        elif icon == QMessageBox.Icon.Warning:
            std_icon = QStyle.StandardPixmap.SP_MessageBoxWarning
        elif icon == QMessageBox.Icon.Question:
            std_icon = QStyle.StandardPixmap.SP_MessageBoxQuestion
        else:
            std_icon = QStyle.StandardPixmap.SP_MessageBoxInformation
        pixmap = style.standardIcon(std_icon).pixmap(48, 48)
        icon_label.setPixmap(pixmap)

        # Message text
        text_label = QLabel(message)
        text_label.setWordWrap(True)

        # Putting icons and text together
        hlayout = QHBoxLayout()
        hlayout.addWidget(icon_label)
        hlayout.addWidget(text_label)
        layout.addLayout(hlayout)

        # OK button
        btn_ok = QPushButton(t('code_ok'))
        btn_ok.clicked.connect(self.on_ok)
        btn_ok.setDefault(True)
        layout.addWidget(btn_ok, alignment=Qt.AlignmentFlag.AlignRight)

        # self.setFixedSize(400, 150)

    def on_ok(self):
        self.result = QMessageBox.StandardButton.Ok
        self.accept()

    def get_result(self):
        return self.result


class ChannelPickerDialog(QDialog):
    """Dialog com busca e lista de canais/grupos da conta para selecao rapida."""

    def __init__(self, title="Select a channel", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(520, 620)
        self.selected_value = None

        self.setStyleSheet(_DARK_QSS)
        layout = QVBoxLayout(self)

        self.search = QLineEdit(self)
        self.search.setPlaceholderText("🔍 Search channel/group...")
        self.search.textChanged.connect(self.filter_items)
        layout.addWidget(self.search)

        self.listw = QListWidget(self)
        self.listw.itemDoubleClicked.connect(lambda _item: self.accept())
        layout.addWidget(self.listw)

        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.buttons.button(QDialogButtonBox.StandardButton.Ok).setText(t('code_ok'))
        self.buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(t('code_cancel'))
        layout.addWidget(self.buttons)

        self.setLayout(layout)

    def add_item(self, label, value):
        item = QListWidgetItem(label)
        item.setData(Qt.ItemDataRole.UserRole, value)
        self.listw.addItem(item)

    def filter_items(self, text):
        text = (text or '').lower()
        for i in range(self.listw.count()):
            item = self.listw.item(i)
            item.setHidden(text not in item.text().lower())

    def get_selected(self):
        item = self.listw.currentItem()
        if item is None:
            return None
        return item.data(Qt.ItemDataRole.UserRole)
