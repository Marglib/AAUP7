#!/usr/bin/env python
from __future__ import absolute_import
from __future__ import print_function
from xml.dom import minidom
import os
import sys
import optparse
import subprocess
import random
import time
import math
import copy
import networkx as nx
import matplotlib.pyplot as plt
from itertools import islice
#import pandas as pd

# we need to import python modules from the $SUMO_HOME/tools directory
try:
     tools = os.path.join(os.environ['SUMO_HOME'], "tools")
     sys.path.append(tools)
except:   
     sys.exit("please declare environment variable 'SUMO_HOME'")

from sumolib import checkBinary
import traci
import sumolib
from CallModel import modelCaller
from callStratego import cStratego

# the port used for communicating with your sumo instance
PORT = 8873

rootDir = os.path.abspath(os.getcwd())
pathToResults = os.path.join(rootDir,'results')
pathToModels = os.path.join(rootDir,'UppaalModels') + '\\'
icavQuery = os.path.join(pathToModels, 'TNC.q')
icavModel = os.path.join(pathToModels, 'TrafficNetworkController.xml')

#------------ STRATEGO STUFF --------
phaseWE = 0
phaseToNS = 1 # from here a transition to NS start
phaseNS = 3
phaseToEW = 4
#------------ END -------------

def run(options):
    """execute the TraCI control loop"""
    print("starting run")
    traci.init(options.port)
    step = 0
    ListOfCarsPlaceholder = []
    networkGraph = preprocess()    
    pathsToFind = 3

    #-------------------------------STRATEGO CONTROLLER STUFF---------------------------------------
    numDetectors = 8
    yellow = 8
    carsPassed = [0] * numDetectors
    carsJammed = [0] * numDetectors
    carsJammedMeters = [0] * numDetectors
    carsPassinge1 = [0] * numDetectors
    carsPassinge2 = [0] * numDetectors
    meanSpeed = [0] * numDetectors

    areDet = ["n43-n31_0_det", "n43-n31_1_det", "n48-n31_0_det", "n48-n31_1_det", "n32-n31_0_det", "n30-n31_0_det"]

    # meassuring performance per leg in intersection
    # left A1 down B1
    legs = ["A1","A2","B1","B2"]
    detLegH = {}
    detLegH["A1"] = [ "n43-n31_0_det", "n43-n31_1_det"] #These need a revisit
    detLegH["A2"] = [ "n48-n31_0_det", "n48-n31_1_det"]#These need a revisit
    detLegH["B1"] = [ "n32-n31_0_det"]#These need a revisit
    detLegH["B2"] = [ "n30-n31_0_det"] #These need a revisit
    jamMetLegH = {}
    jamMetLegH["A1"] = 0.0
    jamMetLegH["A2"] = 0.0
    jamMetLegH["B1"] = 0.0
    jamMetLegH["B2"] = 0.0
    jamCarLegH = {}
    jamCarLegH["A1"] = 0
    jamCarLegH["A2"] = 0
    jamCarLegH["B1"] = 0
    jamCarLegH["B2"] = 0
    
    totalJam = 0
    totalJamMeters = 0
    strategoMasterModel = os.path.join(pathToModels,'lowActivityMiniPro.xml')
    strategoMasterModelGreen = os.path.join(pathToModels,'highActivityPro.xml')
    strategoQuery = os.path.join(pathToModels,'StrategoQuery.q')
    strategoLearningMet = "3"
    strategoSuccRuns = "50"
    strategoGoodRuns = "50"
    strategoMaxRuns = "100"
    strategoEvalRuns = "10"
    strategoMaxIterations = "200"
    # we start with phase 1 where EW has green
    phase = phaseWE
    duration = yellow #phase duration from cross.net.xml   
    totaltimeNS = 0
    totaltimeEW = 0
    nextPhase = phaseNS
    strategoRunTime = 4
    phaseTimer = yellow
    strategoTimer = phaseTimer - strategoRunTime
    strategoMaxGreen = 120 #max time in green in one direction
    strategoGreenTimer = 0
    inYellow = True
    idTL = "n31"
    print("phase: " + str(phase))
    traci.trafficlights.setProgram(idTL, options.load)
    traci.trafficlights.setPhase(idTL, phase)
    minGreen = 10
    maxGreenEW,maxGreenNS = get_max_green(options)
    extTime = 3
    ext = 0
    timeInPhase = 0
    #-------------------------------END OF STRATEGO STUFF-------------------------------------------

    print("Starting simulation expid=" + str(options.expid))

    while traci.simulation.getMinExpectedNumber() > 0:
        print(">>>simulation step: " + str(step))
                
        #THE DEFAULT CONTROLLER - doesnt do anything 
        if options.controller == "default":
            CarsInNetworkList = traci.vehicle.getIDList()
            print(CarsInNetworkList)

        #THE MAIN CONTROLLER
        if options.controller == "TrafficNetworkController":
            CarsInNetworkList = traci.vehicle.getIDList()
            for car in CarsInNetworkList:
                print(traci.vehicle.getRoute(car))

        #Controllers used for experiments from here -------------------
        #Simple rerouting controller
        if options.controller == "SimpleRerouting":
            CarsInNetworkList = traci.vehicle.getIDList()  
            NewCars = []

            #Check if the car is new in the network - if it is, add it to the list of new cars
            for car in CarsInNetworkList:
                if(car not in ListOfCarsPlaceholder):
                    NewCars.append(car)

            #Stuff to do for new cars
            for car in NewCars:
                keyLocSource = traci.vehicle.getRoute(car)[0].find("-")
                keyLocTarget = traci.vehicle.getRoute(car)[(len(traci.vehicle.getRoute(car))-1)].find("-")
                sourceNode = traci.vehicle.getRoute(car)[0][:keyLocSource]
                targetNode = traci.vehicle.getRoute(car)[(len(traci.vehicle.getRoute(car))-1)][keyLocTarget + 1:]
                kShortestPaths = find_k_shortest_paths(networkGraph, sourceNode, targetNode, pathsToFind)
                print("Route: " + str(traci.vehicle.getRoute(car)))
                print("k shortest routes:")
                for path in kShortestPaths:
                    print(path)
                assign_random_new_route(car, kShortestPaths)

            ListOfCarsPlaceholder = list(CarsInNetworkList)


        #------------------------- BEGIN STRATEGO CONTROLLER -----------------------------
        if options.controller == "stratego":
            if strategoTimer == 0:
                if inYellow:
                    nextPhase,_,_ = cStratego(strategoMasterModel,strategoQuery,
                                              strategoLearningMet,strategoSuccRuns,
                                              strategoMaxRuns,strategoGoodRuns,
                                              strategoEvalRuns,strategoMaxIterations,
                                              options.expid,carsPassinge2, carsJammed,
                                              phase,duration,step,options)
                    duration = 10
                    inYellow = False
                    strategoGreenTimer = 0
                else:
                    nextPhase,_,_ =  cStratego(strategoMasterModelGreen,strategoQuery,
                                               strategoLearningMet,strategoSuccRuns,
                                               strategoMaxRuns,strategoGoodRuns,
                                               strategoEvalRuns,strategoMaxIterations,
                                               options.expid,carsPassinge2, carsJammed,
                                               phase,duration,step,options,greenModel=True,
                                               greenTimer=strategoGreenTimer)
                    if nextPhase == phase:
                        duration = 5
                    else:
                        nextPhase = phaseToNS
                        duration = yellow              
                if options.debug:
                    print("calling stratego \n  strategoTimer:" + str(strategoTimer) + \
                              ", currentPhase:"+ str(phase) + ", nextPhase:" \
                              + str(nextPhase) + ", duration:" + str(duration) + "\n" )
            if phaseTimer == 0:
                phase = nextPhase
                traci.trafficlights.setPhase(idTL,phase)
                totaltimeNS,totaltimeEW = sumtimes(totaltimeNS,totaltimeEW,phase,duration)
                print("setting phase:" + str(phase) + " with duration:" + str(duration))
                if phase == phaseToNS or phase == phaseToEW:
                    inYellow = True
                else:
                    inYellow = False
                if not inYellow:
                    traci.trafficlights.setPhaseDuration(idTL,duration)
                strategoTimer = duration - strategoRunTime
                phaseTimer = duration
            if options.debug:
                print("phase:" + str(phase) + ", nextphase:"+ str(nextPhase) + \
                      ", duration:" + str(duration)  + \
                      ", inYellow:" + str(inYellow) + \
                      ", strategoTimer:" + str(strategoTimer) + \
                      ", strategoGreenTimer:" + str(strategoGreenTimer) + \
                      ", phaseTimer:" + str(phaseTimer))
                print_dets_state("carsPassing",areDet,carsPassinge2)
                print_dets_state("carsJammed",areDet,carsJammed)

            strategoGreenTimer = strategoGreenTimer + 1   
            strategoTimer = strategoTimer - 1
            phaseTimer = phaseTimer - 1

            #---------------------------- END -----------------------------

        traci.simulationStep()
        step += 1    
    traci.close()
    sys.stdout.flush()

#----------------------- FUNCTIONS FOR STRATEGO ---------------------------
def get_max_green(options):
    if options.load == 'max':
        return 64,40
    if options.load == 'mid':
        return 54,26
    if options.load == 'low':
        return 36,20
    if options.load == '0':
        return 35,20
                      
def sumtimes(totaltimeNS,totaltimeEW,phase,duration):
    ttNS = 0
    ttWE = 0
    if phase == phaseNS:
        ttNS = totaltimeNS + duration
    if phase == phaseWE:
        ttWE = totaltimeEW + duration
    return ttNS, ttWE

def print_dets_state(msg,dets,res):
    print(msg + " detectors: " +str(dets) + " values: " + str(res))

#------------------------------- END -----------------------------------

def preprocess():
    network = configure_graph_from_network()
    return network

def get_weight(node1, node2, measure):
    if(measure == "euclidian"):
        #Find euclidian distance between nodes - node1[1][0] is the x coordinate for node1 as an example
        return math.sqrt((pow(node1[0] - node2[0],2)) + (pow(node1[1] - node2[1],2)))
    
    return 9999

def find_k_shortest_paths(G, source, target, k):
    return list(islice(nx.shortest_simple_paths(G, source, target, weight='weight'), k))

def assign_random_new_route(car, routes):
    newRouteNodes = random.choice(routes)
    newRoute = []
    edge = ""

    for i in range(0, len(newRouteNodes)-1):
        edge = str(newRouteNodes[i]) + "-" + str(newRouteNodes[i + 1])
        newRoute.append(edge)
    
    newRoute = tuple(newRoute)
    if(not len(newRouteNodes) <= 1):
        traci.vehicle.setRoute(car, newRoute)
        print("new route: " + str(newRoute))


def configure_graph_from_network():
    #Initialize empty list of nodes and edges (graph)
    G = nx.DiGraph()
    
    tupleOfEdges = traci.edge.getIDList() #SUMO returns a tuple
    TupleOfNodes = traci.junction.getIDList() #SUMO returns a tuple 
    ListOfNodes = []
    ListOfEdges = []
    EdgeTuple = ()
    NodeTuple = ()

    #Retrieving netfile from the sumo cfg
    mydoc = minidom.parse(options.sumocfg)
    netFile = ""
    netFileName = mydoc.getElementsByTagName('net-file')
    netFileDirectory = get_directory()
    for name in netFileName:
        netFile = name.attributes['value'].value

    net = sumolib.net.readNet(netFileDirectory + netFile)

    #Checks if the note is an internal node in one of the intersections
    for node in TupleOfNodes:
        if((node[0] == ":") == False):
            ListOfNodes.append(node)

    #Finds every connection in the edges and adds them as pairs of nodes
    for edge in tupleOfEdges:
        if((edge[0] == ":") == False):
            keyLoc = edge.find("-")
            EdgeTuple = (edge[:keyLoc], edge[keyLoc + 1:], float(get_weight(net.getNode(edge[:keyLoc]).getCoord(), net.getNode(edge[keyLoc + 1:]).getCoord(), "euclidian")))
            ListOfEdges.append(EdgeTuple)

    G.add_nodes_from(ListOfNodes)
    G.add_weighted_edges_from(ListOfEdges)
    #nx.draw(G,with_labels=True) #These lines can be used to print the directed graph if needed
    #plt.savefig("graph.png")
    #plt.show()

    return G

def get_directory():
    key = "/"
    keyLen = len(key)
    keyLoc = options.sumocfg.rfind(key)
    return options.sumocfg[:keyLoc+keyLen]        
def update_edgetime(edge):
    if traci.edge.getLastStepOccupancy(edge) > 0.3:
        traci.edge.adaptTraveltime(edge, 1*traci.edge.getLastStepOccupancy(edge))
    else:
        traci.edge.adaptTraveltime(edge, 0)

def debug_print(options, msg):
    if options.debug:
        print(msg)

def get_options():
    optParser = optparse.OptionParser()
    optParser.add_option("--nogui", action="store_true",
                         default=False, help="run the commandline version of sumo")
    optParser.add_option("--debug", action="store_true",
                         default=False, help="display debug information")
    optParser.add_option("--port", type="int", dest="port",default=8873)
    optParser.add_option("--expid", type="int", dest="expid")
    optParser.add_option("--sumocfg", type="string", dest="sumocfg",
                             default="data/nylandsvejPlain.sumocfg")
    optParser.add_option("--load", type="string", dest="load",default="0")
    optParser.add_option("--controller", type="string", dest="controller",default="default")    
    options, args = optParser.parse_args()
    return options

                  
# this is the main entry point of this script
if __name__ == "__main__":
    options = get_options()
    print("im am here: " + os.getcwd())
    if options.nogui:
        sumoBinary = checkBinary('sumo')
    else:
        sumoBinary = checkBinary('sumo-gui')
    # this is the normal way of using traci. sumo is started as a
    # subprocess and then the python script connects and runs
    emissioninfofile = "results/emission" + str(options.expid) + ".xml"
    tripinfofile = "results/tripinfo" + str(options.expid) + ".xml"
    queueinfofile = "results/queueinfo" + str(options.expid) + ".xml"
    sumoProcess = subprocess.Popen([sumoBinary, "-c", options.sumocfg, "--tripinfo-output", 
                                   tripinfofile, "--emission-output", emissioninfofile, "--queue-output", queueinfofile, 
                                   "--remote-port", str(options.port)], stdout=sys.stdout,
                                   stderr=sys.stderr)
    run(options)
    sumoProcess.wait()