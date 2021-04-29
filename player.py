import sys
from PySide2.QtGui import QColor, QPainter
from PySide2.QtCore import QEvent, QRect, Qt, Signal
from PySide2.QtWidgets import QFrame, QLineEdit, QSizeGrip, QSlider, QStyle, QVBoxLayout, QWidget, QPushButton, QHBoxLayout, QApplication


import vlc

class Controller(QWidget):
    closed = Signal()
    play = Signal()
    pause = Signal()
    stop = Signal()

    def __init__(self, parent=None):
        super(Controller, self).__init__(parent)

        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.fillColor = QColor(0, 0, 0, 2)
        self.penColor = QColor("#333333")

        self.popup_fillColor = QColor(240, 240, 240, 255)
        self.popup_penColor = QColor(200, 200, 200, 255)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)

        self.closeLayout = QHBoxLayout()
        self.closeLayout.addStretch()
        self.closeBtn = QPushButton("x", self)
        self.closeBtn.setFixedSize(30,30)
        self.closeLayout.addWidget(self.closeBtn)
        # self.closeBtn.setStyleSheet("background-color : rgba(0,0,0,0); color : white;")
        self.closeBtn.clicked.connect(self._onclose)

        self.playLayout = QHBoxLayout()
        self.playLayout.addStretch()
        self.playBtn = QPushButton("P", self)
        self.playLayout.addWidget(self.playBtn)
        self.playLayout.addStretch()
        # self.playBtn.setStyleSheet("background-color : rgba(0,0,0,0); color : white;")
        self.playBtn.setFixedSize(100,100)
        # self.playBtn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.playBtn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))

        self.timeLayout = QHBoxLayout(self)
        self.startTime = QLineEdit(self)
        self.endTime = QLineEdit(self)
        self.slider = QSlider(Qt.Horizontal, self)
        for w in (self.startTime, self.slider, self.endTime):
            self.timeLayout.addWidget(w)
        
        layout.addLayout(self.closeLayout)
        layout.addStretch()
        layout.addLayout(self.playLayout)
        layout.addStretch()
        layout.addLayout(self.timeLayout)
        self.toggleVisibility(False)

    def paintEvent(self, event):
        s = self.size()
        qp = QPainter()
        qp.begin(self)
        qp.setRenderHint(QPainter.Antialiasing, True)
        qp.setPen(self.penColor)
        qp.setBrush(self.fillColor)
        qp.drawRect(0, 0, s.width(), s.height())

        qp.end()

    def toggleVisibility(self, visible=True):
        p = self.parent()
        self.move(p.pos().x()+5, p.pos().y()+5)
        self.resize(p.width()-10, p.height()-10)
        for w in (self.closeBtn, self.playBtn, self.startTime, self.endTime, self.slider):
            if visible:
                w.show()
            else:
                w.hide()

    def event(self, event):
        print(event.type())
        if event.type() == QEvent.Type.Enter:
            self.toggleVisibility(True)
        elif event.type() == QEvent.Type.Leave:
            self.toggleVisibility(False)

        return super(Controller, self).event(event)

    def mousePressEvent(self, event):
        print("Click")
        self.startPos = event.pos()
        return super(Controller, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        print (event.pos())
        delta = event.pos()-self.startPos
        p = self.parent()
        self.move(self.pos()+delta)
        p.move(p.pos()+delta)
        return super(Controller, self).mouseMoveEvent(event)

    def _onclose(self):
        print("Close")
        self.closed.emit()


class SideGrip(QWidget):
    def __init__(self, parent, edge):
        QWidget.__init__(self, parent)
        if edge == Qt.LeftEdge:
            self.setCursor(Qt.SizeHorCursor)
            self.resizeFunc = self.resizeLeft
        elif edge == Qt.TopEdge:
            self.setCursor(Qt.SizeVerCursor)
            self.resizeFunc = self.resizeTop
        elif edge == Qt.RightEdge:
            self.setCursor(Qt.SizeHorCursor)
            self.resizeFunc = self.resizeRight
        else:
            self.setCursor(Qt.SizeVerCursor)
            self.resizeFunc = self.resizeBottom
        self.mousePos = None

    def resizeLeft(self, delta):
        window = self.window()
        width = max(window.minimumWidth(), window.width() - delta.x())
        geo = window.geometry()
        geo.setLeft(geo.right() - width)
        window.setGeometry(geo)

    def resizeTop(self, delta):
        window = self.window()
        height = max(window.minimumHeight(), window.height() - delta.y())
        geo = window.geometry()
        geo.setTop(geo.bottom() - height)
        window.setGeometry(geo)

    def resizeRight(self, delta):
        window = self.window()
        width = max(window.minimumWidth(), window.width() + delta.x())
        window.resize(width, window.height())

    def resizeBottom(self, delta):
        window = self.window()
        height = max(window.minimumHeight(), window.height() + delta.y())
        window.resize(window.width(), height)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.mousePos = event.pos()

    def mouseMoveEvent(self, event):
        if self.mousePos is not None:
            delta = event.pos() - self.mousePos
            self.resizeFunc(delta)

    def mouseReleaseEvent(self, event):
        self.mousePos = None

class VideoPlayer(QWidget):
    def __init__(self, parent=None):
        super(VideoPlayer, self).__init__(parent)

        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setObjectName("Master")
        self.setStyleSheet("#Master {background-color : white;}")

        self._gripSize = 2
        self.sideGrips = [
            SideGrip(self, Qt.LeftEdge), 
            SideGrip(self, Qt.TopEdge), 
            SideGrip(self, Qt.RightEdge), 
            SideGrip(self, Qt.BottomEdge), 
        ]
        self.cornerGrips = [QSizeGrip(self) for i in range(4)]

        self.mediaContainer = QFrame()
        self.mediaContainer.setAttribute(Qt.WA_TranslucentBackground, False)
        self.mediaContainer.setObjectName("Video")
        self.vlc = vlc.Instance()
        self.mediaplayer = self.vlc.media_player_new()
        self.mediaplayer.set_hwnd(int(self.mediaContainer.winId()))

        hbox = QVBoxLayout(self)
        hbox.setContentsMargins(2,2,2,2)
        hbox.addWidget(self.mediaContainer)
        # hbox.addWidget(self._popup)
        # hbox.addWidget(self._close)
        self.setLayout(hbox)

        self._popframe = None
        self._popflag = False

        self.playVideo(r"C:\Users\Public\Videos\Sample Videos\Wildlife.wmv")

    def show(self):
        super(VideoPlayer, self).show()
        self._onpopup()

    @property
    def gripSize(self):
        return self._gripSize

    def setGripSize(self, size):
        if size == self._gripSize:
            return
        self._gripSize = max(2, size)
        self.updateGrips()

    def updateGrips(self):
        self.setContentsMargins(*[self.gripSize] * 4)

        outRect = self.rect()
        # an "inner" rect used for reference to set the geometries of size grips
        inRect = outRect.adjusted(self.gripSize, self.gripSize,
            -self.gripSize, -self.gripSize)

        # top left
        self.cornerGrips[0].setGeometry(
            QRect(outRect.topLeft(), inRect.topLeft()))
        # top right
        self.cornerGrips[1].setGeometry(
            QRect(outRect.topRight(), inRect.topRight()).normalized())
        # bottom right
        self.cornerGrips[2].setGeometry(
            QRect(inRect.bottomRight(), outRect.bottomRight()))
        # bottom left
        self.cornerGrips[3].setGeometry(
            QRect(outRect.bottomLeft(), inRect.bottomLeft()).normalized())

        # left edge
        self.sideGrips[0].setGeometry(
            0, inRect.top(), self.gripSize, inRect.height())
        # top edge
        self.sideGrips[1].setGeometry(
            inRect.left(), 0, inRect.width(), self.gripSize)
        # right edge
        self.sideGrips[2].setGeometry(
            inRect.left() + inRect.width(), 
            inRect.top(), self.gripSize, inRect.height())
        # bottom edge
        self.sideGrips[3].setGeometry(
            self.gripSize, inRect.top() + inRect.height(), 
            inRect.width(), self.gripSize)

    def resizeEvent(self, event):
        self.updateGrips()
        if self._popflag:
            pos = self.pos()
            self._popframe.move(pos.x()+5, pos.y()+5)
            self._popframe.resize(self.width()-10, self.height()-10)

    def _onpopup(self):
        pos = self.pos()
        self._popframe = Controller(self)
        self._popframe.move(pos.x()+5, pos.y()+5)
        self._popframe.resize(self.width()-10, self.height()-10)
        self._popframe.closed.connect(self._closepopup)
        self._popflag = True
        self._popframe.show()

    def _closepopup(self):
        self._popframe.close()
        self._popflag = False
        self.close()

    def playVideo(self, path):
        self.media = self.vlc.media_new(path)
        self.media.parse()
        print(self.media.get_meta(1))
        self.mediaplayer.set_media(self.media)
        self.mediaplayer.play()
        print("FPS:", self.mediaplayer.get_fps())
        print("Rate:", self.mediaplayer.get_rate())


if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    main = VideoPlayer()
    main.resize(500, 500)
    main.show()
    sys.exit(app.exec_())