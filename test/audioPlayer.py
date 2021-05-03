import os
from PySide2.QtWidgets import QApplication, QPushButton, QWidget
import numpy as np

from PySide2.QtCore import QBuffer, QByteArray, QIODevice, QTimer
from PySide2.QtMultimedia import QAudio, QAudioDeviceInfo, QAudioFormat, QAudioOutput

os.environ['FFMPEG'] = os.path.normpath(os.path.join(__file__,"..", "..", "ffmpeg", "bin","ffmpeg.exe")).replace("\\", "/")
os.environ['FFPROBE'] = os.path.normpath(os.path.join(__file__,"..", "..", "ffmpeg", "bin","ffprobe.exe")).replace("\\", "/")
import ffmpeg 

file = "30.mp4"
probe = ffmpeg.probe(file)

audio_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'audio'), None)

channels = int(audio_stream['channels'])
samplerate = int(audio_stream['sample_rate'])
duration = float(eval(audio_stream['duration']))
audio_codec = audio_stream.get('codec_name')
if (audio_stream.get('sample_fmt') == 'fltp' and audio_codec in ['mp3', 'mp4', 'aac', 'webm', 'ogg']):
    bit = 16
else:
    bit = audio_stream['bits_per_sample']

audioFormat = {
    8  : {'np':np.int8, 'codec':"u8"},
    16 : {'np':np.int16, 'codec':"s16le"},
    32 : {'np':np.int32, 'codec':"s32le"}
}

aout, _ = (
    ffmpeg
    .input(file)
    .output('pipe:', format=audioFormat[bit]["codec"], acodec=f"pcm_{audioFormat[bit]['codec']}", ac=channels)
    .run(capture_stdout=True)
)

audio = (
    np
    .frombuffer(aout, dtype=np.int16)
    # .reshape([channels, -1])
    .transpose()
)
# print(audio.tobytes())

data = QByteArray(audio.tobytes())
app = QApplication([])
w = QPushButton()

format = QAudioFormat()
format.setSampleRate (samplerate)
format.setChannelCount (channels)
format.setSampleSize ( bit )
format.setCodec ( "audio/pcm" ) 
format.setByteOrder (QAudioFormat.LittleEndian )
format.setSampleType (QAudioFormat.SignedInt)

audio = QAudioOutput(format=format)
stream = audio.start()

started = False
def play():
    # print(audio.bufferSize())
    # print(audio.bytesFree())
    if audio.bytesFree() == audio.bufferSize():
        if t.started:
            data.remove(0, audio.bytesFree())
        stream.write(data)
        t.started = True
        # print(dir(stream))
        
t = QTimer(w)
t.setInterval(10)
t.timeout.connect(play)
t.started = False
t.start()

w.show()
app.exec_()
