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
import argparse


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


def build_graphite_render_url(host, target, format, timerange, local, cache):
    if local:
        local = "&local=1"
    else:
        local = "&local=0"
    if cache:
        cache = "&cache=1"
    else:
        cache = "&cache=0"
    return "http://" + host + "/render/?target=" + target + "&format=" + format + "&" + timerange + local + cache


def get_graphite_datapoints(url):
    response = http_get(url, 2)

    try:
        data = json.loads(response)
    except ValueError as ve:
        print ve
        return []
    try:
        data = data[0]
    except IndexError:
        print response
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


def main(args):
    timerange = "from=-" + str(args.timerange) + "min"
    url = build_graphite_render_url(args.host,args.target,"json",timerange, args.local, args.cache)
    print url
    if args.checknones:
        check_metric_in_interval(url, args.interval, args.count)
    else:
        print "Usage:"
        print "--checknones: checks given metric for none values"


if __name__ == '__main__':
    # parameter handling
    parser = argparse.ArgumentParser(description='Instruments backup and replication of applications configured in a yaml config file')
    parser.add_argument("host", help="Graphite Host", type=str)
    parser.add_argument("target", help="Graphite metric target", type=str)
    parser.add_argument("--local", help="Query only for local metrics on graphite host", action="store_true", default=False)
    parser.add_argument("--cache", help="Query without using cache", action="store_true", default=False)
    parser.add_argument("--timerange", help="Graphite timerange to look at", type=int, default=5)
    parser.add_argument("--interval", help="Interval for looping requests", type=int, default=1)
    parser.add_argument("--count", help="Number of requests to make", type=int, default=60)
    parser.add_argument("--checknones", help="Check number and maximum of nones for a metric", action="store_true")
    args = parser.parse_args()
    main(args)
