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
	durationList = []
	timeLossList = []
	waitingTimeList = []
	queueLengthList = []
	queueLengthExpList = []


	for line in f:
		if "<tripinfo id" in line:
		#Finds a value with 2 digits. 

			durationList.append(find_value(line, "duration", 5))
			timeLossList.append(find_value(line, "timeLoss", 5))
			waitingTimeList.append(find_value(line, "waitingTime", 5))


	d = {'AverageDuration':[Average(durationList)],'AverageTimeLoss':[Average(timeLossList)],'AverageWaitingTime':[Average(waitingTimeList)]}
	df = pd.DataFrame(d)

	df.to_csv(tripResultDir, index=False)

	f.close()

def Average(lst):
	lst = list(map(float, lst))
	return sum(lst) / len(lst)

def getnPercentile(n, queueLengthList):
	listLength = len(queueLengthList)
	index = listLength * (n/100)

	return 	(queueLengthList[math.floor(index)] + queueLengthList[math.ceil(index)]) / 2

def get_options():
    optParser = optparse.OptionParser()
    optParser.add_option("--tripinfofile", type="string", dest="tripinfofile", default="", help="--tripinforfile parses the trip info. They are in the results directory")
    optParser.add_option("--queuefile", type="string", dest="queuefile", default="", help="--queuefile parses the queue info. They are in the results directory")
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


