from PySide2.QtCore import QSize
from PySide2.QtWidgets import QApplication, QBoxLayout, QLabel, QSpacerItem, QWidget


class RatioLabel(QLabel):
    def __init__(self, text="", parent=None):
        super(RatioLabel, self).__init__(text, parent=parent)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self):
        return self.width()

    def sizeHint(self):
        return QSize(self.width(), self.heightForWidth())

    def resizeEvent(self, event):
        if event.size().height() == self.heightForWidth():
            return
        self.resize(self.width(), self.heightForWidth())

        self.setText(f"W {self.width()} H {self.height()} R {self.width() / self.height()}")
        return super(RatioLabel, self).resizeEvent(event)

if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    w = RatioLabel()
    w.setStyleSheet("background-color:red;")
    # w.setGeometry(0,0,100,50)
    w.show()
    sys.exit(app.exec_())