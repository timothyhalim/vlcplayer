from component.ButtonIcon import ButtonIcon
from PySide2 import QtWidgets
import os

app = QtWidgets.QApplication([])
play = os.path.normpath(os.path.join(__file__, "..", "resource", "cancel.svg"))
player = ButtonIcon("", icon=play, iconsize=40)
player.show()
player.resize(640, 480)
app.exec_()
