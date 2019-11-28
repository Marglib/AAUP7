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
import webbrowser
import xml.etree.cElementTree as ET
import pandas as pd
import numpy as np
from numpy.random import choice

# we need to import python modules from the $SUMO_HOME/tools directory
try:
     tools = os.path.join(os.environ['SUMO_HOME'], "tools")
     sys.path.append(tools)
except:   
     sys.exit("please declare environment variable 'SUMO_HOME'")

from sumolib import checkBinary
import sumolib
import traci

rootDir = os.path.abspath(os.getcwd())
pathToFiles = rootDir
routeFile = os.path.join(pathToFiles,"RouteFileTemplate.rou.xml")


def generateTrips(options, edgeFileDir):
    fromNodes = []
    toNodes = []
    numberOfTrips = options.numberOfTrips
    runTime = options.runTime
    # parse an xml file by name
    mydoc = minidom.parse(options.edgeFile)

    edges = mydoc.getElementsByTagName('edge')

    fromEdges = []
    toEdges = []



    for edge in edges:
        if("_in" in edge.attributes['type'].value):
            fromEdges.append(edge.attributes['id'].value)
        if("_out" in edge.attributes['type'].value):
            toEdges.append(edge.attributes['id'].value)
    

    randomDepartures = [] 
  
    for j in range(0, numberOfTrips): 
        randomDepartures.append(random.randint(0, runTime)) 

    randomDepartures.sort()

    fo = open(routeFile,"r+")
    routeFileAsString = fo.read()
    fo.close()

    toReplace = "//TRIPS_PLACEHOLDER"
    value = ""
    
    if (options.closeRoads):
        generateRerouter()

    if options.useProbFile:
        df = pd.read_csv(os.path.join(pathToFiles,"inOutNodes.txt"))
        
        isCorrect = verifyProbabilitys(df)
        fromNodes = [element.split("-")[0] for element in fromEdges]
        toNodes = [element.split("-")[1] for element in toEdges]

        additionalInNodes = len(fromEdges) - len(df[df["inOut"] == "in"])
        additionalOutNodes = len(toEdges) - len(df[df["inOut"] == "out"])

        probabilityRemainder = 100 - df[df["inOut"] == "in"].probability.sum()
        defaultWeight = 0

        if additionalInNodes <= 0 and not isCorrect:
            print("something is wrong with your probFile")
            return
        else:  
            defaultWeight = probabilityRemainder / additionalInNodes
        
        inWeights = []
        for ele in fromNodes:
            if ele in (df[df["inOut"] == "in"].nodeName.values):
                inWeights.append( df[df["nodeName"] == ele].iloc[0].probability / 100)
            else:
                inWeights.append(defaultWeight / 100)

        probabilityRemainder = 100 - df[df["inOut"] == "out"].probability.sum()
        outWeights = []
        defaultWeight = probabilityRemainder / additionalOutNodes
        for ele in toNodes:
            if ele in (df[df["inOut"] == "out"].nodeName.values):
                outWeights.append( df[df["nodeName"] == ele].iloc[0].probability / 100)
            else:
                outWeights.append(defaultWeight / 100)

        randomDep = choice(fromEdges, numberOfTrips, p=inWeights)
        randomDest = choice(toEdges, numberOfTrips, p=outWeights)

        singleDest = ""

        for i in range (0, numberOfTrips):
            singleDest = randomDest[i]
            while True:
                if randomDep[i].split("-")[0] != singleDest.split("-")[1] :
                    break
                else:
                    singleDest = choice(toEdges, 1, p=outWeights)[0]
                    
            value += "<trip id=\"" + str(i) + "\" depart=\"" + str(randomDepartures[i]) + "\" from=\"" + randomDep[i] + "\" to=\"" + singleDest + "\"/>\n"
            

    for i in range(0, numberOfTrips):
        randomDep = ""
        randomDest = ""

        
        if options.standard:
            value += "<trip id=\"" + str(i) + "\" depart=\"" + str(randomDepartures[i]) + "\" from=\"" + random.choice(fromEdges) + "\" to=\"" +  random.choice(toEdges) + "\"/>\n"
            

    routeFileAsString = str.replace(routeFileAsString, toReplace, value, 1)

    modelName = os.path.join(edgeFileDir, options.outFile + '.rou.xml')
    text_file = open(modelName, "w")
    text_file.write(routeFileAsString)
    text_file.close()
    print("Success")
    if(options.playSong == True):
        webbrowser.open('https://www.youtube.com/watch?v=Y6ljFaKRTrI')  #


def verifyProbabilitys(df):
    if df[df["inOut" ] == "in"].probability.sum() != 100:
        return False
    if df[df["inOut" ]== "out"].probability.sum() != 100:
        return False

    return True

def findIncomingEdges(edgesToClose):
    dom = minidom.parse("MasterNetFile.net.xml")
    junctions = dom.getElementsByTagName("junction")
   
    result = ""
    for junc in  junctions:
        inclanes = junc.getAttribute("incLanes")
        if ':' in inclanes:
            pass
        else:
            inclanes = inclanes.split(' ')
            incEdges = []
            for lane in inclanes:
                incEdges.append(lane.split('_')[0])

            incEdges = np.unique(incEdges)
            incEdges = list(incEdges)
            for edge in edgesToClose:
                nodes = edge.split("-")
                edgeToCheck = nodes[1] + "-" + nodes[0]

                if edgeToCheck in incEdges:
                    incEdges.remove(edgeToCheck)
                    for IE in incEdges:
                        if result == "":
                            result = IE
                        else:
                            result = result + " " + IE
    return result

def generateRerouter():
    outXML = "reRouteTest.set.xml" #must have same name as outCSV
    outCSV = "reRouteTest.csv" #must have same name as outXML
    edgesToClose = ["n6-n7", "n8-n12"]
    minCloseLength = 50
    maxCloseLength = 150
    simLength = 1000

    
    root = ET.Element("rerouter", id= "generatedReRouter", edges=findIncomingEdges(edgesToClose))
    infoList = []
    for edge in edgesToClose:
        intervalLength = random.randrange(minCloseLength, maxCloseLength +1, 1)
        beginStep = random.randrange(0, simLength - intervalLength, 1)
        stopStep = beginStep + intervalLength
        intervalTag = ET.SubElement(root, "interval", begin = str(beginStep) , end= str(stopStep))
        ET.SubElement(intervalTag, "closingReroute",id=edge)

        d = {
            "edgeID" : edge,
            "beginStep" : beginStep,
            "stopStep" : stopStep
        }
        infoList.append(d)
    
    df = pd.DataFrame(infoList)
    df.to_csv(outCSV, index = False)
    tree = ET.ElementTree(root)
    tree.write(outXML)

def removeIntersectionNodes(listOfNodes):
    return [i for i in listOfNodes if listOfNodes.count(i) <= 1]


def get_options():
    optParser = optparse.OptionParser()
    optParser.add_option("--trips", type="int",
                         default=2000, dest="numberOfTrips",
                         help="Number of trips you would like.")
    optParser.add_option("--time", type="int",
                         default=1000, dest="runTime",
                         help="The latest time a car can spawn. Average cars pr. second is trips/time.")
    optParser.add_option("--edgeFile", type="string", dest="edgeFile", default="",
                         help="The file containing edges to spawn on. Should contain types that end in \"*_out\" and \"*_in\" to identify in and out lanes.")
    optParser.add_option("-o", type="string", dest="outFile", default="",
                         help="What you would like the trip file to be called. It will be placed the same place as the edgeFile.")  
    optParser.add_option("--song", action="store_true", dest="playSong", default=False,
                         help="Opens a success song so you can feel good.")
    optParser.add_option("--useProbFile", action="store_true", dest = "useProbFile", default=False, help="when used will use probabilities you define in inOutNodes.txt all remainding probility not set will be evenly distributed between undefined nodes in inOutNodes")
    optParser.add_option("--standard" , action = "store_true", dest="standard", default=False)
    optParser.add_option("--closeRoads", action = "store_true", dest="closeRoads",default=False, help="will generate a new reroute file and close all edges specefied in the generateReroute function" )
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



