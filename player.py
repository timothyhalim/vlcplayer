import sys
import os
from datetime import datetime
from PySide2.QtGui import QColor, QPainter, QPen
from PySide2.QtCore import Property, QEvent, QPropertyAnimation, QTimer, Qt
from PySide2.QtWidgets import QAction, QFileDialog, QGraphicsOpacityEffect, QMenu, QPushButton, QSlider, QVBoxLayout, QWidget, QHBoxLayout, QApplication

try:
    fileDir = os.path.dirname(__file__)
except:
    import inspect
    fileDir = os.path.dirname(inspect.getframeinfo(inspect.currentframe()).filename)

from component.ButtonIcon import ButtonIcon
from component.TimeSlider import TimeSlider
from component.MediaContainer import MediaContainer

class Controller(QWidget):
    def __init__(self, parent=None):
        super(Controller, self).__init__(parent)

        self.resourcePath = os.path.normpath(os.path.join(fileDir, "resource")).replace("\\", "/")

        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_Hover)
        self.setMouseTracking(True)
        self.setAcceptDrops(True)

        # self.setContextMenuPolicy(Qt.CustomContextMenu)
        # self.customContextMenuRequested.connect(self.onRightClick)


        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)

        self.fillColor = QColor(127, 127, 127, 2)
        self.penColor = QColor(127, 127, 127, 2)

        self.visible = False
        self.drawDrag = False
        self.isPaused = False
        self.lastMove = datetime.now()
        self.lastButton = Qt.MouseButton.NoButton

        self.setupWidget()
        self.setupRightClick()
        if parent:
            self.player = parent
            self.setupSignal()
        self.toggleVisibility(False)

    def setParent(self, parent):
        self.player = parent
        return super().setParent(parent)

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

        self.timer = QTimer()
        self.timer.setInterval(50)
        self.timer.timeout.connect(self.toggleCursor)
        self.timer.start()

        self.fx = []
        for w in (self.closeBtn, self.playBtn, self.volumeSlider):
            fx = QGraphicsOpacityEffect()
            fx.setOpacity(0)
            w.setGraphicsEffect(fx)
            self.fx.append(fx)
        self.timeSlider.setHeight(1)

    def setupRightClick(self):
        self.popMenu = QMenu(self)
        self.openAct = QAction('Open File', self)
        self.fullAct = QAction('Fullscreen', self)
        self.listAct = QAction('Playlist', self)
        self.helpAct = QAction('Help', self)
        self.exitAct = QAction('Exit', self)

        for act in (self.openAct, self.fullAct, self.listAct, self.helpAct):
            self.popMenu.addAction(act)
        self.popMenu.addSeparator()
        self.popMenu.addAction(self.exitAct)

        # Initial 
        self.fullAct.setCheckable(True)
        self.listAct.setCheckable(True)

        # Temp
        self.listAct.setDisabled(True)
        self.helpAct.setDisabled(True)

    def hoverAnimation(self, end, duration):
        anims = []
        for fx in self.fx:
            ani = QPropertyAnimation(fx, b"opacity")
            ani.setStartValue(fx.opacity())
            ani.setEndValue(end)
            a = max(fx.opacity(), end)
            i = min(fx.opacity(), end)
            ani.setDuration((a-i)*duration)
            anims.append(ani)
        return anims

    def setupSignal(self):
        # Controller 
        self.closeBtn.clicked.connect(self.player.close)
        self.playBtn.clicked.connect(self.togglePlay)
        self.volumeSlider.valueChanged.connect(self.player.setVolume)
        self.timeSlider.sliderMoved.connect(self.seek)

        # Player
        self.player.stateChanged.connect(self.onStateChanged)
        self.player.lengthChanged.connect(self.onLengthChanged)
        self.player.timeChanged.connect(self.onTimeChanged)

        # Right click
        self.openAct.triggered.connect(self.openFile)
        self.fullAct.triggered.connect(self.toggleFullscreen)
        self.exitAct.triggered.connect(self.player.close)

    def event(self, event):
        if event.type() == QEvent.Type.Enter:
            self.lastMove = datetime.now()
            self.toggleVisibility(True)
        elif event.type() == QEvent.Type.Leave:
            self.toggleVisibility(False)

        return super(Controller, self).event(event)

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

    def mousePressEvent(self, event):
        self.lastButton = event.button()
        if event.button() == Qt.MouseButton.LeftButton:
            self.startPos = event.pos()
            self.lastClick = datetime.now()
        elif event.button() == Qt.MouseButton.MiddleButton:
            self.startFrame = self.timeSlider.value()
            self.startPos = event.pos()
        return super(Controller, self).mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if hasattr(self, "startPos"):
                if (datetime.now() - self.lastClick).microseconds/1000 < 100:
                    self.togglePlay()
                delattr(self, "startPos")

        elif event.button() == Qt.MouseButton.RightButton:
            self.popMenu.exec_(self.mapToGlobal(event.pos())) 
            
        elif self.lastButton == Qt.MouseButton.MiddleButton:
            if hasattr(self, "startPos"): delattr(self, "startPos")
            if hasattr(self, "startFrame"): delattr(self, "startFrame")

        self.lastButton = None
        return super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        self.lastMove = datetime.now()
        self.toggleVisibility(True)

        if self.lastButton == Qt.MouseButton.LeftButton:
            if not self.player.isFullScreen():
                if hasattr(self, "startPos"):
                    delta = event.pos()-self.startPos
                    self.move(self.pos()+delta)
                    self.player.move(self.player.pos()+delta)
        elif self.lastButton == Qt.MouseButton.MiddleButton:
            if hasattr(self, "startFrame"):
                self.player.pause()
                
                delta = event.pos()-self.startPos
                percent = delta.x()/self.width()
                
                m = self.timeSlider.maximum()
                final = int(self.startFrame+(percent*m))
                
                self.timeSlider.setValue(final)
                self.seek()

        return super(Controller, self).mouseMoveEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggleFullscreen()

        return super().mouseDoubleClickEvent(event)

    def wheelEvent(self, event):
        increment = int(self.volumeSlider.maximum() / 10)
        if (event.angleDelta().y()) > 0 :
            self.volumeSlider.setValue(self.volumeSlider.value()+increment)
        elif (event.angleDelta().y()) < 0 :
            self.volumeSlider.setValue(self.volumeSlider.value()-increment)
        return super().wheelEvent(event)

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
            self.player.stop()
            self.player.createMedia(url)
        elif event.mimeData().hasText():
            url =  event.mimeData().text()
            if os.path.isfile(url):
                self.player.createMedia(url)
    
    def keyPressEvent(self, event):
        print(event.key())
        return super().keyPressEvent(event)

    def onLengthChanged(self, length):
        self.timeSlider.setMaxTime(length)
        self.timeSlider.setMaximum(int(length/1000*self.player.fps))

    def onTimeChanged(self, pos):
        sliderPos = int(pos * self.timeSlider.maximum())
        self.timeSlider.setValue(sliderPos)

    def onStateChanged(self, state):
        if state == 'NothingSpecial':
            return
        elif state == 'Opening':
            return
        elif state == 'Buffering':
            return
        elif state == 'Playing':
            self.playBtn.changeIcon(f"{self.resourcePath}/pause.svg")
        elif state == 'Paused':
            self.playBtn.changeIcon(f"{self.resourcePath}/play.svg")
        elif state == 'Stopped':
            self.playBtn.changeIcon(f"{self.resourcePath}/play.svg")
        elif state == 'Ended':
            self.timeSlider.setValue(self.timeSlider.maximum())
        elif state == 'Error':
            return

    def onRightClick(self, point):
        self.popMenu.exec_(self.mapToGlobal(point))   

    def openFile(self):
        fileName, _ = QFileDialog.getOpenFileName(self, "Open Movie", fileDir, "All (*.*)")
        
        if fileName != '':
            self.player.createMedia(fileName)

    def toggleVisibility(self, visible=True):
        if self.visible == visible:
            return
        self.visible = visible
        if visible:
            self.setCursor(Qt.ArrowCursor)
            
        self.move(self.player.pos().x()+self.player.gripSize, self.player.pos().y()+self.player.gripSize)
        self.resize(self.player.width()-(self.player.gripSize*2), self.player.height()-(self.player.gripSize*2))

        self.anims = self.hoverAnimation(1 if visible else 0, 300)
        heightAni = QPropertyAnimation(self.timeSlider, b"Height")
        heightAni.setStartValue(self.timeSlider.getHeight())
        heightAni.setEndValue(16 if visible else 1)
        self.anims.append(heightAni)
        for a in self.anims:
            a.start()

        self.timeSlider.setTipVisibility(visible)
        # self.timeSlider.setFixedHeight()

    def toggleCursor(self):
        if (datetime.now() - self.lastMove).seconds >= 5 :
            self.setCursor(Qt.BlankCursor)
            self.toggleVisibility(False)
        else:
            self.setCursor(Qt.ArrowCursor)

    def toggleFullscreen(self):
        if self.player.isFullScreen():
            self.player.showNormal()
        else:
            self.player.showFullScreen()
        self.fullAct.setChecked(self.player.isFullScreen())
        self.player.controllerResize()

    def togglePlay(self):
        if not self.player.media:
            self.openFile()

        if self.player.isPlaying():
            self.player.pause()
        else:
            self.player.play()

    def seek(self):
        self.player.setPosition(self.timeSlider.value()/self.timeSlider.maximum())

    def slide(self, pos):
        self.player.setPosition(pos)

if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    main = MediaContainer()
    main.setController(Controller(main))
    main.resize(500, 500)
    main.show()
    sys.exit(app.exec_())