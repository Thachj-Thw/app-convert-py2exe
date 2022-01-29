from PyQt5.QtWidgets import (QLineEdit, QListWidget, QListWidgetItem, QMainWindow, QFrame, QPushButton,
                             QGraphicsDropShadowEffect, QSizeGrip, QDialog)
from PyQt5.QtGui import QDragEnterEvent, QDragMoveEvent, QDropEvent, QColor
from PyQt5.QtCore import Qt, QUrl, QPoint, pyqtSignal
import os

DIR = 0
FILE = 1


class DropLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.mode = DIR
        self.types = tuple()

    def set_types(self, mode, types=tuple()):
        self.mode = mode
        self.types = types

    def set_placeholder_text(self, b: bool):
        if b:
            txt = ""
            for t in self.types:
                txt += " " + t
            self.setPlaceholderText(txt)
        else:
            self.setPlaceholderText("")

    def dragEnterEvent(self, e: QDragEnterEvent) -> None:
        if e.mimeData().hasUrls():
            e.accept()
        else:
            e.ignore()

    def dragMoveEvent(self, e: QDragMoveEvent) -> None:
        if e.mimeData().hasUrls():
            e.setDropAction(Qt.CopyAction)
            e.accept()
        else:
            e.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.CopyAction)
            event.accept()
            url = event.mimeData().urls()[0]
            if url.isLocalFile():
                path = url.toLocalFile()
                if self.mode and os.path.isfile(path):
                    if os.path.splitext(path)[1] in self.types[1:]:
                        self.setText(path)
                else:
                    self.setText(path)
        else:
            event.ignore()


class ListWidgetMoveItem(QListWidget):
    _drag_info = []

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragDropMode(self.DragDrop)

    def startDrag(self, actions):
        self._drag_info[:] = [self]
        for item in self.selectedItems():
            self._drag_info.append(self.row(item))
        super().startDrag(actions)

    def dropEvent(self, event: QDropEvent) -> None:
        if self._drag_info:
            event.setDropAction(Qt.CopyAction)
            for row in self._drag_info[::-1][:-1]:
                self._drag_info[0].takeItem(row)
            super().dropEvent(event)


class TitleBar(QMainWindow):

    def maximize_restore(self):
        btn = self.findChild(QPushButton, "pushButton_max")
        if btn.isChecked():
            self.showMaximized()
            self.findChild(QFrame, "main").setStyleSheet("QFrame#main{background: #121212;border-radius: 0px}")
            btn.setToolTip("Restore")
        else:
            self.showNormal()
            self.resize(self.width() + 1, self.height() + 1)
            self.findChild(QFrame, "main").setStyleSheet("QFrame#main{background: #121212;border-radius: 5px}")
            btn.setToolTip("Maximize")

    def ui_definitions(self):
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(20)
        self.shadow.setXOffset(0)
        self.shadow.setYOffset(0)
        self.shadow.setColor(QColor(0, 0, 0, 100))
        self.findChild(QFrame, "main").setGraphicsEffect(self.shadow)
        self.findChild(QPushButton, "pushButton_max").clicked.connect(lambda: TitleBar.maximize_restore(self))

        def move_window(event):
            if event.buttons() == Qt.LeftButton:
                btn = self.findChild(QPushButton, "pushButton_max")
                if btn.isChecked():
                    btn.setChecked(False)
                    ratio = event.x() / self.width()
                    TitleBar.maximize_restore(self)
                    x = min(ratio * self.width(), self.width() - 80)
                    self.move(event.globalPos() - QPoint(x, event.y()))
                self.move(self.pos() + event.globalPos() - self.drag_pos)
                self.drag_pos = event.globalPos()
                event.accept()

        self.findChild(QFrame, "title").mouseMoveEvent = move_window
        QSizeGrip(self.findChild(QFrame, "size_grip"))

    def update_pos(self, event):
        self.drag_pos = event.globalPos()


class TitleBarDialog(QDialog):

    def ui_definitions(self):
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(20)
        self.shadow.setXOffset(0)
        self.shadow.setYOffset(0)
        self.shadow.setColor(QColor(0, 0, 0, 100))
        self.findChild(QFrame, "main").setGraphicsEffect(self.shadow)

        def move_window(event):
            if event.buttons() == Qt.LeftButton:
                self.move(self.pos() + event.globalPos() - self.drag_pos)
                self.drag_pos = event.globalPos()
                event.accept()

        self.findChild(QFrame, "title").mouseMoveEvent = move_window
        if size_grip := self.findChild(QFrame, "size_grip"):
            QSizeGrip(size_grip)

    def update_pos(self, event):
        self.drag_pos = event.globalPos()
