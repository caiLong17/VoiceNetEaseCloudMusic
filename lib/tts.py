# -*- coding: utf-8 -*- 
import time
from ctypes import *
from io import BytesIO
import wave
import platform
import logging
import os
import sys
import pyaudio

logging.basicConfig(level=logging.DEBUG)

BASEPATH=os.path.split(os.path.realpath(__file__))[0]


try:
    sys_path_dir = os.path.realpath(sys.path[0])
    if os.path.isfile(sys_path_dir):
        sys_path_dir = os.path.dirname(sys_path_dir)
    G_CLIENT_DIR = os.path.abspath(sys_path_dir)
    DLL_PATH = os.path.join(G_CLIENT_DIR, "lib\\bin\\msc.dll")
    dll = windll.LoadLibrary(DLL_PATH)
except Exception as e:
    sys.path.append('.')
    dll = windll.LoadLibrary('./bin/msc.dll')


class TTS(object):
    """docstring for TTS"""
    def __init__(self):
        self.sessionID = None
        self.ret = None
        self.filename = 'test.wav'
        self.login()


    def login(self):
        login_params = "appid = 590c9c55, work_dir = ."
        ret = dll.MSPLogin(None, None, login_params)
        print('MSPLogin =>'), ret


    def tts_session_start(self):
        self.ret = c_int(0)
        session_begin_params="voice_name = xiaoyan, text_encoding = utf8, sample_rate = 16000, speed = 30, volume = 50, pitch = 50, rdn = 2"
        self.sessionID = dll.QTTSSessionBegin(session_begin_params, byref(self.ret));
        print 'QTTSSessionBegin => sessionID:', self.sessionID, 'ret:', self.ret.value


    def play_tts(self, text):
        self.tts_session_start()
        ret = dll.QTTSTextPut(self.sessionID, text, len(text), None)
        audio_len = c_uint(0)
        synth_status = c_int(0)
        ret_c = c_int(0)
        f = BytesIO()
        while True:
            

            p = dll.QTTSAudioGet(self.sessionID, byref(audio_len), byref(synth_status), byref(ret_c))

            if ret_c.value != 0:
                print("QTTSAudioGet failed, error code: " + str(ret_c));
                dll.QTTSSessionEnd(self.sessionID, "AudioGetError");
                break

            if p != None:
                buf = (c_char * audio_len.value).from_address(p)
                f.write(buf)

            if synth_status.value == 2 :
                self.saveWave(f.getvalue(), self.filename)
                break

            time.sleep(1)

        print(u'TTS done.')
        ret = dll.QTTSSessionEnd(self.sessionID, "Normal");
        if ret != 0:
            print("QTTSTextPut failed, error code: " + ret);
        self.play()


    def play(self):
        chunk = 1024
        wf = wave.open(self.filename)
        p = pyaudio.PyAudio()
        stream = p.open(format = p.get_format_from_width(wf.getsampwidth()),
                channels = wf.getnchannels(),
                rate = wf.getframerate(),
                output = True)
        while True:
            data = wf.readframes(chunk)
            if data == "": 
                break
            stream.write(data)

        stream.stop_stream()
        stream.close()
        p.terminate()


    def saveWave(self, raw_data,_tmpFile = 'test.wav'):
        f = wave.open(_tmpFile,'w')
        f.setparams((1, 2, 16000, 262720, 'NONE', 'not compressed'))
        f.writeframesraw(raw_data)
        f.close()
        return _tmpFile


if __name__ == '__main__':
    # text_to_speech('科大讯飞还是不错的','test.wav')
    tts = TTS()
    tts.play_tts("好的。")

