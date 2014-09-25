#!/usr/bin/env python
import os,sys,time
import threading,thread
import urllib,urllib2
import socket
import traceback

VERSION = '0.1.0'

DSTURL = "http://dq.baidu.com/nocipher?pid=rtlog&ver=1.0&cdn=yunyi&service=pcs&type=access&log=%s&node=%s"
LOG_BASE = '/logs/'
PID = '/var/run/PushLog.pid'
THREADNUM = 30
DEBUG = 0

TM = ''
socket.setdefaulttimeout(10) 

def PrintLog(s):
	if not DEBUG:	
		return
        sys.stdout.write("%s: %s" % (time.strftime('%Y-%m-%d %H:%M:%S '), str(s) + '\n'))
        sys.stdout.flush()


class Handler(object):
	def __init__(self, wid):
		pass

	def process(self, line):
		l = urllib.quote(line)
                p_url = DSTURL % (l, 'bj-ct')
		try:
			self.push(s, self.uri)
		except:
			pass

	def push(self, surl):
                try: 
			h =  urllib2.urlopen(sul)
			h.read(10)
			status = h.code
                except Exception , e:
                        PrintLog(e)
                        status = "Error"
        

class TaskManager(object):
        """             
        Simple Task Manager : To add task, process task 
        """             
                        
        def __init__(self):
                self.tasklist = [] 
                self.lock = threading.Lock()
                self.n = 0
                self.exit = 0
                self.finished = 0
        
        # add task to task list 
        def addtask(self, line):
                if len(line) == 0: return
                self.lock.acquire()
                try:self.tasklist.append(line)
                except:pass
                self.lock.release()
        
        # pop task from task list
        def poptask(self):
                task = '' 
                self.lock.acquire()
                try:    
                        if len(self.tasklist) != 0:
                                task = self.tasklist.pop(0)
                except:pass     
                self.lock.release()
                return task
                       
        # check status  
        def check(self):
                while not self.exit:
                        self.lock.acquire()
                        finished = self.finished
                        self.finished = 0
                        unfinished = len(self.tasklist)
                        self.lock.release()

                        s = '*'*20 + "finished %s unfinished %s" % (finished, unfinished) + '*'*20
                        PrintLog(s)
                        time.sleep(5)

        # start task manager
        def start(self):
                PrintLog('*'*20 + ' Start TaskManager ' + '*'*20)
                global THREADNUM
                for t in range(THREADNUM):
                        h = threading.Thread(target=self.worker, args=(t,))
                        h.start()
                c =  threading.Thread(target=self.check, args=())
                c.start()

        # work thread process task
        def worker(self, wid):
                worker_id = wid
                PrintLog( '*'*20 + ' Start Worker ' + str(worker_id) + '*'*20)
                while not self.exit:
                        task = self.poptask()
                        if task == '' :
                                time.sleep(1)
                                continue

			try:
                        	# Create Handler
                        	hd = Handler(worker_id)
                        	# Hander Process Task
                        	hd.process(task)
			except:
				PrintLog(traceback.print_exc())		
                        self.lock.acquire()
                        self.finished += 1
                        self.lock.release()


def GetFileList():
	day_min = time.strftime('%Y%m%d%H%M')
	videolist = LOG_BASE + '/access.baidu.' + day_min
	if not os.path.isfile(videolist):
		PrintLog('%s Not Exists' % videolist)
		time.sleep(3)
		return

	fp = open(videolist, 'rb')
	inode = os.stat(videolist).st_ino	
	while 1:
		if os.stat(videolist).st_ino != inode:
			fp = open(videolist, 'rb')
			inode = os.stat(videolist).st_ino

		line = fp.readline()[:-1]	
               	while line:
                        TM.addtask(line)
                        line = fp.readline()[:-1]

		if time.strftime('%Y%m%d%H%M') != day_min:
			break
		
		time.sleep(3)


def main():
	try:
        	log_base = sys.argv[1]
		thread_num = int(sys.argv[2])
		try:
			debug = sys.argv[3]
			if debug == "debug":
				debug = 1
		except:
			debug = 0
		global DEBUG
		global LOG_BASE
		global THREADNUM
		THREADNUM = thread_num
		LOG_BASE = log_base
		DEBUG = debug
	except:
		print "Usage: PushLog log_dir thread_num [debug](example PushLog /logs/ 30 )"
		sys.exit()
		pass
        global PID
        if os.path.isfile(PID):
                pid = open(PID, 'rb').read()
                cmd = 'ps -p %s' % pid
                rt = os.popen(cmd).read().split('\n')
                if rt[1] != '':
                        PrintLog('Program is runing!')
                        sys.exit()

        pid = os.getpid()
        fp = open(PID, 'wb')
        fp.write(str(pid))
        fp.close()


        global TM

        # Create Task Manager
        TM = TaskManager()
        # Start Task Manager
        TM.start()

        while 1:
                try:
                        # Get File List
                        GetFileList()
                except KeyboardInterrupt:
                        print 'Shutting Down  ...'
                        TM.exit = 1
                        break



main()
