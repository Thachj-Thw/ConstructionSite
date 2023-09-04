import os
from PyQt5.QtWidgets import QLineEdit, QFileDialog, QPushButton
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDragEnterEvent, QDragMoveEvent, QDropEvent

class lineEditPathDragDrop(QLineEdit):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.button = None
        self.filter = ""
        self.caption = "Choose a directory"

    def setCaption(self, caption: str) -> None:
        self.caption = caption

    def setFilter(self, _filter: str) -> None:
        self.filter = _filter
        if self.filter:
            self.caption = "Choose a file"

    def setButton(self, button: QPushButton) -> None:
        self.button = button
        self.button.clicked.connect(self._on_btn_clicked)

    def _on_btn_clicked(self) -> None:
        if self.filter:
            path = QFileDialog.getOpenFileName(self, self.caption, "", self.filter)[0]
        else:
            path = QFileDialog.getExistingDirectory(self, self.caption, "")
        if path:
            self.setText(path)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.CopyAction)
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        if event.mimeData().hasUrls():
            if url := event.mimeData().urls():
                if url[0].isLocalFile():
                    f = url[0].toLocalFile()
                    if self.filter:
                        if os.path.isfile(f) and os.path.splitext(f)[1] in self.filter:
                            event.setDropAction(Qt.CopyAction)
                            return event.accept()
                    else:
                        if os.path.isdir(f):
                            event.setDropAction(Qt.CopyAction)
                            return event.accept()
        event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.CopyAction)
            event.accept()
            self.setText(event.mimeData().urls()[0].toLocalFile())
        else:
            event.ignore()

