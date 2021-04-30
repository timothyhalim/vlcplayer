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
            currentTime = f"{int(currentms / (1000*60*60)) % 24:02d}:{int(currentms / (1000*60)) % 60:02d}:{(currentms / (1000)) % 60:04.02f}"
            self.tip = QToolTip.showText(pos_global, currentTime, self)

    def qss(self):
        return """
            QSlider::handle:horizontal, QSlider::handle:vertical {
                background: #FF0000;
                border-radius: 0px;
            }
            QSlider::handle:horizontal {
                width: 8px;
                height: 8px;
            }
            QSlider::handle:vertical {
                width: 8px;
                height: 8px;
            }

            QSlider::groove:horizontal, QSlider::groove:vertical {
                border: 1px solid transparent;
                background: transparent;
            }
            QSlider::groove:horizontal {
                height: 8px;
            }
            QSlider::groove:vertical {
                background: #aa0000;
                width: 8px;
            }


            QSlider::sub-page:horizontal, QSlider::sub-page:vertical {
                background: #aa0000;
                border: 1px solid transparent;
            }
            QSlider::sub-page:horizontal {
                height: 8px;
            }
            QSlider::sub-page:vertical {
                background: black;
                width: 8px;
            }

            QSlider::handle:horizontal:hover, QSlider::handle:vertical:hover {
                background: #FF0000;
                border: 0px solid #aa0000;
                border-radius: 4px;
            }

            QSlider::sub-page:horizontal:disabled, QSlider::sub-page:vertical:disabled {
                background: #bbbbbb;
                border-color: #999999;
            }

            QSlider::add-page:horizontal:disabled, QSlider::add-page:vertical:disabled {
                background: #2a82da;
                border-color: #999999;
            }

            QSlider::handle:horizontal:disabled, QSlider::handle:horizontal:disabled {
            background: #2a82da;
            }
            """