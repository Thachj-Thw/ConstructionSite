import sys
import os
import module
from PyQt5.QtWidgets import QApplication, QMainWindow, QProgressBar, QFrame, QVBoxLayout, QMessageBox
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QCloseEvent
from PyQt5.uic import loadUi
from Cache import Cache, CacheObject
from DHConstructionSite import ConstructionSiteReport
from Widgets import lineEditPathDragDrop
import re


class Worker(QThread):

    create_one = pyqtSignal()
    end = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, file_name: str, output_dir: str, data: dict, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.file_name = file_name
        self.output_dir = output_dir
        self.data = data
    
    @staticmethod
    def format_time(inp: str) -> str:
        return "%sh%sp" % tuple(inp.split(":")) if inp else ""

    @staticmethod
    def split_data(data: str) -> (str, str, str, str, str, str, str, list, list):
        split = data.split("\n")
        if len(split) < 4:
            raise Exception("Invalid format! Must be:\ndd/mm/yyyy (ngày đi ct)\nTên công trình\nMã công trình\nhh:mm-hh:mm (giờ làm và  nghỉ sáng)\nViệc 1 sáng làm\nViệc 2 sáng làm\nhh:mm-hh:mm (giờ làm và nghỉ chiều)\nViệc 1 chiều làm\nViệc 2 chiều làm\n\n\nCác ngày cách nhau tối thiểu 2 khoảng trống")
        date = split[0]
        name = split[1]
        _id = split[2]
        if not re.search(r"[0-1][0-9]:[0-5][0-9]-[0-1][0-9]:[0-5][0-9]", split[3]):
            raise Exception("Invalid time format!\nMust be hh:mm-hh:mm")
        smo, emo = split[3].split("-")
        is_next = False
        jmo, jaf = [], []
        saf, eaf = "", ""
        for line in split[4:]:
            if t := re.search(r"[0-1][0-9]:[0-5][0-9]-[0-1][0-9]:[0-5][0-9]", line):
                saf, eaf = t.group().split("-")
                is_next = True
                continue
            if is_next:
                jaf.append(line)
            else:
                jmo.append(line)
        return date, name, _id, Worker.format_time(smo), Worker.format_time(emo), Worker.format_time(saf), Worker.format_time(eaf), jmo, jaf


    def run(self) -> None:
        try:
            report = ConstructionSiteReport(self.file_name)
            for page in self.data:
                report.add_page(*self.split_data(page))
                self.create_one.emit()
            report.save(self.output_dir)
        except PermissionError:
            self.error.emit("Permission denied! Maybe the file is open")
        except Exception as msg:
            self.error.emit(str(msg))
        else:
            self.end.emit()

    def stop(self) -> None:
        self.terminate()


class MainWindow(QMainWindow):

    document = os.path.join(os.environ['USERPROFILE'], 'Documents')
    source = module.Path(__file__).source
    app = module.Path(__file__).app
    
    def __cache__(self) -> [CacheObject]:
        return [
            CacheObject("name", self.line_name.text, self.line_name.setText, ""),
            CacheObject("input", self.line_input.text, self.line_input.setText, ""),
            CacheObject("output", self.line_output.text, self.line_output.setText, "")
        ]

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        loadUi(self.source.join("ui/main.ui"), self)
        self.line_input.setFilter("Text File (*.txt) ;; All (*.*)")
        self.line_input.setButton(self.btn_input)
        self.line_output.setButton(self.btn_output)
        self.line_output.setPlaceholderText(self.document)
        self.btn_create.clicked.connect(self._on_btn_create_clicked)
        self.__cache = Cache(self, "ConstructionSite")
        self.__cache.load()
        self._thread = None
        self.progress = None
        self.show()
    
    def create_progressbar(self) -> QProgressBar:
        self.btn_create.hide()
        if self.progress:
            self.progress.setValue(0)
            self.frame.setStyleSheet("QProgressBar {border: 1px solid white;border-radius: 3px;text-align: center;background-color: white;color: black;} QProgressBar::chunk {background-color: green;}")
            self.frame.show()
            return self.progress
        self.frame = QFrame(self.centralwidget)
        self.frame.setStyleSheet("QProgressBar {border: 1px solid white;border-radius: 3px;text-align: center;background-color: white;color: black;} QProgressBar::chunk {background-color: green;}")
        self.frame.setFrameShape(QFrame.StyledPanel)
        self.frame.setFrameShadow(QFrame.Raised)
        self.verticalLayout = QVBoxLayout(self.frame)
        self.progress = QProgressBar(self.frame)
        self.progress.setValue(0)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.addWidget(self.progress)
        self.gridLayout.addWidget(self.frame, 5, 2, 1, 1)
        return self.progress
    
    def get_input(self) -> (str, str, str):
        file_name = self.line_name.text()
        input_file = self.line_input.text()
        output_dir = self.line_output.text()
        if not output_dir:
            output_dir = self.document
        if not input_file:
            self.alert_input.setText("Input must not be empty!")
        elif not os.path.isfile(input_file):
            self.alert_input.setText("Input invalid!")
            input_file = ""
        if not os.path.isdir(output_dir):
            self.alert_output.setText("Output invalid!")
            input_file = ""
        return file_name, input_file, output_dir

    def _on_btn_create_clicked(self) -> None:
        file_name, input_file, output_dir = self.get_input()
        if not input_file:
            return
        with open(input_file, mode="r", encoding="utf-8") as f:
            self.data = re.sub(r'\n\n\n+', r'\n\n\n', f.read()).split("\n\n\n")
            if not self.data[-1]:
                self.data = self.data[:-1]
        self.create_progressbar().setMaximum(len(self.data))
        self._thread = Worker(file_name, output_dir, self.data, self)
        self._thread.create_one.connect(self._on_add_page)
        self._thread.error.connect(self._on_end_create)
        self._thread.end.connect(self._on_end_create)
        self._thread.start()

    def _on_add_page(self) -> None:
        self.progress.setValue(self.progress.value() + 1)
    
    def _on_end_create(self, msg: str = "") -> None:
        if msg:
            self.frame.setStyleSheet("QProgressBar {border: 1px solid white;border-radius: 3px;text-align: center;background-color: white;color: black;} QProgressBar::chunk {background-color: red;}")
            QMessageBox(QMessageBox.Icon.Critical, "Error", self.data[self.progress.value()]+"\n\n" + msg, QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel).exec_()
        else:
            QMessageBox(QMessageBox.Icon.Information, "Info", "Created successfully!", QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel).exec_()
        self.frame.hide()
        self.btn_create.show()
    
    def closeEvent(self, event: QCloseEvent) -> None:
        if self._thread and self._thread.isRunning():
            if QMessageBox(QMessageBox.Icon.Warning, "Warning", "App is running! Do you want to close?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No).exec_() == QMessageBox.StandardButton.No:
                return event.ignore()
            self._thread.stop()
        self.__cache.update()
        super().closeEvent(event)


if __name__ == '__main__':
    module.hide_console()
    module.alert_excepthook()
    app = QApplication(sys.argv)
    main = MainWindow()
    sys.exit(app.exec_())