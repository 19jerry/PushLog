#!/bin/bash
yum install python-setuptools
easy_install supervisor
mkdir -p /data/pushlog/logs
cp -i src/PushLog.py /usr/bin/PushLog
chmod 755 /usr/bin/PushLog  
