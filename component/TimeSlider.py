from PySide2.QtCore import QPoint
from PySide2.QtWidgets import QApplication, QSlider, QStyleOptionSlider, QToolTip

class TimeSlider(QSlider):
    def __init__(self, *args, maxTime=1, offset=QPoint(-25, 0)):
        super(TimeSlider, self).__init__(*args)
        self.offset = offset

        self.setMaxTime(maxTime)
        self.setFixedHeight(8)
        self.style = QApplication.style()
        self.opt = QStyleOptionSlider()
        self.setMaximum(1000)

        self.valueChanged.connect(self.show_tip)
        self.enterEvent = self.show_tip
        # self.mouseReleaseEvent = self.show_tip
        self.setTipVisibility(True)

        self.setStyleSheet(self.qss())

    def setMaxTime(self, maxTime):
        self.maxTime = maxTime
        
    def setTipVisibility(self, visible):
        self.tipVisible = visible

    def show_tip(self, _):
        if self.isVisible() and self.tipVisible:
            self.initStyleOption(self.opt)
            rectHandle = self.style.subControlRect(self.style.CC_Slider, self.opt, self.style.SC_SliderHandle)

            pos_local = rectHandle.topLeft() + self.offset
            pos_global = self.mapToGlobal(pos_local)
            currentms = self.maxTime * (float(self.value()) / 1000)
            currentTime = f"{int(currentms / (1000*60*60)) % 24:02d}:{int(currentms / (1000*60)) % 60:02d}:{(currentms / (1000)) % 60:05.02f}"
            self.tip = QToolTip.showText(pos_global, currentTime, self)

    def qss(self):
        return """
            QSlider::handle:horizontal {
                background: #FF0000;
                width: 8px;
                border: 2px solid #aa0000;
                border-radius: 0px;
            }

            QSlider::groove:horizontal {
                border: 1px solid #444444;
                height: 8px;
                background: transparent;
            }

            QSlider::sub-page:horizontal {
                background: #aa0000;
                border: 1px solid transparent;
                padding-right: 24px; 
                border-top-right-radius: 4px;
                border-bottom-right-radius: 4px;
                height: 8px;
            }

            QSlider::handle:horizontal:hover {
                background: #FF0000;
                height: 8px;
                width: 8px;
                border: 0px solid #aa0000;
                border-radius: 4px;
            }

            QSlider::sub-page:horizontal:disabled {
                background: #bbbbbb;
                border-color: #999999;
            }

            QSlider::add-page:horizontal:disabled {
                background: #2a82da;
                border-color: #999999;
            }

            QSlider::handle:horizontal:disabled {
            background: #2a82da;
            }
            """