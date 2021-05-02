import os
import datetime
import numpy as np

from PySide2.QtCore import QTimer
from PySide2.QtGui import QImage, QPainter, QPixmap
from PySide2.QtWidgets import QApplication, QWidget
from PySide2.QtMultimedia import QAudioFormat, QAudioOutput

os.environ['FFMPEG'] = os.path.normpath(os.path.join(__file__,"..", "..", "ffmpeg", "bin","ffmpeg.exe")).replace("\\", "/")
os.environ['FFPROBE'] = os.path.normpath(os.path.join(__file__,"..", "..", "ffmpeg", "bin","ffprobe.exe")).replace("\\", "/")
import ffmpeg 

class Image(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent=parent)
        
        file = '60.mp4'

        probe = ffmpeg.probe(file)
        audio_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'audio'), None)
        print(audio_stream)
        self.audiorate = int(1/eval(audio_stream['time_base']))
        self.channels = int(audio_stream['channels'])

        video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
        self.frames = int(eval(video_stream['nb_frames']))
        self.duration = float(eval(video_stream['duration']))
        self.video_width = int(video_stream['width'])
        self.video_height = int(video_stream['height'])
        self.fps = self.frames/self.duration
        self.pix_fmt = video_stream['pix_fmt']

        print(video_stream)
        print(self.duration, self.frames, self.video_width, self.video_height, self.fps)
        self.trim = min(self.frames, 500)
        self.duration = self.trim / self.frames * self.duration
        print(self.duration)

        videoFormat = {
            np.uint8 : 'rgb24'
        }

        vout, _ = (
            ffmpeg
            .input(file)
            .output('pipe:', format='rawvideo', pix_fmt='rgb24', vframes=self.trim)
            .run(capture_stdout=True)
        )

        self.video = (
            np
            .frombuffer(vout, np.uint8)
            .reshape([-1, self.video_height, self.video_width, 3])
        )

        audioFormat = {
            np.float64: 'f64le',
            np.float32: 'f32le',
            np.int16: 's16le',
            np.int32: 's32le',
            np.uint32: 'u32le'
        }

        aout, _ = (
            ffmpeg
            .input(file)
            .output('pipe:', format='f64le', acodec="pcm_f64le", ac=str(self.channels), vframes=self.trim)
            .run(capture_stdout=True)
        )
        self.audio = (
            np
            .frombuffer(aout, np.float64)
            .reshape([-1, self.channels])
        )

        print(self.audio)
        print(self.video.shape)
        print(self.audio.shape)

        format = QAudioFormat ()
        format.setSampleRate (self.audiorate)
        format.setChannelCount (self.channels)
        format.setSampleSize ( 16 )
        format.setCodec ( "audio / pcm" ) 
        format.setByteOrder (QAudioFormat.LittleEndian )
        format.setSampleType (QAudioFormat.SignedInt)
        self.audio = QAudioOutput ( format , self)
        self.stream = self.audio.start()
        
        self.frames = self.video.shape[0]
        height = self.video.shape[1]
        width = self.video.shape[2]

        self.setFixedHeight(height)
        self.setFixedWidth(width)
        
        self.timer = QTimer(self)
        self.timer.setInterval(1)
        self.timer.timeout.connect(self.draw)

        self.startTime = datetime.datetime.now()
        self.timer.start()
        
        self.frame = -1
        
        image = QImage(self.video[0], self.video_width, self.video_height, QImage.Format_RGB888)
        self.pixmap = QPixmap(image)
        
    def mouseReleaseEvent(self, event):
        self.frame = -1
        self.startTime = datetime.datetime.now()
        self.timer.start()

    def draw(self):
        delta = (datetime.datetime.now() - self.startTime).total_seconds()
        frame = int((delta/self.duration) * self.frames)
        if frame == self.frame: return
        self.frame = frame
        if self.frame >= self.frames or delta > self.duration:
            self.timer.stop()
            print("Done")
            return
        
        print(self.frame, delta, int(delta%1 * self.fps))
        image = QImage(self.video[self.frame], self.video_width, self.video_height, QImage.Format_RGB888)
        self.pixmap = QPixmap(image)
        self.stream.write( self.audio )
    
        self.update()


    def paintEvent(self, event):
        painter = QPainter()
        painter.begin(self)
        painter.drawPixmap(self.rect(), self.pixmap)
        painter.end()

app = QApplication([])
w = Image()
w.show()
app.exec_()