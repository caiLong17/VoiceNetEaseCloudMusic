#! /usr/bin/env python
# coding=utf-8

__author__ = 'ryhan'


# 以下代码解决输出乱码问题
import sys
# print sys.getdefaultencoding()
reload(sys)
sys.setdefaultencoding('utf-8')
# print sys.getdefaultencoding()

from ctypes import *
import time
import pyaudio

sys.path.append('./bin')

dll = windll.LoadLibrary("./bin/msc.dll")

# print dll.MSPLogin
# print dll.QTTSSessionBegin
# print dll.QTTSTextPut
# print dll.QTTSAudioGet
# print dll.QTTSSessionEnd

uname = "18917110835"
upass = ""

login_params = "appid = 590c9c55, work_dir = ."
session_begin_params = "sub=iat,aue=speex-wb;7,result_type=plain,result_encoding=utf8,language=zh_cn," \
                       "accent=mandarin,sample_rate=16000,domain=music,vad_bos=2000,vad_eos=2000"
grammar_id = None  # '346c55176c3a5fc69750a3068b1a8457'

FRAME_LEN = 640  # Byte

MSP_SUCCESS = 0
# 端点数据
MSP_EP_LOOKING_FOR_SPEECH = 0
MSP_EP_IN_SPEECH = 1
MSP_EP_AFTER_SPEECH = 3
MSP_EP_TIMEOUT = 4
MSP_EP_ERROR = 5
MSP_EP_MAX_SPEECH = 6
MSP_EP_IDLE = 7
# 音频情况
MSP_AUDIO_SAMPLE_INIT = 0x00
MSP_AUDIO_SAMPLE_FIRST = 0x01
MSP_AUDIO_SAMPLE_CONTINUE = 0x02
MSP_AUDIO_SAMPLE_LAST = 0x04
# 识别状态
MSP_REC_STATUS_SUCCESS = 0
MSP_REC_STATUS_NO_MATCH = 1
MSP_REC_STATUS_INCOMPLETE = 2
MSP_REC_STATUS_NON_SPEECH_DETECTED = 3
MSP_REC_STATUS_SPEECH_DETECTED = 4
MSP_REC_STATUS_COMPLETE = 5
MSP_REC_STATUS_MAX_CPU_TIME = 6
MSP_REC_STATUS_MAX_SPEECH = 7
MSP_REC_STATUS_STOPPED = 8
MSP_REC_STATUS_REJECTED = 9
MSP_REC_STATUS_NO_SPEECH_FOUND = 10
MSP_REC_STATUS_FAILURE = MSP_REC_STATUS_NO_MATCH

filename = "tts_sample.wav"
filename = "iflytek01.wav"
# filename = "ryhan.wav"


class Msp:
    def __init__(self):
        pass

    def login(self):
        ret = dll.MSPLogin(None, None, login_params)
        print('MSPLogin =>'), ret

        pass

    def isr(self, audiofile, session_begin_params, grammar_id):
        ret = c_int()
        sessionID = dll.QISRSessionBegin(grammar_id, session_begin_params, byref(ret))
        print 'QISRSessionBegin => sessionID:', sessionID, 'ret:', ret.value

        # 每秒【1000ms】  16000 次 * 16 bit 【20B】 ，每毫秒：1.6 * 16bit 【1.6*2B】 = 32Byte
        # 1帧音频20ms【640B】 每次写入 10帧=200ms 【6400B】


        p = pyaudio.PyAudio()
        stream = p.open(rate=16000,
                        channels=1,
                        format=pyaudio.paInt16,
                        input=True,
                        frames_per_buffer=2048)

        epStatus = c_int(0)
        recogStatus = c_int(0)

        wavData = stream.read(2048)

        ret = dll.QISRAudioWrite(sessionID, wavData, len(wavData), MSP_AUDIO_SAMPLE_FIRST, byref(epStatus),
                                 byref(recogStatus))
        print 'len(wavData):', len(
            wavData), 'QISRAudioWrite ret:', ret, 'epStatus:', epStatus, 'recogStatus:', recogStatus

        times = 0
        while True:
            wavData = stream.read(2048)
            ret = dll.QISRAudioWrite(sessionID, wavData, len(wavData), MSP_AUDIO_SAMPLE_CONTINUE, byref(epStatus),
                                     byref(recogStatus))
            print 'len(wavData):', len(
                wavData), 'QISRAudioWrite ret:', ret, 'epStatus:', epStatus, 'recogStatus:', recogStatus
            time.sleep(0.02)
            times += 1

            if epStatus.value != MSP_EP_IN_SPEECH:
                break

        ret = dll.QISRAudioWrite(sessionID, None, 0, MSP_AUDIO_SAMPLE_LAST, byref(epStatus),
                                 byref(recogStatus))
        print 'len(wavData):', len(
            wavData), 'QISRAudioWrite ret:', ret, 'epStatus:', epStatus, 'recogStatus:', recogStatus


        # -- 获取音频
        laststr = ''
        while recogStatus.value != MSP_REC_STATUS_COMPLETE:
            ret = c_int()
            dll.QISRGetResult.restype = c_char_p
            retstr = dll.QISRGetResult(sessionID, byref(recogStatus), 0, byref(ret))
            if retstr is not None:
                laststr += retstr
            print 'ret:', ret, 'recogStatus:', recogStatus

            time.sleep(0.2)

        print '*' * 20, 'laststr:', '*' * 20
        print laststr
        print '*' * 20, 'laststr:', '*' * 20

    pass


if __name__ == "__main__":
    msp = Msp()

    msp.login()
    msp.isr(filename, session_begin_params, grammar_id)
