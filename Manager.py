# Manager.py
# -*- coding: utf-8 -*-
import re
import urllib
import urllib2
import cookielib
import Queue,time
from multiprocessing.managers import BaseManager
# 存放问题链接的队列
questionQueue = Queue.Queue()

#存放下载结果的队列
resultQueue = Queue.Queue()

# 是否开始标志
isStart = Queue.Queue()

class QueueManager(BaseManager):
    pass


# 在网络上注册队列
QueueManager.register('get_question_queue',callable=lambda:questionQueue)
QueueManager.register('get_result_queue',callable=lambda:resultQueue)
QueueManager.register('get_flag',callable=lambda:isStart)

# 绑定端口设置验证码
manager = QueueManager(address=('',5111),authkey='IamSpiderMan')
manager.start()

# 获得网络上的数据对象
questionNum = manager.get_question_queue()
resultNum = manager.get_result_queue()
isStart = manager.get_flag()
# 登陆类，负责登陆知乎
class Login(object):
    def __init__(self,id,password,result):
        self.id = id
        self.password = password
        self.result = result
        # 浏览器header
        self.header = {
            'Connection':'Keep-Alive',
            'Accept':'text/html,application/xhtml+xml,*/*',
            'Accept-Language':'en-US,en;q=0.8,zh-Hans-CN;q=0.5,zh-Hans;q=0.3',
            'User-Agent':'Mozilla/5.0(Windows NT 6.3;WOW64;Trident/7.0;rv:11.0) like Gecko',
            'Accept-Encodeing':'gzip,deflate',
            'Host':'www.zhihu.com',
            'DNT':'1'
        }
    # 获取登陆需要的_xsrf
    def getXSRF(self):
        data = re.compile('name=\"_xsrf\" value=\"(.*)\"',flags = 0)
        str = data.findall(self.result)
        return str[0]

    # 将字典转换成元组集合，放进opener
    def getOpener(self):
        myCookie = cookielib.CookieJar()
        process = urllib2.HTTPCookieProcessor(myCookie)
        opener =urllib2. build_opener(process)
        header = []
        for key,value in self.header.items():
            elem = (key,value)
            header.append(elem)
        opener.addheaders = header
        return opener

# 返回登陆成功后的响应信息
    def login(self,loginUrl):
        xsrf = self.getXSRF()
        postData = {
            '_xsrf':xsrf,
            'email':self.id,
            'password':self.password,
            'rememberme':'y'
        }
        opener = self.getOpener()
        responseData = urllib.urlencode(postData).encode()
        openData = opener.open(loginUrl,responseData)
        return openData.read()


# 寻找传入的数据中的问题链接并放到队列中
def putUrl(data):
    if data:
        # 抓取问题的号码并放入队列
        questionPattern = re.compile("<a class=\"question_link\" target=\"_blank\" href=\"/question/(.*)\">")
        urllist = questionPattern.findall(data)
        for x in urllist:
            questionNum.put(x)

# 爬虫主进程
class QuestManager():
    def __init__(self,id,password,num):
        self.id = id
        self.password = password
        self.count = num

    def tStart(self):
        hosturl = 'http://www.zhihu.com/'
        result = urllib2.urlopen(hosturl).read()
        zhihu = Login(self.id,self.password,result)
        data = zhihu.login(hosturl + 'login')
        putUrl(data)
        isStart.put(1)
        print "任务初始化完成等待爬虫仔报告......."
        time.sleep(3)
        i = 0
        while i < self.count:
            print "报!",resultNum.get(),"已完成下载"
            i += 1
        isStart.get()
        print "主人任务已完成!"
        time.sleep(3)
        manager.shutdown()


test = QuestManager(account,password,20)
test.tStart()
#print "请输入知乎账号 密码 以及要爬的网页数(空格隔开)\n"
#str = raw_input()
#mess = str.split(' ')

#zhihu = QueueManager(mess[0],mess[1],int(mess[2]))
#zhihu.tStart()



