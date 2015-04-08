# Spider.py
# -*- coding: utf-8 _*_
import re,urllib2
from multiprocessing.managers import BaseManager

# 任务管理类
class QueueManager(BaseManager):
    pass

# 在网络上注册，只提供名字
QueueManager.register('get_question_queue')
QueueManager.register('get_result_queue')
QueueManager.register('get_flag')

# 连接服务器
server_addr = '127.0.0.1'

#配置连接信息
m = QueueManager(address=(server_addr,5111),authkey='IamSpiderMan')

#连接
m.connect()

#获取在网络上注册的队列
task_queue = m.get_question_queue()
result_queue = m.get_result_queue()
isStart = m.get_flag()

# 寻找传入的数据中的问题链接并放到队列中
def putUrl(data):
    if data:
        # 抓取问题的号码并放入队列
        questionPattern = re.compile("<a class=\"question_link\" href=\"/question/(.*)\">.+?</a>")
        urllist = questionPattern.findall(data)
        if urllist:
            for x in urllist:
                task_queue.put(x)


# 下载队列中的问题链接
def downLoad(questionUrl):
    html = urllib2.urlopen(questionUrl).read()
    # 获取问题的标题,此处因为有空格，要开启're.S'否则不能匹配成功
    title = re.search("<h2 class=\"zm-item-title zm-editable-content\">(.*)</h2>",html,re.S).group(1).strip('\n')
    print title
    f = open(title + '.html','w+')
    f.write(html)
    f.close()
    result_queue.put(title)
    return html


def taskStart():
    hosturl = 'http://www.zhihu.com/question/'
    while task_queue.qsize() > 1 and isStart.qsize() > 0:
        num = task_queue.get()
        questionUrl = hosturl + num
        print num
        questionData = downLoad(questionUrl)
        putUrl(questionData)
    print "主人任务已完成"

taskStart()
