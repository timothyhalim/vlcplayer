# https://wiki.python.org/moin/PyQt/Playing%20a%20sound%20with%20QtMultimedia
# https://github.com/baoboa/pyqt5/blob/master/examples/multimedia/audiooutput.py
# TEST
import numpy
from PySide2.QtCore import QBuffer, QByteArray, QIODevice
from PySide2.QtMultimedia import QAudio, QAudioFormat, QAudioOutput, QAudioBuffer, QAudioDeviceInfo, QMediaPlayer, \
    QMediaContent

wav_file = Path(__file__).resolve().parents[2] / 'dat' / 'test-mwm.wav'
wav = Track.read(wav_file)

audioFormat = QAudioFormat()
audioFormat.setChannelCount(1)
audioFormat.setSampleRate(wav.fs)
audioFormat.setSampleSize(16)
audioFormat.setCodec("audio/pcm")
audioFormat.setByteOrder(QAudioFormat.LittleEndian)
audioFormat.setSampleType(QAudioFormat.SignedInt)

device = QAudioDeviceInfo.defaultOutputDevice()
info = QAudioDeviceInfo(device)
print(info.deviceName())
assert info.isFormatSupported(audioFormat)

###
# data = QByteArray()
# data.clear()
# data.append(numpy.ndarray.tobytes(wav.value))
# data.fromRawData(numpy.ndarray.tobytes(wav.value))
data = QByteArray(numpy.ndarray.tobytes(wav.value))

# buffer = QBuffer()
# buffer.setData(data)
buffer = QBuffer(data)
buffer.open(QIODevice.ReadOnly)
buffer.seek(0)

content = QMediaContent()
player = QMediaPlayer()
player.setMedia(content, buffer)
player.play()

# output = QAudioOutput(device, audioFormat)
# # output.setVolume(0.99)  # linear
#
#
#
# #output.start(buffer)
# device = output.start()
# print(output.state())
# print(device.isWritable())
# device.write(data)
# print(output.state())
# ###

import time

time.sleep(5)
