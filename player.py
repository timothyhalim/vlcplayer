import sys
import os
from PySide2.QtGui import QColor, QFont, QPainter, QPen
from PySide2.QtCore import QEvent, QPoint, QRect, QTimer, QUrl, Qt, Signal
from PySide2.QtWidgets import QFrame, QLineEdit, QSizeGrip, QSlider, QVBoxLayout, QWidget, QHBoxLayout, QApplication

try:
    fileDir = os.path.dirname(__file__)
except:
    import inspect
    fileDir = os.path.dirname(inspect.getframeinfo(inspect.currentframe()).filename)

pyVersion = float(f"{sys.version_info[0]}.{sys.version_info[1]}")
vlcdir = os.path.normpath(os.path.join(fileDir, "vlc"))
if pyVersion >= 3.8:
    os.path.add_dll_directory(vlcdir)
else:
    if not vlcdir in sys.path:
        sys.path.append(vlcdir)
    os.environ['PYTHON_VLC_MODULE_PATH'] = vlcdir
    os.environ['PYTHON_VLC_LIB_PATH'] = os.path.normpath(os.path.join(vlcdir, "libvlc.dll"))
    os.chdir(vlcdir)
    
import vlc

from component.ButtonIcon import ButtonIcon
from component.TimeSlider import TimeSlider

class Controller(QWidget):
    def __init__(self, parent):
        super(Controller, self).__init__(parent)

        self.resourcePath = os.path.normpath(os.path.join(fileDir, "resource")).replace("\\", "/")

        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAcceptDrops(True)

        self.fillColor = QColor(127, 127, 127, 2)
        self.penColor = QColor(127, 127, 127, 2)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)

        self.vlc = self.parent().vlc
        self.mediaPlayer = self.parent().mediaPlayer

        self.drawDrag = False
        self.mediaPlaying = False

        self.setupWidget()
        self.setupSignal()
        self.initUI()

    def setupWidget(self):
        self.closeBtn = ButtonIcon(icon=f"{self.resourcePath}/cancel.svg", iconsize=15)
        self.closeLayout = QHBoxLayout()
        self.closeLayout.setContentsMargins(0,5,5,0)
        self.closeLayout.addStretch()
        self.closeLayout.addWidget(self.closeBtn)

        self.playBtn = ButtonIcon(icon=f"{self.resourcePath}/play.svg", iconsize=100)
        self.volumeSlider = QSlider(Qt.Vertical, self)
        self.volumeSlider.setMaximum(100)
        self.volumeSlider.setValue(100)
        
        self.timeSlider = TimeSlider(Qt.Horizontal, self)
        self.volumeSlider.setStyleSheet(self.timeSlider.qss())

        self.playLayout = QHBoxLayout()
        self.playLayout.addStretch()
        self.playLayout.addWidget(self.playBtn)
        self.playLayout.addStretch()
        self.playLayout.addWidget(self.volumeSlider)
        
        self.layout().addLayout(self.closeLayout)
        self.layout().addStretch()
        self.layout().addLayout(self.playLayout)
        self.layout().addStretch()
        self.layout().addWidget(self.timeSlider)

        self.timer = QTimer(self)
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.updateUI)

    def setupSignal(self):
        # Signal
        self.closeBtn.clicked.connect(self.close)
        self.playBtn.clicked.connect(self.play)
        self.volumeSlider.valueChanged.connect(self.setVolume)
        self.timeSlider.sliderMoved.connect(self.setFrame)
        self.timeSlider.sliderMoved.connect(self.setFrame)
        # self.timeSlider.sliderPressed.connect(self.hold)
        # self.timeSlider.sliderReleased.connect(self.hold)

    def initUI(self):
        # Init
        self.toggleVisibility(False)

    def paintEvent(self, event):
        s = self.size()
        qp = QPainter()
        qp.begin(self)
        qp.setRenderHint(QPainter.Antialiasing, True)
        qp.setPen(self.penColor)
        qp.setBrush(self.fillColor)
        qp.drawRect(0, 0, s.width(), s.height())

        if self.drawDrag:
            pen = QPen(Qt.white, 5)
            pen.setCapStyle(Qt.RoundCap)
            qp.setPen(pen)
            qp.setBrush(self.fillColor)

            outerWidth = s.width()-60
            outerHeight = s.height()-60

            ow = int(s.width()/2-outerWidth/2)
            oh = int(s.height()/2-outerHeight/2)
            qp.drawRoundedRect(ow, oh, outerWidth, outerHeight, 5, 5)
            
            qp.setBrush(Qt.white)
            thickness = 12
            length = 50
            roundness = thickness/2

            vS = int(s.width()/2-thickness/2)
            vE = int(s.height()/2-length/2)
            qp.drawRoundedRect(vS, vE, thickness, length, roundness, roundness)
            hS = int(s.width()/2-length/2)
            hE = int(s.height()/2-thickness/2)
            qp.drawRoundedRect(hS, hE, length, thickness, roundness, roundness)

        qp.end()

    def event(self, event):
        if event.type() == QEvent.Type.Enter:
            self.toggleVisibility(True)
        elif event.type() == QEvent.Type.Leave:
            self.toggleVisibility(False)

        return super(Controller, self).event(event)

    def mousePressEvent(self, event):
        self.startPos = event.pos()
        return super(Controller, self).mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if hasattr(self, "startPos"):
            delattr(self, "startPos")
        return super().mouseReleaseEvent(event)
    
    def mouseMoveEvent(self, event):
        if hasattr(self, "startPos"):
            delta = event.pos()-self.startPos
            p = self.parent()
            self.move(self.pos()+delta)
            p.move(p.pos()+delta)
        return super(Controller, self).mouseMoveEvent(event)

    def mouseDoubleClickEvent(self, event):
        self.setFullscreen()
        return super().mouseDoubleClickEvent(event)

    def dragEnterEvent(self, event):
        self.drawDrag = True
        self.update()
        if event.mimeData().hasUrls():
            event.accept()
        elif event.mimeData().hasText():
            event.accept()
        else:
            event.ignore()
    
    def dragLeaveEvent(self, event):
        self.drawDrag = False
        self.update()
        return super().dragLeaveEvent(event)

    def dropEvent(self, event):
        self.drawDrag = False
        self.update()
        if event.mimeData().hasUrls():
            url = event.mimeData().urls()[0].toString()
            self.mediaPlayer.stop()
            self.createMedia(url)
    
    def wheelEvent(self, event):
        increment = int(self.volumeSlider.maximum() / 10)
        if (event.angleDelta().y()) > 0 :
            self.volumeSlider.setValue(self.volumeSlider.value()+increment)
        elif (event.angleDelta().y()) < 0 :
            self.volumeSlider.setValue(self.volumeSlider.value()-increment)
        return super().wheelEvent(event)

    def close(self):
        self.parent().close()
        self.timer.stop()
        self.mediaPlayer.pause()
        return super().close()

    def toggleVisibility(self, visible=True):
        p = self.parent()
        self.move(p.pos().x()+p._gripSize, p.pos().y()+p._gripSize)
        self.resize(p.width()-(p._gripSize*2), p.height()-(p._gripSize*2))
        for w in (self.closeBtn, self.playBtn, self.volumeSlider):
            w.setVisible(visible)
        self.timeSlider.setTipVisibility(visible)
        self.timeSlider.setFixedHeight(16 if visible else 1)

    def setFullscreen(self):
        if self.parent().windowState() & Qt.WindowFullScreen:
            # QApplication.setOverrideCursor(Qt.ArrowCursor)
            self.parent().showNormal()
        else:
            self.parent().showFullScreen()
            # QApplication.setOverrideCursor(Qt.BlankCursor)
        self.parent().controllerResize()

    def updateUI(self):
        media_pos = self.mediaPlayer.get_position()
        slider_pos = int((media_pos+(0.03*media_pos)) * 1000)
        self.timeSlider.setValue(slider_pos)
        
    def playSample(self):
        self.createMedia(os.path.join(fileDir, "sample.mov"))

    def createMedia(self, path):
        self.media = self.vlc.media_new(path)
        self.media.parse()
        print(self.media.get_meta(1))
        self.mediaPlayer.set_media(self.media)
        print("FPS:", self.mediaPlayer.get_fps())
        print("Rate:", self.mediaPlayer.get_rate())
        print("Ratio:", self.mediaPlayer.video_get_width()/self.mediaPlayer.video_get_height())
        print("Duration", self.media.get_duration())
        print("Frames", int(self.media.get_duration()/1000*self.mediaPlayer.get_fps()))
        self.parent().setRatio(self.mediaPlayer.video_get_width()/self.mediaPlayer.video_get_height())

        duration = self.media.get_duration()
        self.timeSlider.setMaxTime(duration)
        self.play()

    def isPlaying(self):
        self.mediaPlayer.is_playing()

    def play(self):
        if hasattr(self, "media"):
            if self.mediaPlayer.is_playing():
                self.mediaPlaying = False
                self.timer.stop()
                self.playBtn.changeIcon(f"{self.resourcePath}/play.svg")
                self.mediaPlayer.pause()
            else:
                self.mediaPlaying = True
                self.timer.start()
                self.playBtn.changeIcon(f"{self.resourcePath}/pause.svg")
                self.mediaPlayer.play()

    def hold(self):
        if self.mediaPlaying:
            self.timer.stop()
            self.mediaPlayer.pause()
        else:
            self.timer.start()
            self.mediaPlayer.play()

    def setFrame(self, frame):
        self.mediaPlayer.set_position(frame / 1000.0)

    def setVolume(self, volume):
        self.mediaPlayer.audio_set_volume(volume)


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
        self.setStyleSheet("#Master {background-color : transparent;}")

        self._gripSize = 1
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
        self.mediaPlayer = self.vlc.media_player_new()
        self.mediaPlayer.set_hwnd(int(self.mediaContainer.winId()))

        hbox = QVBoxLayout(self)
        hbox.setContentsMargins(self._gripSize,self._gripSize,self._gripSize,self._gripSize)
        hbox.addWidget(self.mediaContainer)
        self.setLayout(hbox)

        self.controller = Controller(self)

        self.setRatio(1280/720)

    def show(self):
        super(VideoPlayer, self).show()
        self.controller.show()

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

        offset = 10

        # left edge
        self.sideGrips[0].setGeometry(
            0, inRect.top()+offset, self.gripSize, inRect.height()-offset)
        # top edge
        self.sideGrips[1].setGeometry(
            inRect.left()+offset, 0, inRect.width()-offset, self.gripSize)
        # right edge
        self.sideGrips[2].setGeometry(
            inRect.left() + inRect.width(), 
            inRect.top()+offset, self.gripSize, inRect.height()-offset)
        # bottom edge
        self.sideGrips[3].setGeometry(
            self.gripSize+offset, inRect.top() + inRect.height(), 
            inRect.width()-offset, self.gripSize)

        # top left
        self.cornerGrips[0].setGeometry(
            QRect(outRect.topLeft(), inRect.topLeft()+QPoint(offset,offset)))
        # top right
        self.cornerGrips[1].setGeometry(
            QRect(outRect.topRight(), inRect.topRight()+QPoint(-offset,offset)).normalized())
        # bottom right
        self.cornerGrips[2].setGeometry(
            QRect(outRect.bottomRight(), inRect.bottomRight()+QPoint(-offset,-offset)).normalized())
        # bottom left
        self.cornerGrips[3].setGeometry(
            QRect(outRect.bottomLeft(), inRect.bottomLeft()+QPoint(offset,-offset)).normalized())

    def setRatio(self, ratio=None):
        if ratio:
            self.ratio = ratio
        self.keepRatio(self.size())

    def keepRatio(self, size):
        newHeight = size.width()/self.ratio
        newHeight -= newHeight%1
        newHeight += 1
        if self.height() == newHeight:
            return
        self.resize(size.width(), newHeight)

    def resizeEvent(self, event):
        if event.size() == event.oldSize():
            return
        else:
            self.keepRatio(event.size())
        
        self.updateGrips()
        self.controllerResize()

    def controllerResize(self):
        self.controller.move(self.pos().x()+(self._gripSize), self.pos().y()+(self._gripSize))
        self.controller.resize(self.width()-(self._gripSize*2), self.height()-(self._gripSize*2))

if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    main = VideoPlayer()
    main.resize(500, 500)
    main.show()
    sys.exit(app.exec_())