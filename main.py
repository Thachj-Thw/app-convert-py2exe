from PyQt5 import uic
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from customs import *
from PyQt5.QtCore import QThread, pyqtSignal
from imgs import icons
import subprocess
from subprocess import CREATE_NO_WINDOW, PIPE
import os
import shutil
import sys


def subprocess_args(include_stdout=True):
    if hasattr(subprocess, 'STARTUPINFO'):
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        env = os.environ
    else:
        si = None
        env = None

    if include_stdout:
        ret = {'stdout': subprocess.PIPE}
    else:
        ret = {}

    ret.update({'stdin': subprocess.PIPE,
                'stderr': subprocess.PIPE,
                'startupinfo': si,
                'env': env})
    return ret


DIR = os.path.normpath(os.path.dirname(__file__))
ERROR = 0
WARNING = 1
QUESTION = 2


class Setting(QDialog):
    _data = [0, '']

    def __init__(self):
        super().__init__()
        uic.loadUi(os.path.join(DIR, "ui", "setting.ui"), self)
        self.setWindowTitle("Setting Source")
        icon = QIcon()
        icon.addPixmap(QPixmap(os.path.join(DIR, "imgs", "ico", "icon.ico")))
        self.setWindowIcon(icon)
        self.venv = self.findChild(QRadioButton, "radioButton_venv")
        self.path = self.findChild(DropLineEdit, "lineEdit_path")
        self.path.set_types(0, ("Virtual Environments directory", ))
        self.change_path = self.findChild(QToolButton, "toolButton_path")
        self.change_path.clicked.connect(self.open_filedialog)
        if self._data[0]:
            self.venv.setChecked(True)
        TitleBarDialog.ui_definitions(self)
        self.path.setText(self._data[1])
        self.setModal(True)
        self.show()
        self.c = self.exec_()

    def mousePressEvent(self, event):
        TitleBarDialog.update_pos(self, event)

    def open_filedialog(self):
        if path := QFileDialog.getExistingDirectory(self, "Choose a Virtual Environments directory"):
            self.path.setText(path)

    def get(self):
        if self.c == QDialog.Accepted:
            self._data[1] = self.path.text()
            if self._data[1] and self.venv.isChecked():
                self._data[0] = 1
                return self._data[1]
            self._data[0] = 0
            return "PATH"


class Icon(QDialog):
    _data = [0, '']

    def __init__(self):
        super().__init__()
        uic.loadUi(os.path.join(DIR, "ui", "icon.ui"), self)
        self.setWindowTitle("Setting Icon")
        icon = QIcon()
        icon.addPixmap(QPixmap(os.path.join(DIR, "imgs", "ico", "icon.ico")))
        self.setWindowIcon(icon)
        self.none = self.findChild(QRadioButton, "radioButton_none")
        self.option = self.findChild(QRadioButton, "radioButton_option")
        self.path = self.findChild(DropLineEdit, "lineEdit_path")
        self.change_path = self.findChild(QToolButton, "toolButton_path")
        self.change_path.clicked.connect(self.open_filedialog)
        self.path.set_types(1, ("Icon file", ".ico"))
        if self._data[0] == 1:
            self.none.setChecked(True)
        elif self._data[0] == 2:
            self.option.setChecked(True)
        self.path.setText(self._data[1])
        TitleBarDialog.ui_definitions(self)
        self.setModal(True)
        self.show()
        self.exc = self.exec_()

    def mousePressEvent(self, event):
        TitleBarDialog.update_pos(self, event)

    def open_filedialog(self):
        directory = os.path.dirname(self.path.text()) if self.path.text() else ""
        if path := QFileDialog.getOpenFileName(self, "Choose an icon file", directory, "Icon File (*.ico)"):
            self.path.setText(path[0])

    def get(self):
        self._data[1] = self.path.text()
        if self.exc == QDialog.Accepted:
            if self.none.isChecked():
                self._data[0] = 1
            elif self.option.isChecked():
                if self._data[1]:
                    self._data[0] = 2
            else:
                self._data[0] = 0
        if self._data[0] == 1:
            return "NONE"
        if self._data[0] == 2:
            return self._data[1]


class Message(QDialog):
    def __init__(self, mode, message):
        super(Message, self).__init__()
        icon = QIcon()
        icon.addPixmap(QPixmap(os.path.join(DIR, "imgs", "ico", "icon.ico")))
        self.setWindowIcon(icon)
        if mode == ERROR:
            uic.loadUi(os.path.join(DIR, "ui", "error.ui"), self)
            self.setWindowTitle("Error")
        elif mode == WARNING:
            uic.loadUi(os.path.join(DIR, "ui", "warning.ui"), self)
            self.setWindowTitle("Warning")
        else:
            uic.loadUi(os.path.join(DIR, "ui", "question.ui"), self)
            self.setWindowTitle("Question")
        self.mess = self.findChild(QLabel, "label_mess")
        self.mess.setText(message)
        TitleBarDialog.ui_definitions(self)
        self.setModal(True)
        self.show()
        self.exc = self.exec_()

    def mousePressEvent(self, event):
        TitleBarDialog.update_pos(self, event)

    def get(self):
        return self.exc == QDialog.Accepted


class WorkerConvert(QThread):
    finish = pyqtSignal(str)
    successfully = pyqtSignal(bool, str)

    def __init__(self, cmd: str):
        super().__init__()
        self.cmd = cmd

    def run(self):
        p = subprocess.Popen(self.cmd, creationflags=CREATE_NO_WINDOW, **subprocess_args())
        info = ""
        for e in p.stderr:
            info = e.decode()[:-2]
            self.finish.emit(info)
        err = p.wait()
        self.successfully.emit(err, info)


class Main(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi(os.path.join(DIR, "ui", "base.ui"), self)
        self.setWindowTitle("Convert py to exe")
        icon = QIcon()
        icon.addPixmap(QPixmap(os.path.join(DIR, "imgs", "ico", "icon.ico")))
        self.setWindowIcon(icon)
        self.venv_path, self.icon_path = None, None
        self.input_path, self.output_path = None, None
        self.thread_convert = None
        self.name, self.script = "", ""
        self.pixmap_console = QPixmap(os.path.join(DIR, "imgs", "ico", "console.ico"))
        self.pixmap_windowed = QPixmap(os.path.join(DIR, "imgs", "ico", "windowed.ico"))
        self.line_edit_name = self.findChild(QLineEdit, "lineEdit_name")
        self.line_edit_input = self.findChild(DropLineEdit, "lineEdit_path_input")
        self.line_edit_input.textChanged.connect(self.on_path_changed)
        self.findChild(QToolButton, "toolButton_path_input").clicked.connect(self.on_change_input)
        self.line_edit_output = self.findChild(DropLineEdit, "lineEdit_path_output")
        self.findChild(QToolButton, "toolButton_path_output").clicked.connect(self.on_change_output)
        self.findChild(QPushButton, "button_setting").clicked.connect(self.open_setting)
        self.checkbox_one_file = self.findChild(QCheckBox, "checkBox_oneFile")
        self.checkbox_no_console = self.findChild(QCheckBox, "checkBox_noConsole")
        self.checkbox_no_console.toggled.connect(self.on_no_console_toggled)
        self.checkbox_admin = self.findChild(QCheckBox, "checkBox_admin")
        self.button_icon = self.findChild(QPushButton, "pushButton_icon")
        self.button_icon.clicked.connect(self.open_icon)
        self.list_widget_all_file = self.findChild(ListWidgetMoveItem, "listWidget_all")
        self.list_widget_file_add = self.findChild(ListWidgetMoveItem, "listWidget_add")
        self.findChild(QPushButton, "pushButton_add").clicked.connect(self.on_add)
        self.findChild(QPushButton, "pushButton_remove").clicked.connect(self.on_remove)
        self.button_convert = self.findChild(QPushButton, "pushButton_convert")
        self.console = self.findChild(QTextEdit, "textEdit_console")
        self.version = self.findChild(QLabel, "label_version")
        self.button_convert.clicked.connect(self.on_convert)
        self.update_version()
        TitleBar.ui_definitions(self)
        self.show()

    def mousePressEvent(self, event: QMouseEvent):
        TitleBar.update_pos(self, event)

    def open_setting(self):
        if path := Setting().get():
            if path == "PATH":
                self.venv_path = None
            else:
                self.venv_path = os.path.normpath(path)
            self.update_version()

    def update_version(self):
        pythonw = "pythonw"
        if self.venv_path:
            pythonw = os.path.join(self.venv_path, "scripts", "pythonw.exe")
        p = subprocess.Popen([pythonw, os.path.join(DIR, "module", "version.pyw")],
                             creationflags=CREATE_NO_WINDOW,
                             **subprocess_args())
        v = p.communicate()[0]
        if v:
            self.version.setText("PyInstaller Version: " + v.decode()[:-2])
            self.version.setEnabled(True)
        else:
            self.version.setText("PyInstaller Version not found!")
            self.version.setDisabled(True)

    def on_change_input(self):
        if path := QFileDialog.getOpenFileName(self, "Choose a python file",
                                               filter="Python File (*.py *.pyw);;All File (*.*)")[0]:
            self.line_edit_input.setText(path)
            file = os.path.splitext(os.path.basename(path))
            if not self.line_edit_output.text():
                self.line_edit_output.setText(os.path.dirname(path))
            if not self.line_edit_name.text():
                self.line_edit_name.setText(file[0])
            if file[1] == ".pyw":
                self.checkbox_no_console.setChecked(True)
                self.checkbox_no_console.setDisabled(True)
            else:
                self.checkbox_no_console.setDisabled(False)
            self.list_widget_all_file.clear()
            self.list_widget_file_add.clear()
            self.list_widget_all_file.addItems(os.listdir(os.path.dirname(path)))

    def on_path_changed(self, path):
        if os.path.isfile(path):
            file = os.path.splitext(os.path.basename(path))
            if not self.line_edit_output.text():
                self.line_edit_output.setText(os.path.dirname(path))
            if not self.line_edit_name.text():
                self.line_edit_name.setText(file[0])
            if file[1] == ".pyw":
                self.checkbox_no_console.setChecked(True)
                self.checkbox_no_console.setDisabled(True)
            else:
                self.checkbox_no_console.setDisabled(False)
            self.list_widget_all_file.clear()
            self.list_widget_file_add.clear()
            self.list_widget_all_file.addItems(os.listdir(os.path.dirname(path)))

    def on_change_output(self):
        current_path = self.line_edit_output.text()
        directory = current_path if current_path else ""
        if path := QFileDialog.getExistingDirectory(self, "Choose a folder output", directory):
            self.line_edit_output.setText(path)

    def open_icon(self):
        self.icon_path = Icon().get()
        if self.icon_path == "NONE":
            self.button_icon.setText("NONE")
            self.button_icon.setIcon(QIcon())
        else:
            self.button_icon.setText("")
            icon = QIcon()
            if self.icon_path:
                icon.addPixmap(QPixmap(self.icon_path))
                self.button_icon.setIcon(icon)
            else:
                self.on_no_console_toggled(self.checkbox_no_console.isChecked())

    def on_no_console_toggled(self, b: bool):
        if not self.icon_path:
            icon = QIcon()
            if b:
                icon.addPixmap(self.pixmap_windowed)
            else:
                icon.addPixmap(self.pixmap_console)
            self.button_icon.setIcon(icon)

    def on_add(self):
        for item in self.list_widget_all_file.selectedItems():
            self.list_widget_file_add.addItem(self.list_widget_all_file.takeItem(self.list_widget_all_file.row(item)))

    def on_remove(self):
        for item in self.list_widget_file_add.selectedItems():
            self.list_widget_all_file.addItem(self.list_widget_file_add.takeItem(self.list_widget_file_add.row(item)))

    def on_convert(self):
        if not self.version.isEnabled():
            self.button_convert.setEnabled(True)
            return Message(mode=ERROR, message="PyInstaller not found")
        self.name = self.line_edit_name.text()
        if not self.name:
            self.button_convert.setEnabled(True)
            return Message(mode=WARNING, message="Name must not be empty")
        if not self.line_edit_input.text():
            self.button_convert.setEnabled(True)
            return Message(mode=WARNING, message="Input file must not be empty")
        else:
            self.script = os.path.normpath(self.line_edit_input.text())
        if not self.line_edit_output.text():
            self.button_convert.setEnabled(True)
            return Message(mode=WARNING, message="Output folder must not be empty")
        else:
            dist = os.path.normpath(self.line_edit_output.text())
        icon = self.icon_path if self.icon_path is None or self.icon_path == "NONE" else os.path.normpath(self.icon_path)
        options = []
        if self.checkbox_one_file.isChecked():
            options.append("--onefile")
        if self.checkbox_no_console.isChecked():
            options.append("--noconsole")
        if self.checkbox_admin.isChecked():
            options.append("--uac-admin")
        data = [self.list_widget_file_add.item(i).text() for i in range(self.list_widget_file_add.count())]
        self.console.clear()
        converter = os.path.join(self.venv_path, "scripts", "pyinstaller.exe") if self.venv_path else "pyinstaller"
        command = f'"{converter}" --clean --name="{self.name}" --workpath "{os.path.join(DIR, "build")}" ' \
                  f'--distpath "{dist}" --specpath "{os.path.dirname(self.script)}" '
        if icon:
            command += f'--icon="{icon}" '
        for opt in options:
            command += opt + " "
        for d in data:
            path = os.path.join(os.path.dirname(self.script), d)
            if os.path.isfile(path):
                command += f'--add-data="{path};." '
            else:
                command += f'--add-data="{path};{d}" '
        command += f'"{self.script}"'
        print(command)
        self.thread_convert = WorkerConvert(command)
        self.thread_convert.finish.connect(self.on_finish)
        self.thread_convert.successfully.connect(self.on_successfully)
        self.thread_convert.start()

    def on_finish(self, info):
        self.console.append(info)

    def on_successfully(self, err, info):
        pth = os.path.join(DIR, "build", self.name)
        if os.path.exists(pth):
            shutil.rmtree(pth)
        if err:
            print(info)
            return Message(mode=ERROR, message="Failed to convert\n" + info)
        else:
            if Message(mode=QUESTION, message="Convert Successfully\nDo you want to remove spec file?"):
                os.remove(os.path.join(os.path.dirname(self.script), self.name + ".spec"))
        self.button_convert.setEnabled(True)

    def closeEvent(self, event):
        if not self.button_convert.isEnabled():
            Message(mode=WARNING, message="Converting can't close the app")
            event.ignore()
        else:
            event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Main()
    sys.exit(app.exec_())
