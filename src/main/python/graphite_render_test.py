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
import sys
import random

TIMEOUT_COUNT = 0
VERBOSE = False

def http_get(url, timeout):
    curl = pycurl.Curl()
    curl.setopt(pycurl.URL, url)
    curl.setopt(pycurl.CONNECTTIMEOUT, timeout)
    #curl.setopt(pycurl.FOLLOWLOCATION, 1)
    contents = StringIO.StringIO()
    curl.setopt(pycurl.WRITEFUNCTION, contents.write)
    start_time = time.time()
    curl.perform()
    response_time = round(time.time() - start_time, 5)
    #print "HTTP-STATUS: " + str(curl.getinfo(pycurl.HTTP_CODE))
    return (contents.getvalue(), response_time)


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


def get_graphite_datapoints(response):

    try:
        data = json.loads(response)
    except ValueError as ve:
        if VERBOSE:
            print "ValueError: " + str(ve)
        return []
    try:
        data = data[0]
    except IndexError:
        return []
    try:
        return data["datapoints"]
    except KeyError:
        return []

def list_average(values_list):
    return sum(values_list) / float(len(values_list))

def count_nones(metrics):
    """
    Parameters
    ----------
    metrics : list of floats
        the metrics to count nones for

    Returns
    -------
    count : int
       the number of Nones in the list or None if the list is None or empty
    """
    nones = 0
    if metrics:
        for metric in metrics:
            if metric[0] is None:
                nones = nones + 1
    return nones

def read_file(path):
    try:
        return [line.strip() for line in open(path)]
    except Exception as e:
        print "Error reading file: " + str(e)
        sys.exit(2)

def get_random_entries(dataset, number_of_entries):
    random_data = []
    for count in range(0, number_of_entries):
        index = random.randint(1,len(dataset)-1)
        random_data.append(dataset[index])
    return random_data

def check_single_metric(host, timerange, local, cache, target, interval, number_of_checks):
    generate_load(host, timerange, local, cache, [target], interval, number_of_checks)

def check_random_metrics(host, timerange, local, cache, targetfile, interval, number_of_checks, number_of_metrics):
    targets = read_file(targetfile)
    random_targets = get_random_entries(targets, number_of_metrics)
    generate_load(host, timerange, local, cache, random_targets, interval, number_of_checks)

def generate_load(host, timerange, local, cache, targets, interval, number_of_checks):
    max_nones = 0
    no_data_count = 0
    to_much_nones_count = 0
    response_times = []
    global TIMEOUT_COUNT


    for count in range(0, number_of_checks):
        for target in targets:
            url = build_graphite_render_url(host, target,"json",timerange, local, cache)
            if VERBOSE:
                print "URL: " + url

            try:
                (response, response_time) = http_get(url, 1)
            except pycurl.error as e:
                print str(datetime.datetime.now()) + " - Timeout: " + str(e)
                TIMEOUT_COUNT = TIMEOUT_COUNT + 1
                # if there was an error, drop further work on this request and start over
                continue

            if response_time:
                response_times.append(response_time)
            datapoints = get_graphite_datapoints(response)
            nones = count_nones(datapoints)
            if nones > 1:
                to_much_nones_count = to_much_nones_count + 1
            if len(datapoints) == 0:
                no_data_count = no_data_count + 1
            if max_nones < nones:
                max_nones = nones
            print str(datetime.datetime.now()) + " - Nones: " + str(nones) + "/" + str(len(datapoints)) + " - Target: " + target
            if VERBOSE:
                print "Datapoints: " + str(datapoints)
        print "## waiting " + str(interval) + "s ##"
        time.sleep(interval)
    print ""
    print "Request duration:"
    print "- Maximum request duration:    " + str(max(response_times)) + "s"
    print "- Minimum request duration:    " + str(min(response_times)) + "s"
    print "- Average request duration:    " + str(list_average(response_times)) + "s"
    print ""
    print "Data:"
    print "- Maximum number of nones:     " + str(max_nones)
    print "- Received <No Data> for:      " + str(no_data_count) + " / " + str(len(targets)*number_of_checks) + " render requests"
    print "- Received too many nones for: " + str(to_much_nones_count) + " / " + str(len(targets)*number_of_checks) + " render requests"
    print "- Got timeout for:             " + str(TIMEOUT_COUNT) + " / " + str(len(targets)*number_of_checks) + " render requests"

def main(args):

    global VERBOSE
    VERBOSE = args.verbose
    try:
        timerange = "from=-" + str(args.timerange) + "min"

        # run checknones with sigle target supplied
        if args.checknones and args.target:
            check_single_metric(args.host, timerange, args.local, args.cache, args.target, args.interval, args.count)
        if args.checknones and args.targetfile and args.numberoftargets:
            check_random_metrics(args.host, timerange, args.local, args.cache, args.targetfile, args.interval, args.count, args.numberoftargets)
        else:
            print "Invalid input supplied - USAGE:"
            print ""
            print "Input-Data:"
            print "  --target <target name> for single target checks"
            print "  --targetfile <path> to supply a file with targets"
            print ""
            print "Actions:"
            print "  --checknones: checks given metric for none values"
    except KeyboardInterrupt:
        sys.exit(0)

if __name__ == '__main__':
    # parameter handling
    parser = argparse.ArgumentParser(description='Instruments backup and replication of applications configured in a yaml config file')
    parser.add_argument("host", help="Graphite Host", type=str)
    parser.add_argument("--target", help="Graphite metric target", type=str)
    parser.add_argument("--targetfile", help="Graphite metric targets supplied as line-separated list in file", type=str)
    parser.add_argument("--numberoftargets", help="Number of targets to take randomly from targetfile", type=int)
    parser.add_argument("--local", help="Query only for local metrics on graphite host", action="store_true", default=False)
    parser.add_argument("--cache", help="Query without using cache", action="store_true", default=False)
    parser.add_argument("--timerange", help="Graphite timerange to look at", type=int, default=5)
    parser.add_argument("--interval", help="Interval for looping requests", type=float, default=1)
    parser.add_argument("--count", help="Number of requests to make", type=int, default=60)
    parser.add_argument("--checknones", help="Check number and maximum of nones for a metric", action="store_true")
    parser.add_argument("--verbose", help="Display verbose output like requested url", action="store_true", default=False)
    args = parser.parse_args()
    main(args)
