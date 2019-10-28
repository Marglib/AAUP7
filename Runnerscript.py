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
    #Declare all the classes - program correspond as following: 
    # 0 = vertical large intersection
    # 1 = horizontal large intersection
    # 2 = large center intersection
    if options.trafficlight == "smart":
        #Every vertical traffic light:
        tln3 = smartTL('n3','0')
        tln7 = smartTL('n7','0')
        tln11 = smartTL('n11','0')
        tln31 = smartTL('n31','0')
        
        #The large center traffic light:
        tln15 = smartTL('n15','2')
        
        #Every horizontal intersection:
        tln13 = smartTL('n13','1')
        tln14 = smartTL('n14','1')
        tln16 = smartTL('n16','1')
        tln28 = smartTL('n28','1') 

        ListOfTls = [tln3,tln7,tln11,tln13,tln14,tln15,tln16,tln28,tln31] 

        #Set all phases and program ids
        for tls in ListOfTls:
            traci.trafficlight.setProgram(tls.tlID, tls.programID)
            traci.trafficlight.setPhase(tls.tlID, tls.phase)
    #-------------------------------END TLS-------------------------------------------
 
    #-------------------- Setup list of all edges in network ----------------------
    tupleOfEdges = traci.edge.getIDList() #SUMO returns a tuple
    listOfEdges = []

    for edge in tupleOfEdges:
        if((edge[0] == ":") == False):
            listOfEdges.append(edge)
    #-------------------- END -------------------------------------------------------
    print("Starting simulation expid=" + str(options.expid))

    #------------setup for basicConrtoller without uppal-----------------------
    currentCarInformation = {}
    currentEdgeInformation = {}
    #------------END-------------------------

    while traci.simulation.getMinExpectedNumber() > 0:
        print(">>>simulation step: " + str(step))

        if options.controller == "basicMessoController":
            dataForStratego = []
            for edge in listOfEdges:
                carsOnEdge = traci.edge.getLastStepVehicleIDs(edge)
                adaptedTT = traci.edge.getTraveltime(edge)
                carRoutes = []

                for car in carsOnEdge:
                    route = traci.vehicle.getRoute(car)
                    carRoutes.append(route)

                dataForStratego.append([edge, adaptedTT, carsOnEdge, carRoutes])


        #basic controller without uppal
        if options.controller == "Basic":
            
            # ---------------setup/update data -----------------------------------
            for edge in listOfEdges:
                currentEdgeInformation[edge] = [traci.edge.getTraveltime(edge), traci.edge.getLastStepVehicleIDs(edge)]

                carsOnEdge = traci.edge.getLastStepVehicleIDs(edge)
                for car in carsOnEdge:
                    route = traci.vehicle.getRoute(car)
                    
                    if car in currentCarInformation:
                        if currentCarInformation[car][0] == edge:
                            pass
                        else:
                            currentCarInformation[car] = [edge, step, traci.vehicle.getRoute(car)]
                    else:
                        currentCarInformation[car] = [edge, step, traci.vehicle.getRoute(car)]

            #-----------------------END--------------------------------------------------

            simulateTrafficFlow(currentCarInformation, currentCarInformation, step, 200)





        """
            #collect current information from traci
            dataForController = []
            for edge in listOfEdges:
                carsOnEdge = traci.edge.getLastStepVehicleIDs(edge)
                TT = traci.edge.getTraveltime(edge)
                carRoutes = []

                for car in carsOnEdge:
                    route = traci.vehicle.getRoute(car)
                    carRoutes.append(route)

                dataForController.append([edge, TT, carsOnEdge, carRoutes])

            #find congested edges
            congestedEdges = getCongestedEdges(dataForController)

            #find all cars that will hit a congested edge later on the route
            carsToReRoute = findCarsToReroute(dataForController, congestedEdges)

            newRoutesForCars = findNewRoutesForCars(dataForController, carsToReRoute)
            """



        
        #THE DEFAULT CONTROLLER - doesnt do anything 
        if options.controller == "default":
            CarsInNetworkList = traci.vehicle.getIDList()  
            for car in CarsInNetworkList:
                if(len(traci.vehicle.getRoute(car)) > 0): 
                    if(not(traci.vehicle.getRoadID(car)[0] == ':')):
                        newRoute = makeNewRoute('n8-n12', networkGraph, car)
                        if(not (newRoute == "")):
                            traci.vehicle.setRoute(car, newRoute)

        #THE MAIN CONTROLLER
        if options.controller == "TrafficNetworkController":
            #------------------------- SMART TRAFFIC LIGHT -----------------------------
            if options.trafficlight == "smart":
                with concurrent.futures.ThreadPoolExecutor(max_workers=len(ListOfTls)) as executor:
                    for tls in ListOfTls:
                        future = executor.submit(tls.update_tl_state,strategoMasterModel,strategoMasterModelGreen,strategoQuery,
                                                            strategoLearningMet,strategoSuccRuns,
                                                            strategoMaxRuns,strategoGoodRuns,
                                                            strategoEvalRuns,strategoMaxIterations,
                                                            options.expid,step)
                        future.result()

            #---------------------------- END -----------------------------

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
    optParser.add_option("--trafficlight", type="string", dest="trafficlight",default="traditional")
    options, args = optParser.parse_args()
    return options

def getCongestedEdges(edgeDict):
    congestedEdges = []
    for key in edgeDict:
        if edgeDict[key][1] > 5:
            congestedEdges.append(key)
    return congestedEdges

def findCarsToReroute(data, congestedEdges):
    carsToReRoute = []
    for line in data:
        routes = line[3]
        cars = line[2]
        for i in range(0, len(line[2])):
            foundCurrentProgress = False
            for edge in routes[i]:
                if not foundCurrentProgress:
                    #check how far along the car is on it's route
                    if edge == line[0]: 
                        foundCurrentProgress = True
                else:
                    if edge in congestedEdges:
                        carsToReRoute.append([cars[i], routes[i], line[0]])
                        break
    return carsToReRoute

def simulateTrafficFlow(carData, edgeData, currentStep ,horizon):
    
    for i in range (1, horizon):
        for carKey in carData:
            singleCarData = carData[carKey]
            currentEdge = singleCarData[0]
            enterTime = singleCarData[1]
            travelTimeForEdge = edgeData[currentEdge][0]
            timeOnEdge = (currentStep - enterTime) + i
            
            if timeOnEdge >= travelTimeForEdge:
                nextEdge = getNextEdgeForCar(singleCarData[0], singleCarData[2])

def getNextEdgeForCar(currentEdge, route):
    for i in range(0,len(route)):
        if route[i] == currentEdge:
            if i > (len(route) - 2):
                return route[i+1]
            else:
                return "Goal"
    return "Error"

def findNewRoutesForCars(data, carsAtRisk):

    return 0

def makeNewRoute(edgeToAvoid, networkGraph, car):
    if(not(traci.vehicle.getRoadID(car)[0] == ':')):
        oldRoute = traci.vehicle.getRoute(car)
        currEdge = traci.vehicle.getRoadID(car)
        nextJunction = traci.vehicle.getRoadID(car).split("-")[1]
        sourceNode = nextJunction
        targetNode = oldRoute[len(oldRoute)-1].split("-")[1]

        kShortestPaths = find_k_shortest_paths(networkGraph, sourceNode, targetNode, 5) #5 shortest paths

        routeGood = False
        i = 0
        candidateRoute = []
        while(routeGood == False):
            candidateRoute = nodesToRouteEdges(kShortestPaths[i], currEdge)
            if(edgeToAvoid in candidateRoute):
                i = i + 1
                pass
            else:
                routeGood = True
        
        
        if(not len(candidateRoute) <= 1):
            return tuple(candidateRoute)
        else:
            return ""
    else:
        return ""
    
     
def nodesToRouteEdges(nodes, currEdge):
    edges = []
    edges.append(currEdge)
    for i in range(0, len(nodes)-1):
        edge = str(nodes[i]) + "-" + str(nodes[i + 1])
        edges.append(edge)
    return edges  


                  
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

