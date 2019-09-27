import os
import sys
import random
import optparse
import subprocess
import math
import pandas as pd

def find_value(line, parameter, digits):
  	start = line.find(parameter) + len(parameter) + 2
  	line = line[start:start+digits]
  	line = line.replace('"', '')
  	return line


def generate_results(options, tripResultDir, tripFileDir, queueFileDir):
	f = open(tripFileDir, "r+")
	r = open(queueFileDir, "r+")

	maxDuration = 0
	maxTimeLoss = 0
	maxWaitingTime = 0
	maxQueueLength = 0
	maxQueueLengthExp = 0
	durationList = []
	timeLossList = []
	waitingTimeList = []
	queueLengthList = []
	queueLengthExpList = []


	for line in f:
		if "<tripinfo id" in line:
		#Finds a value with 2 digits. 
			currDuration = float(find_value(line, "duration", 5))
			currTimeLoss = float(find_value(line, "timeLoss", 5))
			currWaitingTime = float(find_value(line, "waitingTime", 5))
			if(currDuration > maxDuration):
				maxDuration = currDuration
			if(currTimeLoss > maxTimeLoss):
				maxTimeLoss = currTimeLoss
			if(currWaitingTime > maxWaitingTime):
				maxWaitingTime = currWaitingTime

			durationList.append(find_value(line, "duration", 5))
			timeLossList.append(find_value(line, "timeLoss", 5))
			waitingTimeList.append(find_value(line, "waitingTime", 5))
		
	for line in r:
		if "<lane id" in line:
			currQueueLength = float(find_value(line, "queueing_length", 5))
			currQueueLengthExp = float(find_value(line, "queueing_length_experimental", 5))
			if(currQueueLength > maxQueueLength):
				maxQueueLength = currQueueLength
			if(currQueueLengthExp > maxQueueLengthExp):
				maxQueueLengthExp = currQueueLengthExp

			queueLengthList.append(find_value(line, "queueing_length", 5))
			queueLengthExpList.append(find_value(line, "queueing_length_experimental", 5))


	d = {'AverageDuration':[Average(durationList)],
		'AverageTimeLoss':[Average(timeLossList)],
		'AverageWaitingTime':[Average(waitingTimeList)],
		'AverageQueueLength':[Average(queueLengthList)],
		'AverageQueueLengthExp':[Average(queueLengthExpList)],
		'maxDuration':[maxDuration],
		'maxTimeLoss':[maxTimeLoss],
		'maxWaitingTime':[maxWaitingTime],
		'maxQueueLength':[maxQueueLength],
		'maxQueueLengthExp':[maxQueueLengthExp],
		'95thPercentileLength':[getnPercentile(95, queueLengthList)],
		'95thPercentileLengthExp':[getnPercentile(95, queueLengthExpList)]
		
		}
	df = pd.DataFrame(d)

	df.to_csv(tripResultDir, index=False)
	
	f.close()
	r.close()
	
	print("succes")


def Average(lst):
	lst = list(map(float, lst))
	return sum(lst) / len(lst)

def getnPercentile(n, queueLengthList):
	lst = list(map(float, queueLengthList))
	lst.sort()
	listLength = len(lst)
	index = listLength * (n/100)

	return 	(lst[math.floor(index)] + lst[math.ceil(index)]) / 2

def get_options():
    optParser = optparse.OptionParser()
    optParser.add_option("--tripinfofile", type="string", dest="tripinfofile", default="", help="Parses the trip info. They are in the results directory")
    optParser.add_option("--queuefile", type="string", dest="queuefile", default="", help="Parses the queue info. They are in the results directory")
    options, args = optParser.parse_args()
    return options
                  
# this is the main entry point of this script
if __name__ == "__main__":
    options = get_options()

    if(options.tripinfofile == ""):
	    sys.exit("A result file is neccesary")

    tripFileDir = "results/" + options.tripinfofile + ".xml"
    queueFileDir = "results/" + options.queuefile + ".xml"
    tripResults = "results/Results_" + str(options.tripinfofile) + ".csv"
    generate_results(options, tripResults, tripFileDir, queueFileDir)


