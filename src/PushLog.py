#!/usr/bin/env python
import os,sys,time
import threading,thread
import urllib,urllib2
import socket
import traceback

VERSION = '0.1.0'

DSTURL = "http://dq.baidu.com/nocipher?pid=rtlog&ver=1.0&cdn=ctdns&service=pcs&type=access&log=%s&node=%s"
LOG_BASE = '/logs/'
PID = '/var/run/PushLog.pid'
THREADNUM = 30
DEBUG = 0
DAY_MIN = ''
SERVERCONF = ''
SERVERS = {}

TM = ''
socket.setdefaulttimeout(10) 

def PrintLog(s, tt=''):
	if not DEBUG and tt == '':	
		return
        sys.stdout.write("%s: %s" % (time.strftime('%Y-%m-%d %H:%M:%S '), str(s) + '\n'))
        sys.stdout.flush()


def GetServerList():
	global SERVERCONF
	global SERVERS
	last_mtime = 0
	while 1:
		server_tmpd = {}
		mtime = os.stat(SERVERCONF).st_mtime
		if mtime > last_mtime:
			fp = open(SERVERCONF, 'rb')
			cont = fp.read().split('\n')
			fp.close()
			for k in cont:
				if len(k)  == 0:continue
				if k.find('#') >= 0 :continue
				try:
					items = k.split()
					sip = items[0]
					idc = items[1]
					server_tmpd[sip] = idc
				except:	
					pass
			SERVERS = server_tmpd
			PrintLog('Server Num %s' % len(SERVERS.keys()), 'info')
			last_mtime = mtime

		time.sleep(60)


class Handler(object):
	def __init__(self, wid):
		pass

	def process(self, line):
		"""112.251.255.160 - p0.qq.sogoucdn.com [26/Sep/2014:13:19:05 +0800] 0.175 "GET /u/dhqq/v2/js/jquery.min.js HTTP/1.1" 502 718 "http://xiaoshuo.sogou.com/" "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/31.0.1650.63 Safari/537.36 SE 2.X MetaSr 1.0" "112.251.255.160" 123.151.116.75 "-" 1411708745.206 "-" MISS
		"""
		idc = ''
		st = 0
		global SERVERS
		try:
			items = line.split(' ')
			s_ip = items[-5]
			idc = SERVERS.get(s_ip, '') 
		except:
			traceback.print_exc()
		l = urllib.quote(line)
                p_url = DSTURL % (l, idc)
		try:
			st = self.push(p_url)
		except:
			traceback.print_exc()
		return st

	def push(self, surl):
		st = 0
                try: 
			h =  urllib2.urlopen(surl)
			h.read(10)
			status = h.code
			if status == 200:
				st = 1		
                except Exception , e:
                        PrintLog(e)
                        status = "Error"
		return st
        

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
		self.error = 0
        
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
			error = self.error
                        self.finished = 0
			self.error = 0
                        unfinished = len(self.tasklist)
                        self.lock.release()

                        s = '*'*20 + "finished %s error %s unfinished %s" % (finished, error, unfinished) + '*'*20
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
                        	isok = hd.process(task)
			except:
				PrintLog(traceback.print_exc())		
                        self.lock.acquire()
			if isok:
                        	self.finished += 1
			else:
				self.error += 1
                        self.lock.release()

def gen_next_min(day_min):
	next_min = time.strftime('%Y%m%d%H%M',(time.localtime(time.mktime(time.strptime(day_min, '%Y%m%d%H%M')) + 60)))
	return next_min

def juge_change():
	global DAY_MIN
	if time.strftime('%Y%m%d%H%M') != DAY_MIN:
		next_day_min = gen_next_min(DAY_MIN)
		DAY_MIN = next_day_min
		return 1
	return 0

def GetFileList():
	global DAY_MIN
	videolist = LOG_BASE + '/access.baidu' + DAY_MIN
	PrintLog('Process logfile ' + videolist, 'info')
	if not os.path.isfile(videolist):
		PrintLog('%s Not Exists' % videolist)
		time.sleep(1)
		juge_change()
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

		day_change = juge_change()
		if day_change:
			break
		
		time.sleep(1)


def main():
	try:
        	log_base = sys.argv[1]
		thread_num = int(sys.argv[2])
		server_file = sys.argv[3]
		try:
			debug = sys.argv[4]
			if debug == "debug":
				debug = 1
		except:
			debug = 0
		global DEBUG
		global LOG_BASE
		global THREADNUM
		global SERVERCONF
		THREADNUM = thread_num
		LOG_BASE = log_base
		SERVERCONF = server_file
		DEBUG = debug
	except:
		print "Usage: PushLog log_dir thread_num server_file [debug](example PushLog /logs/baidulog/ /logs/servers.txt 30)"
		sys.exit()
		pass
        global PID
        if os.path.isfile(PID):
                pid = open(PID, 'rb').read()
                cmd = 'ps -p %s' % pid
                rt = os.popen(cmd).read().split('\n')
                if rt[1] != '':
                        PrintLog('Program is runing!', 'info')
                        sys.exit()

        pid = os.getpid()
        fp = open(PID, 'wb')
        fp.write(str(pid))
        fp.close()

	# start GetServerList Thread
	thread.start_new_thread(GetServerList, ())

        global TM

        # Create Task Manager
        TM = TaskManager()
        # Start Task Manager
        TM.start()
	day_min = time.strftime('%Y%m%d%H%M')
	global DAY_MIN
	DAY_MIN = day_min
        while 1:
                try:
                        # Get File List
                        GetFileList()
                except KeyboardInterrupt:
                        print 'Shutting Down  ...'
                        TM.exit = 1
                        break



main()
