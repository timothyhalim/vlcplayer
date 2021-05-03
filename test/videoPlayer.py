import os
import datetime
import numpy as np

from PySide2.QtCore import QTimer
from PySide2.QtGui import QImage, QPainter, QPixmap
from PySide2.QtWidgets import QApplication, QWidget

os.environ['FFMPEG'] = os.path.normpath(os.path.join(__file__,"..", "..", "ffmpeg", "bin","ffmpeg.exe")).replace("\\", "/")
os.environ['FFPROBE'] = os.path.normpath(os.path.join(__file__,"..", "..", "ffmpeg", "bin","ffprobe.exe")).replace("\\", "/")
import ffmpeg 

def streamVideo(file, bit=8):

    format = {
        8 : {"np" : np.uint8, 'rgb' : 'gray', "ch": 1}, # Gray Scale
        24 : {"np" : np.uint8, 'rgb' : 'rgb24', "ch": 3}, # RGB 8Bit
        32 : {"np" : np.uint8, 'rgb' : 'rgba', "ch": 4} # RGBA 8Bit
    }
    if not bit in format.keys(): raise ("{bit}-Bit number not supported yet. Currently only 8-Bit (Grayscale), 24-Bit (RGB), 32-Bit(RGBA)")
    
    probe = ffmpeg.probe(file)

    video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
    print(video_stream)
    
    if video_stream:
        frames = int(eval(video_stream['nb_frames'])) if 'nb_frames' in video_stream else 1
        duration = float(eval(video_stream['duration'])) if 'duration' in video_stream else 1
        width = int(video_stream['width'])
        height = int(video_stream['height'])
        fps = frames/duration
        pix_fmt = video_stream['pix_fmt']

        metadata = {
            "frame" : frames,
            "duration" : duration,
            "fps" : fps,
            "width" : width,
            "height" : height,
            "ratio" : width/height,
            "format" : pix_fmt,
            "bit" : bit
        }

        vout, _ = (
            ffmpeg
            .input(file)
            .output('pipe:', format='rawvideo', pix_fmt=format[bit]['rgb'])
            .run(capture_stdout=True)
        )

        stream = (
            np
            .frombuffer(vout, format[bit]['np'])
            .reshape([-1, height, width, format[bit]['ch']])
        )
        return stream, metadata

class Image(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent=parent)
        
        file = 'rgba.mov'
        bit = 32
        self.vStream, self.vInfo = streamVideo(file, bit)
        
        self.frame = -1
        
        self.imageFormat = {
            8 :  QImage.Format_Grayscale8,
            24 :  QImage.Format_RGB888,
            32:  QImage.Format_RGBA8888_Premultiplied,
            # 64:  QImage.Format_RGBA64_Premultiplied
        }

        image = QImage(self.vStream[0], self.vInfo['width'], self.vInfo['height'], self.imageFormat[self.vInfo['bit']])
        self.pixmap = QPixmap(image)

        self.setFixedHeight(self.vInfo['height'])
        self.setFixedWidth(self.vInfo['width'])
        
        self.timer = QTimer(self)
        self.timer.setInterval(1)
        self.timer.timeout.connect(self.draw)

        self.startTime = datetime.datetime.now()
        self.timer.start()
        
    def mouseReleaseEvent(self, event):
        self.frame = -1
        self.startTime = datetime.datetime.now()
        self.timer.start()

    def draw(self):
        delta = (datetime.datetime.now() - self.startTime).total_seconds()
        frame = int((delta/self.vInfo['duration']) * self.vInfo['frame'])
        if frame == self.frame: return
        self.frame = frame
        if self.frame >= self.vInfo['frame'] or delta >= self.vInfo['duration']:
            self.timer.stop()
            image = QImage(self.vStream[self.vInfo['frame']-1], self.vInfo['width'], self.vInfo['height'], self.imageFormat[self.vInfo['bit']])
            self.pixmap = QPixmap(image)
            self.update()
            return
        
        image = QImage(self.vStream[self.frame], self.vInfo['width'], self.vInfo['height'], self.imageFormat[self.vInfo['bit']])
        self.pixmap = QPixmap(image)
    
        self.update()


    def paintEvent(self, event):
        painter = QPainter()
        painter.begin(self)
        painter.drawPixmap(self.rect(), self.pixmap)
        painter.end()

if __name__ == "__main__":
    app = QApplication([])
    w = Image()
    w.show()
    app.exec_()