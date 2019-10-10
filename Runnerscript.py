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
import concurrent.futures
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
from TrafficLightClass import smartTL

# the port used for communicating with your sumo instance
PORT = 8873

rootDir = os.path.abspath(os.getcwd())
pathToResults = os.path.join(rootDir,'results')
pathToModels = os.path.join(rootDir,'UppaalModels')
icavQuery = os.path.join(pathToModels, 'TNC.q')
icavModel = os.path.join(pathToModels, 'TrafficNetworkController.xml')


def run(options):
    """execute the TraCI control loop"""
    print("starting run")
    traci.init(options.port)
    step = 0
    ListOfCarsPlaceholder = []
    networkGraph = preprocess()    
    pathsToFind = 3

    laneList = list(reversed(traci.trafficlight.getControlledLanes("n31")))
    print(laneList)
    
    #Detectors for each intersection declared here
    n11det = ["n7-n11_0_det","n7-n11_1_det","n12-n11_0_det","n46-n11_0_det","n46-n11_1_det","n10-n31_0_det"]
    n31det = ["n43-n31_0_det", "n43-n31_1_det", "n32-n31_0_det", "n48-n31_1_det", "n48-n31_0_det", "n30-n31_0_det"]

    #-------------------------------STRATEGO info---------------------------------------
    strategoMasterModel = os.path.join(pathToModels,'lowActivityMiniPro.xml')
    strategoMasterModelGreen = os.path.join(pathToModels,'highActivityPro.xml')
    strategoQuery = os.path.join(pathToModels,'StrategoQuery.q')
    strategoLearningMet = "3"
    strategoSuccRuns = "20"
    strategoGoodRuns = "40"
    strategoMaxRuns = "20"
    strategoEvalRuns = "10"
    strategoMaxIterations = "150"
    #---------------------------- END ------------------------------

    #-------------------- CLASS tls from here ----------------------
    #Declare all the classes
    tln11 = smartTL('n11',6,n11det,6,'0',8,0)
    tln31 = smartTL('n31',6,n31det,6,'0',8,0)
    ListOfTls = [tln31, tln11]

    #Set all phases and program ids
    for tls in ListOfTls:
        traci.trafficlight.setProgram(tls.tlID, tls.programID)
        traci.trafficlight.setPhase(tls.tlID, tls.phase)
    #-------------------------------END TLS-------------------------------------------

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
            with concurrent.futures.ThreadPoolExecutor(max_workers=len(ListOfTls)) as executor:
                for tls in ListOfTls:
                    future = executor.submit(tls.update_tl_state,strategoMasterModel,strategoMasterModelGreen,strategoQuery,
                                                        strategoLearningMet,strategoSuccRuns,
                                                        strategoMaxRuns,strategoGoodRuns,
                                                        strategoEvalRuns,strategoMaxIterations,
                                                        options.expid,step)
                    future.result()

            #---------------------------- END -----------------------------

        traci.simulationStep()
        step += 1    
    traci.close()
    sys.stdout.flush()

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