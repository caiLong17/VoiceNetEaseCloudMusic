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
import os
import time
import pyaudio

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


# print dll.MSPLogin
# print dll.QTTSSessionBegin
# print dll.QTTSTextPut
# print dll.QTTSAudioGet
# print dll.QTTSSessionEnd

uname = "18917110835"
upass = ""

login_params = "appid = 590c9c55, work_dir = ."
session_begin_params = "sub=iat,aue=speex-wb;7,result_type=plain,result_encoding=utf8,language=zh_cn," \
                       "accent=mandarin,sample_rate=16000,domain=music,vad_bos=1000,vad_eos=1000"
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
        self.login()
        self.sessionID = None
        self.recogStatus = None
        self.epStatus = None
        self.ret = None


    def login(self):
        ret = dll.MSPLogin(None, None, login_params)
        # self.ret = dll.MSPLogin(None, None, login_params)
        # print('MSPLogin =>'), self.ret
        print('MSPLogin =>'), ret


    def session_begin(self):
        self.epStatus = c_int(0)
        self.recogStatus = c_int(0)
        self.ret = c_int()
        self.sessionID = dll.QISRSessionBegin(grammar_id, session_begin_params, byref(self.ret))
        print 'QISRSessionBegin => sessionID:', self.sessionID, 'ret:', self.ret.value

    def session_end(self):
        self.ret = c_int()
        dll.QISRSessionEnd(self.sessionID, byref(self.ret))
        print 'QISRSessionEnd => sessionID:', self.sessionID, 'ret:', self.ret.value


    def data_push(self, data, index):
        if index == 0:
            self.ret = dll.QISRAudioWrite(self.sessionID, data, len(data), MSP_AUDIO_SAMPLE_FIRST, byref(self.epStatus),
                                     byref(self.recogStatus))
        else:
            if data:
                self.ret = dll.QISRAudioWrite(self.sessionID, data, len(data), MSP_AUDIO_SAMPLE_CONTINUE, byref(self.epStatus),
                                     byref(self.recogStatus))
            else:
                self.ret = dll.QISRAudioWrite(self.sessionID, None, 0, MSP_AUDIO_SAMPLE_LAST, byref(self.epStatus),
                                 byref(self.recogStatus))

        print ('index:', index, 'len(wavData):', len(data), 'QISRAudioWrite ret:', 
                self.ret, 'epStatus:', self.epStatus, 'recogStatus:', self.recogStatus)


    def get_result(self):
        laststr = ''
        times = 0
        while self.recogStatus.value != MSP_REC_STATUS_COMPLETE:
            times += 1
            self.ret = c_int()
            dll.QISRGetResult.restype = c_char_p
            retstr = dll.QISRGetResult(self.sessionID, byref(self.recogStatus), 0, byref(self.ret))
            if retstr is not None:
                laststr += retstr
            print 'ret:', self.ret, 'recogStatus:', self.recogStatus
            time.sleep(0.2)
            if times > 5:
                break
        return laststr

