# Model selection dialog for SheetGuard

from PySide6.QtWidgets import QDialog, QListWidget, QPushButton, QVBoxLayout, QMessageBox
from PySide6.QtCore import Qt

class ModelSelectDialog(QDialog):
    """Simple dialog that lets the user pick an LLM model.

    The dialog presents a list of predefined model names. When the user
    clicks **OK**, the selected model name is returned via the ``selected``
    attribute. If the user cancels, ``selected`` remains ``None``.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Model")
        self.setModal(True)
        self.resize(300, 250)
        self.selected = None

        # Pre‑defined models – extend as needed.
        self.models = [
            "ChatGPT (GPT‑4o)",
            "Claude (Sonnet)",
            "Gemini (1.5 Flash)",
            "Llama 3.2 (8B)",
        ]

        self.list_widget = QListWidget(self)
        self.list_widget.addItems(self.models)
        self.list_widget.setCurrentRow(0)

        self.btn_ok = QPushButton("OK", self)
        self.btn_ok.clicked.connect(self._accept)
        self.btn_cancel = QPushButton("Cancel", self)
        self.btn_cancel.clicked.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(self.list_widget)
        layout.addWidget(self.btn_ok)
        layout.addWidget(self.btn_cancel)
        self.setLayout(layout)

    def _accept(self):
        current = self.list_widget.currentItem()
        if current:
            self.selected = current.text()
        self.accept()
