pid=`ps aux | grep "PushLog" | grep -v grep | awk '{print $2}'`
echo 'PushLog pid' $pid
if [ -z $pid ]
then
echo 'Start PushLog ....'
python /data/gather/gather_video.py 1>/data/gather/video.log 2>/data/gather/video.err &
fi
