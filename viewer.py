import sys
import os
import platform
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSlot, Qt, QProcess
from PyQt5.QtWidgets import QPushButton, QLabel, QFileDialog, QProgressDialog
from PyQt5.QtGui import QPixmap

# full path to image editor
application = '/Applications/GIMP-2.10.app'


class FlowLayout(QtWidgets.QLayout):
    def __init__(self, parent=None, margin=-1, hspacing=-1, vspacing=-1):
        super(FlowLayout, self).__init__(parent)
        self._hspacing = hspacing
        self._vspacing = vspacing
        self._items = []
        self.setContentsMargins(margin, margin, margin, margin)

    def __del__(self):
        del self._items[:]

    def addItem(self, item):
        self._items.append(item)

    def horizontalSpacing(self):
        if self._hspacing >= 0:
            return self._hspacing
        else:
            return self.smartSpacing(
                QtWidgets.QStyle.PM_LayoutHorizontalSpacing)

    def verticalSpacing(self):
        if self._vspacing >= 0:
            return self._vspacing
        else:
            return self.smartSpacing(
                QtWidgets.QStyle.PM_LayoutVerticalSpacing)

    def count(self):
        return len(self._items)

    def itemAt(self, index):
        if 0 <= index < len(self._items):
            return self._items[index]

    def takeAt(self, index):
        if 0 <= index < len(self._items):
            return self._items.pop(index)

    def expandingDirections(self):
        return QtCore.Qt.Orientations(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self.doLayout(QtCore.QRect(0, 0, width, 0), True)

    def setGeometry(self, rect):
        super(FlowLayout, self).setGeometry(rect)
        self.doLayout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QtCore.QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
        left, top, right, bottom = self.getContentsMargins()
        size += QtCore.QSize(left + right, top + bottom)
        return size

    def doLayout(self, rect, testonly):
        left, top, right, bottom = self.getContentsMargins()
        effective = rect.adjusted(+left, +top +30, -right, -bottom)
        x = effective.x()
        y = effective.y()
        lineheight = 0
        for item in self._items:
            widget = item.widget()
            hspace = self.horizontalSpacing()
            if hspace == -1:
                hspace = widget.style().layoutSpacing(
                    QtWidgets.QSizePolicy.PushButton,
                    QtWidgets.QSizePolicy.PushButton, QtCore.Qt.Horizontal)
            vspace = self.verticalSpacing()
            if vspace == -1:
                vspace = widget.style().layoutSpacing(
                    QtWidgets.QSizePolicy.PushButton,
                    QtWidgets.QSizePolicy.PushButton, QtCore.Qt.Vertical)
            nextX = x + item.sizeHint().width() + hspace
            if nextX - hspace > effective.right() and lineheight > 0:
                x = effective.x()
                y = y + lineheight + vspace
                nextX = x + item.sizeHint().width() + hspace
                lineheight = 0
            if not testonly:
                item.setGeometry(
                    QtCore.QRect(QtCore.QPoint(x, y), item.sizeHint()))
            x = nextX
            lineheight = max(lineheight, item.sizeHint().height())
        return y + lineheight - rect.y() + bottom

    def smartSpacing(self, pm):
        parent = self.parent()
        if parent is None:
            return -1
        elif parent.isWidgetType():
            return parent.style().pixelMetric(pm, None, parent)
        else:
            return parent.spacing()

class Bubble(QtWidgets.QLabel):
    def __init__(self, text):
        super(Bubble, self).__init__(text)
        self.word = text
        self.setContentsMargins(5, 5, 5, 5)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
        painter.drawRoundedRect(
            0, 0, self.width() - 1, self.height() - 1, 5, 5)
        super(Bubble, self).paintEvent(event)

class ImageButton(QtWidgets.QLabel):
    def __init__(self, name, location):
        super().__init__()
        self.name = name
        self.location = location
        if platform.system() == 'Windows':
            slash = '\\'
        else:
            slash = '/'
        pixmap = QPixmap(location + slash + name)
        smaller_pixmap = pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.FastTransformation)
        self.setPixmap(smaller_pixmap)
        self.setScaledContents(True)
        self.resize(100, 100)
        self.setMouseTracking(True)
        self.enlarge = False
        self.setToolTip(name)

    def mousePressEvent(self, event):
        if platform.system() == 'Windows':
            slash = '\\'
        else:
            slash = '/'
        pixmap = QPixmap(self.location + slash + self.name)
        self.enlarge = not self.enlarge
        if self.enlarge:
            s_pixmap = pixmap.scaled(500, 500, Qt.KeepAspectRatio, Qt.FastTransformation)
        else:
            s_pixmap = pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.FastTransformation)
        self.setPixmap(s_pixmap)

    def mouseDoubleClickEvent(self, event):
        self.p = QProcess()
        self.p.start(application, [self.location + '/' + self.name])

    def mouseMoveEvent(self, event):
        global Mouse_X
        global Mouse_Y
        # print(event.type())
        try:
            Mouse_X = event.x()
            Mouse_Y = event.y()
            # print("mouse X,Y: {},{}" .format(Mouse_X, Mouse_Y))
        except Exception as msg:
            logging.error('Error Update_work: ' + str(msg))


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, text, parent=None):
        global application
        super(MainWindow, self).__init__(parent)
        self.mainArea = QtWidgets.QScrollArea(self)
        self.mainArea.setWidgetResizable(True)

        self.button = QPushButton('Open Directory', self)
        self.button.setToolTip('Directory to browse images')
        self.button.resize(150, self.button.height())
        self.button.move(0, 0)
        self.button.clicked.connect(self.on_click)

        widget = QtWidgets.QWidget(self.mainArea)
        widget.setMinimumWidth(100)
        self.layout = FlowLayout(widget)
        MainWindow.resize(self, 800, 600)

        self.mainArea.move(0, self.button.height())
        self.mainArea.resize(self.mainArea.width(), self.mainArea.height() - self.button.height())

        self.clear = QPushButton('Clear', self)
        self.clear.setToolTip('Clear images')
        self.clear.resize(150, self.clear.height())
        self.clear.move(self.button.width(), 0)
        self.clear.clicked.connect(self.clear_click)

        # self.words = []

        # for word in text.split():
        #    label = Bubble(word)
        #    label.setFont(QtGui.QFont('SblHebrew', 18))
        #    label.setFixedWidth(label.sizeHint().width())
        #    self.words.append(label)
        #    layout.addWidget(label)

        self.mainArea.setWidget(widget)
        self.setCentralWidget(self.mainArea)

    @pyqtSlot()
    def clear_click(self):
        self.layout.removeWidget(self.mainArea)
        self.layout.removeWidget(self.button)
        self.layout.removeWidget(self.clear)

        self.mainArea.deleteLater()
        self.button.deleteLater()
        self.clear.deleteLater()

        self.mainArea = None
        self.button = None
        self.clear = None

        self.mainArea = QtWidgets.QScrollArea(self)
        self.mainArea.setWidgetResizable(True)

        widget = QtWidgets.QWidget(self.mainArea)
        widget.setMinimumWidth(100)
        self.layout = FlowLayout(widget)

        self.mainArea.setWidget(widget)

        self.button = QPushButton('Open Directory', self)
        self.button.setToolTip('Directory to browse images')
        self.button.resize(150, self.button.height())
        self.button.move(0, 0)
        self.button.clicked.connect(self.on_click)
        self.button.show()

        self.clear = QPushButton('Clear', self)
        self.clear.setToolTip('Clear images')
        self.clear.resize(150, self.clear.height())
        self.clear.move(self.button.width(), 0)
        self.clear.clicked.connect(self.clear_click)
        self.clear.show()

        # self.setCentralWidget(self.mainArea)

        self.update()

    @pyqtSlot()
    def on_click(self):
        directory = str(QFileDialog.getExistingDirectory(self, "Select Directory"))
        fileCount = 0
        curFile = 0
        if len(directory) > 0:
            for file in os.listdir(directory):
                if file.endswith(".jpg") or file.endswith(".JPG") or file.endswith('.jpeg') or file.endswith('.png') or file.endswith('.bmp'):
                    fileCount += 1
            progress = QProgressDialog('Processing images...', 'Cancel', 0, fileCount)
            progress.setWindowModality(Qt.WindowModal)
            progress.show()
            for file in os.listdir(directory):
                if progress.wasCanceled():
                    break
                if file.endswith(".jpg") or file.endswith(".JPG") or file.endswith('.jpeg') or file.endswith('.png') or file.endswith('.bmp'):
                    label = ImageButton(file, directory)
                    self.layout.addWidget(label)
                curFile += 1
                progress.setValue(curFile)
        progress.hide()

        self.setCentralWidget(self.mainArea)
        self.update()

if __name__ == '__main__':

    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow('Image Viewer')
    window.show()
    sys.exit(app.exec_())