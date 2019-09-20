from __future__ import absolute_import
from __future__ import print_function
from xml.dom import minidom
import os
import sys
import random
import optparse
import subprocess
import random
import time
import math
import copy

routeFile = "RouteFileTemplate.rou.xml"

def generateTrips(options, edgeFileDir):
    fromNodes = []
    toNodes = []
    numberOfTrips = options.numberOfTrips
    runTime = options.runTime
    # parse an xml file by name
    mydoc = minidom.parse(options.edgeFile)

    edges = mydoc.getElementsByTagName('edge')

    for elem in edges:
        fromNodes.append(elem.attributes['from'].value)
        toNodes.append(elem.attributes['to'].value)

    fromNodes = removeIntersectionNodes(fromNodes)
    toNodes = removeIntersectionNodes(toNodes)

    fromEdges = []
    toEdges = []

    for edge in edges:
        if(edge.attributes['from'].value in fromNodes):
            fromEdges.append(edge.attributes['id'].value)
        if(edge.attributes['to'].value in fromNodes):
            toEdges.append(edge.attributes['id'].value)
    
    randomDepartures = [] 
  
    for j in range(0, numberOfTrips): 
        randomDepartures.append(random.randint(0, runTime)) 

    randomDepartures.sort()

    fo = open(routeFile, "r+")
    routeFileAsString = fo.read()
    fo.close()

    toReplace = "//TRIPS_PLACEHOLDER"
    value = ""
    for i in range(0, numberOfTrips):
        value += "<trip id=\"" + str(i) + "\" depart=\"" + str(randomDepartures[i]) + "\" from=\"" + random.choice(fromEdges) + "\" to=\"" + random.choice(toEdges) + "\"/>\n"

    routeFileAsString = str.replace(routeFileAsString, toReplace, value, 1)

    modelName = os.path.join(edgeFileDir, options.outFile + '.rou.xml')
    text_file = open(modelName, "w")
    text_file.write(routeFileAsString)
    text_file.close()
    print("Success")

def removeIntersectionNodes(listOfNodes):
    return [i for i in listOfNodes if listOfNodes.count(i) <= 1]


def get_options():
    optParser = optparse.OptionParser()
    optParser.add_option("--trips", type="int",
                         default=2000, dest="numberOfTrips")
    optParser.add_option("--time", type="int",
                         default=1000, dest="runTime")
    optParser.add_option("--edgeFile", type="string", dest="edgeFile", default="")
    optParser.add_option("-o", type="string", dest="outFile", default="")  
    options, args = optParser.parse_args()
    return options

                  
# this is the main entry point of this script
if __name__ == "__main__":
    options = get_options()

    if(options.edgeFile == ""):
        sys.exit("edgeFile cannot be empty")
    if((os.path.exists(options.edgeFile)) == False):
        sys.exit("edgeFile does not exist: " + options.edgeFile)
    if(options.outFile == ""):
        sys.exit("outFile cannot be empty")
    
    edgeFileDir = os.path.dirname(options.edgeFile)
    generateTrips(options, edgeFileDir)



