import datetime
import time


# 时间戳转格式化的字符串
def stamp_to_time_str():
    stamp = int(time.time())
    time_str = time.strftime("%Y-%m-%d %H:%M", time.localtime(stamp))
    return time_str


# 字符串转时间戳
def _strtime_to_timestamp(str_time):
    timestamp = time.mktime(datetime.datetime.strptime(str_time, "%Y-%m-%dT%H:%M:%S").timetuple()) + 8 * 3600
    return str(int(timestamp))



