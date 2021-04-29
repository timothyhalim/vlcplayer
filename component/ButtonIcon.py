from PySide2.QtCore import Property, QAbstractAnimation, QEasingCurve, QEvent, QPropertyAnimation, QSize
from PySide2.QtGui import QColor, QCursor, QIcon, QPixmap, Qt
from PySide2.QtWidgets import QPushButton

import os

class ButtonIcon(QPushButton):
    def __init__(self, label=None, icon="", iconsize=40, inactive=(200, 200, 200), active=(255, 0, 0), duration=300):
        super(ButtonIcon, self).__init__()

        self.activeColor = QColor(active[0], active[1], active[2])
        self.inactiveColor = QColor(inactive[0], inactive[1], inactive[2])
        self.animDuration = duration
        
        self.setStyleSheet("background-color : transparent;")
        
        self.setFixedSize(iconsize+5,iconsize+5)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.iconPath = icon
        if os.path.isfile(self.iconPath):
            self.px = QPixmap(self.iconPath)
            self.px.scaled(iconsize, iconsize, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.px_mask = self.px.createMaskFromColor(QColor('transparent'))
            self.px.fill(self.inactiveColor)
            self.px.setMask(self.px_mask)
            
            self.setIcon(QIcon(self.px))
            self.setIconSize(QSize(iconsize, iconsize))

        if isinstance(label, str):
            font = self.font()
            font.setPointSize(iconsize/10)
            self.setFont(font)
            self.setText(label)
            
        if self.px:
            self.setColor(self.inactiveColor)
            self.hoverAnimation = self.animate(self.inactiveColor, self.activeColor, self.animDuration, self.animationCallback)
            self.leaveAnimation = self.animate(self.activeColor, self.inactiveColor, self.animDuration, self.animationCallback)

    def setColor(self,value): 
        self.__color = value
        self.px.fill(self.__color)
        self.px.setMask(self.px_mask)
        self.setIcon(QIcon(self.px))

    def getColor(self): return self.__color
    color = Property(QColor, getColor, setColor)

    def animationCallback(self, state):
        if state == QAbstractAnimation.State.Stopped:
            self.hoverAnimation = self.animate(self.inactiveColor, self.activeColor, self.animDuration, self.animationCallback)
            self.leaveAnimation = self.animate(self.activeColor, self.inactiveColor, self.animDuration, self.animationCallback)

    def animate(self, start, end, duration, callback):
        ani = QPropertyAnimation(self, b"color")
        ani.setStartValue(start)
        ani.setEndValue(end)
        ani.setDuration(duration)
        ani.stateChanged.connect(callback)
        return ani

    def event(self, event):
        if event.type() == QEvent.Type.Enter:
            if self.leaveAnimation.state() == QAbstractAnimation.State.Running:
                self.leaveAnimation.stop()
                current = sum([self.getColor().redF(), self.getColor().greenF(), self.getColor().blueF()])
                target = sum([self.activeColor.redF(), self.activeColor.greenF(), self.activeColor.blueF()])
                self.hoverAnimation = self.animate(self.getColor(), self.activeColor, (target-current)*self.animDuration, self.animationCallback)
            self.hoverAnimation.start()
        elif event.type() == QEvent.Type.Leave:
            if self.hoverAnimation.state() == QAbstractAnimation.State.Running:
                self.hoverAnimation.stop()
                current = max([self.getColor().redF(), self.getColor().greenF(), self.getColor().blueF()])
                target = max([self.inactiveColor.redF(), self.inactiveColor.greenF(), self.inactiveColor.blueF()])
                self.leaveAnimation = self.animate(self.getColor(), self.inactiveColor, (current-target)*self.animDuration, self.animationCallback)
            self.leaveAnimation.start()
        elif event.type() in [QEvent.Type.MouseButtonPress, QEvent.Type.MouseButtonDblClick]:
            pressColor = QColor(
                (self.inactiveColor.red() + self.activeColor.red())/2, 
                (self.inactiveColor.green() + self.activeColor.green())/2,
                (self.inactiveColor.blue() + self.activeColor.blue())/2
            )
            self.px.fill(pressColor)
            self.px.setMask(self.px_mask)
            self.setIcon(QIcon(self.px))
        elif event.type() == QEvent.Type.MouseButtonRelease:
            self.px.fill(self.activeColor)
            self.px.setMask(self.px_mask)
            self.setIcon(QIcon(self.px))

        return super(ButtonIcon, self).event(event)