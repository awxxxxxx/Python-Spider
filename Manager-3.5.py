# Manager.py
# -*- coding: utf-8 -*-
import re
from urllib.request import urlopen,build_opener,HTTPCookieProcessor
from http import cookiejar
from urllib.parse import urlencode
import queue,time
from multiprocessing.managers import BaseManager
# 存放问题链接的队列
questionQueue = queue.Queue()

#存放下载结果的队列
resultQueue = queue.Queue()

# 是否开始标志
isStart = queue.Queue()

class QueueManager(BaseManager):
    pass

def return_questionQueue():
    global questionQueue
    return questionQueue

def return_resultQueue():
    global resultQueue
    return resultQueue

def return_isStart():
    global isStart
    return isStart

def init():
    # 在网络上注册队列
    QueueManager.register('get_question_queue', callable=return_questionQueue)
    QueueManager.register('get_result_queue', callable=return_resultQueue)
    QueueManager.register('get_flag', callable=return_isStart)

    # 绑定端口设置验证码
    manager = QueueManager(address=('127.0.0.1', 5111), authkey=b'IamSpiderMan')
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
                'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language':'en-US,en;q=0.8,zh-Hans-CN;q=0.5,zh-Hans;q=0.3',
                'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.101 Safari/537.36',
                'Accept-Encodeing':'gzip,deflate,sdch',
                'Host':'www.zhihu.com',
                'Origin':'https://www.zhihu.com',
                'DNT':'1',
                'Upgrade-Insecure-Requests':'1',
                'X-Requested-With':'XMLHttpRequest',
            }
        # 获取登陆需要的_xsrf
        def getXSRF(self):
            data = re.compile('name=\"_xsrf\" value=\"(.*?)\"')
            sp = data.search(str(self.result))
            s=str(sp.group()).split('"')[len(str(sp.group()).split('"'))-2]
            self.code=s
            return s

        # 将字典转换成元组集合，放进opener
        def getOpener(self):
            self.cookie = cookiejar.CookieJar()
            process = HTTPCookieProcessor(self.cookie)
            opener = build_opener(process)
            header = []
            for key,value in self.header.items():
                elem = (key,value)
                header.append(elem)
            opener.addheaders = header
            return opener

    # 返回登陆成功后的响应信息
        def login(self,loginUrl):
            xsrf = self.getXSRF()
            self.header['X-Xsrftoken']=xsrf
            postData = {
                '_xsrf':xsrf,
                'email':self.id,
                'password':self.password,
                'captcha_type':'cn'
            }
            opener = self.getOpener()
            self.cookie.set_cookie(cookiejar.Cookie(
                version=0,
                name="_xsrf",
                value=xsrf,
                port=None,
                port_specified=False,
                domain="www.zhihu.com",
                domain_specified=True,
                domain_initial_dot=False,
                path="/",
                path_specified=True,
                secure=False,
                expires=None,
                discard=False,
                comment=None,
                comment_url=None,
                rest=None
            ))
            responseData = urlencode(postData).encode()
            openData = opener.open(loginUrl,responseData)
            c=self.cookie._cookies.values()
            return openData.read()


    # 寻找传入的数据中的问题链接并放到队列中
    def putUrl(data):
        if data:
            # 抓取问题的号码并放入队列
            questionPattern = re.compile("<a class=\"question_link\" target=\"_blank\" href=\"/question/(.*?)\">")
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
            hosturl = 'https://www.zhihu.com/'
            result = urlopen(hosturl).read()
            zhihu = Login(self.id,self.password,result)
            data = zhihu.login(hosturl + 'login/email')
            putUrl(data)
            isStart.put(1)
            print("任务初始化完成等待爬虫仔报告.......")
            time.sleep(3)
            i = 0
            while i < self.count:
                print("报!",resultNum.get(),"已完成下载")
                i += 1
            isStart.get()
            print("主人任务已完成!")
            time.sleep(3)
            manager.shutdown()

    test = QuestManager("", "", 20)
    test.tStart()

if __name__  == '__main__':
    init()
#print "请输入知乎账号 密码 以及要爬的网页数(空格隔开)\n"
#str = raw_input()
#mess = str.split(' ')

#zhihu = QueueManager(mess[0],mess[1],int(mess[2]))
#zhihu.tStart()



