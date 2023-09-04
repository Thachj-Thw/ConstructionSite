import sys
import module
from PyQt5.QtWidgets import QApplication, QMainWindow, QProgressBar, QSizePolicy, QFrame, QVBoxLayout
from PyQt5.QtCore import Qt
from PyQt5.uic import loadUi


class MainWindow(QMainWindow):

    source = module.Path(__file__).source
    app = module.Path(__file__).app

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        loadUi(self.source.join("ui/main.ui"), self)
        self.line_input.setFilter("Text File (*.txt) ;; All (*.*)")
        self.line_input.setButton(self.btn_input)
        self.line_output.setButton(self.btn_output)
        self.btn_create.clicked.connect(self._on_btn_create_clicked)
        self.show()

    def _on_btn_create_clicked(self) -> None:
        if not self.line_input.text():
            self.alert_input.setText("input must not be empty")
            return
        with open(self.line_input.text(), mode="r", encoding="utf-8") as f:
            data = f.read()
        lst_data = data.split("\n\n\n")
        self.btn_create.hide()
        self.frame = QFrame(self.centralwidget)
        self.frame.setFrameShape(QFrame.StyledPanel)
        self.frame.setFrameShadow(QFrame.Raised)
        self.verticalLayout = QVBoxLayout(self.frame)
        self.progress = QProgressBar(self.frame)
        self.progress.setValue(0)
        self.progress.setMaximum(len(lst_data))
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.addWidget(self.progress)
        self.gridLayout.addWidget(self.frame, 3, 1, 1, 1)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main = MainWindow()
    sys.exit(app.exec_())