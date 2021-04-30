import sys
import os
from datetime import datetime
from PySide2.QtGui import QColor, QPainter, QPen
from PySide2.QtCore import QEvent, QTimer, Qt
from PySide2.QtWidgets import QLabel, QSlider, QVBoxLayout, QWidget, QHBoxLayout, QApplication

try:
    fileDir = os.path.dirname(__file__)
except:
    import inspect
    fileDir = os.path.dirname(inspect.getframeinfo(inspect.currentframe()).filename)

pyVersion = float(f"{sys.version_info[0]}.{sys.version_info[1]}")
vlcdir = os.path.normpath(os.path.join(fileDir, "vlc"))
if pyVersion >= 3.8:
    os.add_dll_directory(vlcdir)
else:
    if not vlcdir in sys.path:
        sys.path.append(vlcdir)
    os.environ['PYTHON_VLC_MODULE_PATH'] = vlcdir
    os.environ['PYTHON_VLC_LIB_PATH'] = os.path.normpath(os.path.join(vlcdir, "libvlc.dll"))
    os.chdir(vlcdir)
    
import vlc

from component.ButtonIcon import ButtonIcon
from component.TimeSlider import TimeSlider
from component.FrameWidget import FrameWidget

class Controller(QWidget):
    def __init__(self, parent):
        super(Controller, self).__init__(parent)

        self.resourcePath = os.path.normpath(os.path.join(fileDir, "resource")).replace("\\", "/")

        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_Hover)
        self.setMouseTracking(True)
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
        self.timeSlider.sliderPressed.connect(self.seek)
        self.timeSlider.sliderReleased.connect(self.seek)

    def initUI(self):
        # Init
        self.visible = False
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
            self.lastMove = datetime.now()
            self.toggleVisibility(True)
        elif event.type() == QEvent.Type.Leave:
            self.toggleVisibility(False)

        return super(Controller, self).event(event)

    def mousePressEvent(self, event):
        self.startPos = event.pos()
        self.lastClick = datetime.now()
        return super(Controller, self).mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if hasattr(self, "startPos"):
            if (datetime.now() - self.lastClick).microseconds/1000 < 100:
                self.play()
            delattr(self, "startPos")
        return super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        self.lastMove = datetime.now()
        self.lastPos = event.pos()
        self.toggleVisibility(True)
        if hasattr(self, "startPos") and not (self.parent().windowState() & Qt.WindowFullScreen):
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
        self.timer.stop()
        self.mediaPlayer.pause()
        self.parent().close()
        return super().close()

    def toggleVisibility(self, visible=True):
        if self.visible == visible:
            return
        self.visible = visible
        if visible:
            self.setCursor(Qt.ArrowCursor)
        p = self.parent()
        self.move(p.pos().x()+p.gripSize, p.pos().y()+p.gripSize)
        self.resize(p.width()-(p.gripSize*2), p.height()-(p.gripSize*2))
        for w in (self.closeBtn, self.playBtn, self.volumeSlider):
            w.setVisible(visible)
        self.timeSlider.setTipVisibility(visible)
        self.timeSlider.setFixedHeight(16 if visible else 1)

    def setFullscreen(self):
        if self.parent().isFullScreen():
            self.parent().showNormal()
        else:
            self.parent().showFullScreen()
        self.parent().controllerResize()

    def updateUI(self):
        media_pos = self.mediaPlayer.get_position()
        slider_pos = int((media_pos+(0.03*media_pos)) * self.timeSlider.maximum())
        self.timeSlider.setValue(slider_pos)
        
        if (datetime.now() - self.lastMove).seconds >= 5 :
            self.setCursor(Qt.BlankCursor)
            self.toggleVisibility(False)
        else:
            self.setCursor(Qt.ArrowCursor)

    def createMedia(self, path):
        self.media = self.vlc.media_new(path)
        self.media.parse()
        print(self.media.get_meta(1))
        self.mediaPlayer.set_media(self.media)
        print("FPS:", self.mediaPlayer.get_fps())
        print("Ratio:", self.mediaPlayer.video_get_width()/self.mediaPlayer.video_get_height())
        print("Duration", self.media.get_duration())
        print("Frames", int(self.media.get_duration()/1000*self.mediaPlayer.get_fps()))
        self.parent().setRatio(self.mediaPlayer.video_get_width()/self.mediaPlayer.video_get_height())

        duration = self.media.get_duration()
        self.timeSlider.setMaxTime(duration)
        self.timeSlider.setMaximum(int(self.media.get_duration()/1000*self.mediaPlayer.get_fps()))
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
        else:
            self.createMedia(os.path.join(fileDir, "sample.mov"))

    def seek(self):
        if self.mediaPlayer.is_playing():
            if self.timer.isActive():
                self.timer.stop()
            else:
                self.timer.start()

    def setFrame(self, frame):
        self.mediaPlayer.set_position(frame / self.timeSlider.maximum())

    def setVolume(self, volume):
        self.mediaPlayer.audio_set_volume(volume)

class VideoPlayer(FrameWidget):
    def __init__(self, parent=None):
        super(VideoPlayer, self).__init__(parent)

        self.mediaContainer = QLabel()
        self.mediaContainer.setStyleSheet("background:black;")
        self.mediaContainer.setAttribute(Qt.WA_TranslucentBackground, False)
        self.mediaContainer.setObjectName("Video")
        self.vlc = vlc.Instance()
        self.mediaPlayer = self.vlc.media_player_new()
        self.mediaPlayer.set_hwnd(int(self.mediaContainer.winId()))

        hbox = QVBoxLayout(self)
        hbox.setContentsMargins(self.gripSize,self.gripSize,self.gripSize,self.gripSize)
        hbox.addWidget(self.mediaContainer)
        self.setLayout(hbox)

        self.controller = Controller(self)

    def show(self):
        super(VideoPlayer, self).show()
        self.controller.show()

    def resizeEvent(self, event):
        super(VideoPlayer, self).resizeEvent(event)
        self.controllerResize()

    def controllerResize(self):
        self.controller.move(self.pos().x()+(self.gripSize)+1, self.pos().y()+(self.gripSize)+1)
        self.controller.resize(self.width()-(self.gripSize*2)-2, self.height()-(self.gripSize*2)-2)

if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    main = VideoPlayer()
    main.resize(500, 500)
    main.show()
    sys.exit(app.exec_())