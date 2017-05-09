 #*- coding: utf-8 *-
#####################################################################
#    Created:    2017/05/
#    Filename:   client.py
#    Author:     codehai
#    Copyright:  
#********************************************************************
#    Comments:
#
#    UpdateLogs:
#####################################################################
import os
import sys
import time
import random
import json
import datetime
import glob 
import wx
import wx.html2
import threading
import thread
import _winreg
import trace
import numpy as np 
from pyaudio import PyAudio, paInt16
from lib.music import neteaseMusic
import requests
import re
from lib.asr import Msp


reload(sys)
sys.setdefaultencoding('utf-8')

############################ Utility functions ############################
def console_print(*args):

    desc = []

    if len(args) == 1:
        log_str = args[0]
    elif len(args) > 1:
        for i, arg in enumerate(args[1:]):
            if isinstance(arg, (dict, list, tuple)):
                desc.append(json.dumps(arg, ensure_ascii=False, indent=2))
            else:
                desc.append(arg) 
        log_str = args[0] % tuple(desc)

    # print "Sim> %s" %(log_str)    
    msg = "Sim> %s" %(log_str)
    wx.CallAfter(CLIENT_FRAME.log_message, msg)


############################ Main functions ############################

class ThreadTask(threading.Thread):
    """A subclass of threading.Thread, with a kill() method."""

    def __init__(self, *args, **keywords):
        threading.Thread.__init__(self, *args, **keywords)
        self.killed = False

    def start(self):
        """Start the thread."""
        self.__run_backup = self.run
        self.run = self.__run      # Force the Thread to install our trace.
        threading.Thread.start(self)

    def __run(self):
        """Hacked run function, which installs the trace."""
        sys.settrace(self.globaltrace)
        self.__run_backup()
        self.run = self.__run_backup

    def globaltrace(self, frame, why, arg):
        if why == 'call':
            return self.localtrace
        else:
            return None

    def localtrace(self, frame, why, arg):
        if self.killed:
            if why == 'line':
                raise SystemExit()
        return self.localtrace

    def kill(self):
        self.killed = True

        
class ClientFrame(wx.Frame):

    def __init__(self):
        wx.Frame.__init__(self, None, title="Client Simulator Console", size=(
            800, 600), style=wx.DEFAULT_FRAME_STYLE ^ wx.RESIZE_BORDER)
        panel = wx.Panel(self)

        # 这里需要打开所有权限
        self.key = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER, 
            r"SOFTWARE\Microsoft\Internet Explorer\Main\FeatureControl\FEATURE_BROWSER_EMULATION", 0, _winreg.KEY_ALL_ACCESS)
        try:
            # 设置注册表python.exe 值为 11000(IE11)
            _winreg.SetValueEx(self.key, 'python.exe', 0, _winreg.REG_DWORD, 0x00002af8)
        except:
            # 设置出现错误
            print 'error in set value!'

        # 定义log,console,client窗口
        self.log = wx.TextCtrl(
            panel, -1, "", style=wx.TE_MULTILINE, size=(425, 550))
        self.console = wx.TextCtrl(
            panel, -1, "", size=(175, -1), style=wx.TE_PROCESS_ENTER)
        self.browser = wx.html2.WebView.New(panel, -1, size=(330, 600))

        # 用BoxSizer布局页面
        left_inner = wx.BoxSizer(wx.VERTICAL)
        right_inner = wx.BoxSizer(wx.VERTICAL)
        main = wx.BoxSizer(wx.HORIZONTAL)
        main.Add(left_inner, 0, wx.ALL, 5)
        main.Add(right_inner, 0, wx.ALL, 5)
        left_inner.Add(self.browser, 1, wx.ALL, 5)
        right_inner.Add(self.log, 1, wx.EXPAND | wx.ALL, 5)
        right_inner.Add(self.console, 0, wx.EXPAND | wx.ALL, 5)
        panel.SetSizer(main)

        # 绑定事件
        self.Bind(wx.EVT_CLOSE,  self.on_close_window)
        self.Bind(wx.EVT_TEXT_ENTER, self.enter_console)

        # 显示主界面
        self.root_path = os.path.abspath('./lib/templates')
        self.main_url = os.path.abspath('./lib/templates/main.html')
        print(self.main_url)
        self.browser.LoadURL(self.main_url)

        # 默认cloud 测试开启 录音自动打开
        self.audio_in = True

        
    def on_close_window(self, evt):
        self.Destroy()
        # 用完取消注册表设置
        _winreg.DeleteValue(self.key, 'python.exe')
        # 关闭打开的注册表
        _winreg.CloseKey(self.key)


    def client_show(self, content_data, img_id=1, script=None):
        # console_print(content_data)
        if img_id not in [0, 1, 2, 3]:
            img_id = 1
        script_show = '''
                $('.back_image').hide();
                $('#tuner').hide();
                $('#b%d').show();
            ''' %(img_id)
        if isinstance(content_data, (str, unicode)):
            script_show = script_show + '''
                $('.middle-inner').html('');
                $('.middle-inner').append('%s');
            ''' % (content_data)
        elif isinstance(content_data, dict):
            for data in content_data:
                if data == 'info':
                    script_show = script_show + '''
                        $('.middle-inner').html('');
                        $('.middle-inner').append('<p>%s</p>');
                        $('.middle-inner').fadeIn('slow');
                    ''' % (content_data['info'])
                for div in ['title', 'footer', 'header']:
                    if data == div:
                        script_show = script_show + '''
                            $('#%s').html('%s').show();
                        ''' % (data, content_data[data])
                    else:
                        script_show = script_show + '''
                            $('#%s').hide();
                        ''' %(div)      
                if data == 'number':
                    script_show = script_show + '''
                        $('.middle-inner').html('');
                        $('.middle-inner').append('<p>%s</p>');
                        $('.middle-inner').show();
                    ''' % (content_data['number'])
                if data == 'content':
                    script_show = script_show +'''
                        $('.middle-inner').html('');
                    '''
                    for index, content in enumerate(content_data['content']):
                        script_show = script_show + '''
                            $('.middle-inner').append('<p><ins>%s</ins><span>&nbsp;&nbsp;&nbsp;&nbsp;</span>%s</p>');
                        ''' % (index+1, content)
                    script_show = script_show + '''
                            $('.middle-inner').show();
                        ''' 
                if data == 'icon':
                    icon_id = content_data['icon']
                    if icon_id == 3:
                        script_show = script_show + '''
                            icon_speaker = $('#icon-speaker').clone();
                            $('.middle-inner').html('');
                            $('.middle-inner').append('<p></p>');
                            $('.middle-inner p').append(icon_speaker);
                            $('.middle-inner p #icon-speaker').show();
                            $('.middle-inner').show();
                        '''
        if script:
            script_show += script

        if img_id == 0:
            script_show = script_show + "$('.middle-inner').html('');"
            for div in ['title', 'header', 'footer', 'content']:
                script_show = script_show + '''
                    $('#%s').html('');
                ''' %(div)
        print(script_show) 
        self.browser.RunScript(script_show)


    def client_clean(self):
        pass
        # self.browser.SetPage('')


    def log_message(self, msg):
        try:
            self.log.AppendText(msg)
        except Exception as e:
            print e
            print 'log wrong %s' %(msg)
        self.log.AppendText('\n')


    def cloud_debug(self):
        '''
        调试云端接口
        '''
        NUM_SAMPLES = 2048      # pyAudio内部缓存的块的大小
        SAMPLING_RATE = 16000    # 取样频率
        LEVEL = 1000            # 声音保存的阈值
        COUNT_NUM = 5           # NUM_SAMPLES个取样之内出现COUNT_NUM个大于LEVEL的取样则记录声音
        SAVE_LENGTH = 8         # 声音记录的最小长度：SAVE_LENGTH * NUM_SAMPLES 个取样

        audio_cut = 0
        audio_collect = []

        #asr 初始化
        asr = Msp()

        # 开启声音输入
        pa = PyAudio() 
        stream = pa.open(format=paInt16, channels=1, rate=SAMPLING_RATE, input=True, 
                frames_per_buffer=NUM_SAMPLES)

        last_audio_data = 0

        SESSION_STARTED = False

        index = 0
        while self.audio_in:
            # 读入NUM_SAMPLES个取样
            string_audio_data = stream.read(NUM_SAMPLES) 
            # 将读入的数据转换为数组
            audio_data = np.fromstring(string_audio_data, dtype=np.short) 
            # 计算大于LEVEL的取样的个数
            large_sample_count = np.sum( audio_data > LEVEL )
            max_audio_data = np.max(audio_data)
            
            # console_print(max_audio_data)
                
            if not audio_cut:
                audio_collect.append(max_audio_data)
                if len(audio_collect) == 10:
                    audio_cut = sum(audio_collect) - max(audio_collect) - min(audio_collect)
                    console_print('audio_cut = %s', str(audio_cut))
            else:

                if max_audio_data > audio_cut:
                    if not SESSION_STARTED:
                        SESSION_STARTED = True
                        console_print('Start session.')
                        asr.session_begin()
                    #TODO push data
                    asr.data_push(string_audio_data, index)
                    index += 1
                else:
                    if last_audio_data > audio_cut:
                        console_print('Stop session.')
                        SESSION_STARTED = False
                        asr.data_push(string_audio_data, index)
                        asr.data_push([], index+1)
                        #TODO push last data
                        # push(string_audio_data, index=index+1)
                        # push([], index=index+2)
                        index = 0
                        #TODO get result
                        asr_result = asr.get_result()
                        asr.session_end()
                        console_print(type(asr_result))
                        console_print(asr_result.decode('utf-8'))
                        #call Tree
                last_audio_data = max_audio_data

    def enter_console(self, evt):
        cmd = self.console.GetValue()
        if cmd:
            self.log_message(cmd)
            self.console.SetValue('')

            if cmd == 'cloud':
                thread.start_new_thread(self.cloud_debug, ())

            elif cmd == 'pause':
                MusicAPP.pause()

            elif cmd == 'resume':
                MusicAPP.resume()

            elif cmd == 'next':
                MusicAPP.next()

            elif cmd == 'continue':
                self.audio_in = True
                thread.start_new_thread(self.cloud_debug, ())

            elif cmd == 'play':
                MusicAPP.play_song()

            elif cmd == 'stop':
                MusicAPP.stop()

            elif '$' in cmd:
                self.browser.RunScript(cmd)
            elif '.html' in cmd:
                self.browser.LoadURL(cmd)
        else:
            self.log_message("Please enter command(play, pause, resume, stop, etc.):")

   

class Music(object):
    """docstring for Music""" 
    
    def __init__(self):
        self.playing = False
        # self.pause = False
        self.index = 0
        self.mode = 0
        self.music_task = None
        self.playlist = []


    def music_script(self, music_info, percent_pos):
        script = u"""
            var template = '\
            <div id="music">\
                <div class="music-info">\
                </div>\
                <div class="progress">\
                    <div class="progress-bar progress-bar-info" role="progressbar" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100" style="width: 0%">\
                        <span class="sr-only">40% Complete (success)</span>\
                    </div>\
                </div>\
            </div>'
            $("#music").remove();
            $(".middle-box").append(template);
            $(".middle-box .music-info").html("{0}");    
            $(".middle-box .progress-bar").css("width","{1}%");
            $(".middle-box").show();
        """.format(music_info, percent_pos)
        
        wx.CallAfter(CLIENT_FRAME.client_show, None, script=script)


    def source_change(self, *args, **kwargs):
        APP_INSTANCES["tuner"].scan(( 1 if args[0]== 7 else 0))
        return True

    def execCmd(self, cmd):  
        try:  
            print u"命令%s开始运行%s" % (cmd,datetime.datetime.now())  
            os.system(cmd)  
            print u"命令%s结束运行%s" % (cmd,datetime.datetime.now())  
        except Exception, e:  
            print u'%s\t 运行失败,失败原因\r\n%s' % (cmd,e)


    def get_percent_pos(self):
        try:
            while True:
                time.sleep(1)
                song_name = self.playlist[self.index]['name']
                artist_name = self.playlist[self.index]['artists'][0]['name']
                music_info = "%s-%s" %(song_name, artist_name)
                if not self.playing:
                    break
                else:
                    cmd = "echo print-text ${percent-pos} >\\\\.\pipe\mpvsocket"
                    os.system(cmd)
                    with open('mpv.log') as file:
                        lines = file.readlines()
                    if lines:
                        if re.match('Exiting', lines[-1]):
                            break
                        elif re.match(r'\d+', lines[-1]):
                            percent_pos = re.findall(r'\d+', lines[-1])[0]
                            self.music_script(music_info, percent_pos)
                            if int(percent_pos) > 98:
                                self.next()
        except Exception as e:
            console_print('Exceptiong in get_percent_pos e = %s', e) 


    def play(self, mode='replace'):
        try:
            if self.mode == 1:
                self.index = random.randint(0, len(self.playlist))
            print(json.dumps(self.playlist[self.index], indent=2))
            song_id = self.playlist[self.index]['id']
            song_name = self.playlist[self.index]['name']
            artist_name = self.playlist[self.index]['artists'][0]['name']

            url = "http://music.163.com/#/song?id=%d" %(song_id)
            music = neteaseMusic(url)
            source = music.url_parser()
            console_print('source = %s', source)
            console_print('Start play.')
            console_print(u'歌曲名:%s', song_name)
            console_print(u'歌手名:%s', artist_name)
            if not self.music_task:
                cmd = ".\lib\mpv\mpv --quiet --audio-display no %s --input-ipc-server=\\\\.\pipe\mpvsocket > mpv.log" %(source)
                console_print('Start music task.')
                self.music_task = ThreadTask(target=self.execCmd, args=(cmd,))
                self.music_task.start()
                self.playing = True
                thread.start_new_thread(self.get_percent_pos, ())
            else:
                cmd = "echo loadfile %s %s >\\\\.\pipe\mpvsocket" %(source, mode)
                console_print('Loadfile mode=%s.', mode)
                os.system(cmd)
            return song_name.encode('utf-8'), artist_name.encode('utf-8')
        except Exception as e:
            console_print('Exception in music play. Exception:%s', e)


    def play_artist(self, *args, **kwargs):
        try:
            payload = { 
                's': args[0],
                'limit':10, 
                'type':100, 
                'offset':0 
            } 
            r = requests.post("http://music.163.com/api/search/get/",
                      params=payload, headers=HEADERS, cookies=COOKIES)
            result = json.loads(r.text)['result']
            if result['artistCount'] >= 1:
                artist_id = result['artists'][0]['id']
                console_print("get artist_id = %d", artist_id)
                album_url = "http://music.163.com/api/artist/albums/%d/?offset=0&limit=3" %(artist_id)
                r = requests.get(album_url, headers=HEADERS, cookies=COOKIES)
                result = json.loads(r.text)
                if len(result['hotAlbums']) >= 1:
                    album_id = result['hotAlbums'][0]['id']
                    url = "http://music.163.com/api/album/%d/" %(album_id)
                    r = requests.get(url, headers=HEADERS, cookies=COOKIES)
                    self.playlist =  json.loads(r.text)['album']['songs']
                    return self.play()
                else:
                    return False
            else:
                return False
        except Exception as e:
            console_print('Exception in music play_artist. Exception:%s', e)


    def play_song(self, *args, **kwargs):
        try:
            if len(args) >= 1 and args[0]:
                payload = { 
                    's': args[0],
                    'limit':30, 
                    'type':1, 
                    'offset':0 
                }
                r = requests.post("http://music.163.com/api/search/get/", params=payload)
                result = json.loads(r.text)['result']
                if result['songCount'] >= 1:
                    self.playlist = result['songs']
                    return self.play()
                else:
                    return False
            else:
                url = "http://music.163.com/api/playlist/detail?id=31246857&&updateTime=-1"
                r = requests.get(url, headers=HEADERS, cookies=COOKIES)
                tracks = json.loads(r.text)['result']['tracks']
                self.playlist = tracks
                return self.play()
        except Exception as e:
            console_print('Exception in music play_artist. Exception:%s', e)


    def next(self, *args, **kwargs):
        if self.playing:
            self.index += 1
            if self.index > len(self.playlist):
                self.index = 0
            return self.play()
        else:
            return False

    def previous(self, *args, **kwargs):
        if self.playing:
            self.index -= 1
            if self.index < -len(self.playlist):
                self.index = 0
            return self.play()
        else:
            return False

    def resume(self, *args, **kwargs):
        if self.playing:
            cmd = "echo set pause no >\\\\.\pipe\mpvsocket"
            os.system(cmd)
            return True
        else:
            return False

    def pause(self, *args, **kwargs):
        if self.playing:
            cmd = "echo set pause yes >\\\\.\pipe\mpvsocket"
            os.system(cmd)
            return True
        else:
            return False


    def stop(self, *args, **kwargs):
        if self.playing:
            self.playing = False
            self.music_task = None
            cmd = 'echo stop >\\\\.\pipe\mpvsocket'
            os.system(cmd)
            script = u'''
                $("#music").remove()
            '''
            cmd = 'taskkill /f /im mpv.exe'
            os.system(cmd)
            wx.CallAfter(CLIENT_FRAME.client_show, None, script=script)
            return True
        else:
            return False


if __name__ == "__main__":

    COOKIES = {"appver":"2.0.2"}
    HEADERS = {"Referer":"http://music.163.com"}

    MusicAPP = Music()
    APP = wx.PySimpleApp() 
    CLIENT_FRAME = ClientFrame()
    CLIENT_FRAME.Show()
    APP.MainLoop()
