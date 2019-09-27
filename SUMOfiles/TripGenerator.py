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
import pandas as pd


routeFile = "RouteFileTemplate.rou.xml"

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
    
    print(fromEdges, toEdges)

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
        randomDep = ""
        randomDest = ""


        if options.useProbFile:
            df = pd.read_csv("inOutNodes.txt")
          
            isCorrect = verifyProbabilitys(df)
            fromNodes = [element.split("-")[0] for element in fromEdges]
            toNodes = [element.split("-")[1] for element in toEdges]
            for node in df.nodeName:
                if  not (node in fromNodes) and not (node in toNodes):
                    print("You gave an invalid node:", node )
                    return

            if not isCorrect:
                print("Something is wrong with the probabilities you gave")
                return

            ranInNumber = random.randrange(1,101,1)
            ranOutNumber = random.randrange(1,101,1)


            dfIn = df[df["inOut"] == "in"].sort_values("probability")
            dfOut = df[df["inOut"] == "out"].sort_values("probability")

            inNode = ""
            outNode = ""

            restProb = 101

            for index, row in dfIn.iterrows():
                if ranInNumber <= row["probability"]:
                    inNode = row.nodeName
                    break
                else:
                    restProb -= row.probability 
                    ranInNumber = random.randrange(1,restProb,1)
            
            restProb = 101
            for index, row in dfOut.iterrows():
                if ranOutNumber <= row["probability"]:
                    outNode = row.nodeName
                    break
                else:
                    restProb -= row.probability 
                    ranOutNumber = random.randrange(1,restProb,1)

            while True:
                #TODO: This should be optimized to a for loop!!
                randomDep = random.choice(fromEdges)
                randomDest = random.choice(toEdges)

                if randomDep.split("-")[0] == inNode and randomDest.split("-")[1] == outNode:
                    break
            
    
            value += "<trip id=\"" + str(i) + "\" depart=\"" + str(randomDepartures[i]) + "\" from=\"" + randomDep + "\" to=\"" + randomDest + "\"/>\n"

               

        if options.setRouteRestriction :

            leftOutNodes = ["n1", "n2", "n3"]
            rightOutNodes = ["n22", "n21", "n20"]

            while True:
                randomDep = random.choice(fromEdges)
                randomDest = random.choice(toEdges)

                if randomDep.split("-")[0] in leftOutNodes and randomDest.split("-")[1] in rightOutNodes:
                    break
                if randomDep.split("-")[0] in rightOutNodes and randomDest.split("-")[1] in leftOutNodes:
                    break
            
            value += "<trip id=\"" + str(i) + "\" depart=\"" + str(randomDepartures[i]) + "\" from=\"" + randomDep + "\" to=\"" + randomDest + "\"/>\n"
        
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
    optParser.add_option("--setRouteRestriction", action="store_true", dest="setRouteRestriction", default=False)
    optParser.add_option("--useProbFile", action="store_true", dest = "useProbFile", default=False)
    optParser.add_option("--standard" , action = "store_true", dest="standard", default=False)
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



