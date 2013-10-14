'''
Created on 14.10.2013

@author: mhoyer
'''

import pycurl
import StringIO
import json
import types
import time
import datetime

def http_get(url, timeout):
    curl = pycurl.Curl()
    curl.setopt(pycurl.URL, url)
    curl.setopt(pycurl.CONNECTTIMEOUT, timeout)
    #curl.setopt(pycurl.FOLLOWLOCATION, 1)
    contents = StringIO.StringIO()
    curl.setopt(pycurl.WRITEFUNCTION, contents.write)
    curl.perform()

    #print "HTTP-STATUS: " + str(curl.getinfo(pycurl.HTTP_CODE))
    return contents.getvalue()

def build_graphite_render_url(host, target, format, from_time, local, cache):
    if local:
        local = "&local=1"
    else:
        local = "&local=0"
    if cache:
        cache = "&cache=1"
    else:
        cache = "&cache=0"
    return "http://" + host + "/render/?target=" + target + "&format=" + format + "&from=-" + from_time + local + cache
         
def get_graphite_datapoints(url):
    response = http_get(url,2)
    data = json.loads(response)
    try:
        data = data[0]
    except IndexError:
        print "No data"
        return None
    return data["datapoints"]

def count_nones(metrics):
    nones = 0
    if metrics:
        for metric in metrics:
            if isinstance(metric[0], types.NoneType):
                nones = nones + 1
        return nones
    else:
        return "No data"

# checks metric with an interval of x seconds
def check_metric_in_interval(url, interval, number_of_checks):
    max_nones = 0
    for count in range(0, number_of_checks):
        datapoints = get_graphite_datapoints(url)
        nones = count_nones(datapoints)
        if max_nones < nones:
            max_nones = nones
        print str(datetime.datetime.now()) + " - Nones: " + str(nones) + " (" + str(datapoints) + ")"
        time.sleep(interval)
    print "Maximum number of nones was: " + str(max_nones)
        

if __name__ == '__main__':
    url = build_graphite_render_url("tuvgrp12.rz.is","app.devapp12.system.diskspace._data.inodes_used","json","5min", True, False)
    print url
    check_metric_in_interval(url, 1,1800)