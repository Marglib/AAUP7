#!/usr/bin/env python
from __future__ import absolute_import
from __future__ import print_function
from xml.dom import minidom
import os
import sys
import optparse
import subprocess
import csv
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
mainQuery = os.path.join(pathToModels, 'TNC.q')
mainModel = os.path.join(pathToModels, 'TNC_OneChoice.xml')
listOfCarTimeLists = []


def run(options):
    """execute the TraCI control loop"""
    #sys.stdout = open('stdoutFileTest', 'w')
    print("starting run")
    traci.init(options.port)
    step = 0
    ListOfCarsPlaceholder = []
    amountOfReroutes = 0
    totalRouteDif = 0
    newRoutes = []
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
    # 3 = small intersection
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

        #Every small intersection:
        tln1 = smartTL('n1','3')
        tln2 = smartTL('n2','3')
        tln4 = smartTL('n4','3')
        tln5 = smartTL('n5','3')
        tln6 = smartTL('n6','3')
        tln8 = smartTL('n8','3')
        tln9 = smartTL('n9','3')
        tln10 = smartTL('n10','3')
        tln12 = smartTL('n12','3')
        tln22 = smartTL('n22','3')
        tln24 = smartTL('n24','3')
        tln26 = smartTL('n26','3')
        tln29 = smartTL('n29','3')
        tln30 = smartTL('n30','3')
        tln32 = smartTL('n32','3')
        tln33 = smartTL('n33','3')

        ListOfTls = [tln1,tln2,tln3,tln4,tln5,tln6,tln7,tln8,tln9,tln10,tln11,tln12,tln13,tln14,tln15,tln16,tln22,tln24,tln26,tln28,tln29,tln30,tln31,tln32,tln33] 
        #ListOfTls = [tln3,tln7,tln11,tln13,tln14,tln15,tln16,tln28,tln31] 

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

    #------------------------------setup for closing roads------------------------------
    closingEdgeInfo = []
    if options.controller == "TrafficNetworkController":
        dom = minidom.parse(options.sumocfg)
        rerouterTag = dom.getElementsByTagName("additional-files")
        rerouteFileName = rerouterTag[0].getAttribute("value")
        nameForCSV = rerouteFileName.split(".")[0]
        
        with open("SUMOfiles/"+nameForCSV+".csv", 'r') as f:
            reader = csv.reader(f)
            closingEdgeInfo = list(reader)
    #--------------------------------END-------------------------------------------------
    print("Starting simulation expid=" + str(options.expid))

    while traci.simulation.getMinExpectedNumber() > 0:
        print(">>>simulation step: " + str(step))
                
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

        #THE DEFAULT CONTROLLER - doesnt do anything 
        if options.controller == "default":
            print(traci.trafficlight.getProgram('n3'))

        #THE MAIN CONTROLLER
        if (options.controller == "TrafficNetworkController"):
            #Update graph weights according to current traffic
            closedEdges = []
            CarsInNetworkList = traci.vehicle.getIDList()
            #if(step > 300 and step < 700):
            #closedEdges = [('n11','n56'), ('n56','n11'), ('n7','n56'), ('n56','n7')]
            if len(closingEdgeInfo) > 0:
                iterator = 0
                for line in closingEdgeInfo:
                    if iterator != 0:
                        #NOTE -20 is here to give info that road is closing 20 secs before
                        if int(line[0]) - 20 <= step and int(line[2]) >= step:
                            closedEdges.append(tuple(line[1].split("-")))
                    iterator += 1

            edges = list(networkGraph.edges)
            for i in range(0,len(edges)):
                networkGraph[edges[i][0]][edges[i][1]]['weight'] = get_weight(edges[i][0],edges[i][1], "travelTime")
            NodeIDs = networkGraph.nodes()      
        
            if len(CarsInNetworkList) > 0:
                Cars = []
                networkNodes = []
                update_time_on_edge(CarsInNetworkList)
                for id in NodeIDs:
                    networkNodes.append([id[1:], traci.junction.getPosition(id)])
                for car in CarsInNetworkList:
                    onClosed = route_contains_closed_edge(car,closedEdges)
                    Cars.append([car, get_route_nodes(car), get_time_on_edge(car), onClosed])
                
                if(step % 10 == 0):      
                    for car in newRoutes:
                        car.kill()              
                    newRoutes = modelCaller(mainModel, mainQuery, options.expid, step, Cars, networkGraph, networkNodes, closedEdges)

                for car in newRoutes:
                    car.update_route()
                    if car.rerouted:
                        amountOfReroutes += 1
                        totalRouteDif += car.routeChange
                        

                newRoutes = [car for car in newRoutes if not car.rerouted]
            
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

        if (amountOfReroutes > 0 and options.trafficlight == "smart"):
            print("Amount of reroutes so far: " + str(amountOfReroutes))
            print("Average route deviation: " + str(totalRouteDif/amountOfReroutes))
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
        return math.sqrt((pow(node1[0] - node2[0],2)) + (pow(node1[1] - node2[1],2))) #expects the nodes as a set of coordinates
    if(measure == "travelTime"):
        edge = node1 +"-"+ node2
        if(traci.edge.getLaneNumber(edge) == 1):
            return (13.73 * (traci.lane.getLength(edge + "_0") / 200)) + 1.54 * traci.edge.getLastStepVehicleNumber(edge) * (200/traci.lane.getLength(edge + "_0"))
        elif(traci.edge.getLaneNumber(edge) == 2):
            return (7.37 * (traci.lane.getLength(edge + "_0") / 100)) + 0.17 * traci.edge.getLastStepVehicleNumber(edge) * (100/traci.lane.getLength(edge + "_0"))
        elif(traci.edge.getLaneNumber(edge) == 3):
            return (6.46 * (traci.lane.getLength(edge + "_0") / 100)) + 0.44 * traci.edge.getLastStepVehicleNumber(edge) * (100/traci.lane.getLength(edge + "_0"))
        elif(traci.edge.getLaneNumber(edge) == 4):
            return (5.69  * (traci.lane.getLength(edge + "_0") / 100)) + 0.84 * traci.edge.getLastStepVehicleNumber(edge) * (100/traci.lane.getLength(edge + "_0"))
        
def route_contains_closed_edge(car, closedEdges):
    for edge in traci.vehicle.getRoute(car):
        if edge in nodestuples_to_edges(closedEdges):
            return 2
        else:
            return 0
  
def nodestuples_to_edges(nodes):
    edges = []
    for i in range(0, len(nodes)):
        edge = nodes[i][0] + "-" + nodes[i][1]
        edges.append(edge)
    return edges

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

    #Checks if the node is an internal node in one of the intersections
    for node in TupleOfNodes:
        if((node[0] == ":") == False):
            ListOfNodes.append(node)

    #Finds every connection in the edges and adds them as pairs of nodes
    for edge in tupleOfEdges:
        if((edge[0] == ":") == False):
            keyLoc = edge.find("-")
            #EdgeTuple = (edge[:keyLoc], edge[keyLoc + 1:], 
            #             float(get_weight(net.getNode(edge[:keyLoc]).getCoord(), net.getNode(edge[keyLoc + 1:]).getCoord(), "euclidian")))
            #This stuff initializes the weight to the euclidian distance between the nodes
            EdgeTuple = (edge[:keyLoc], edge[keyLoc + 1:], float(get_weight(edge[:keyLoc], edge[keyLoc + 1:], "travelTime"))) #Creates the weights according to traveltime
            ListOfEdges.append(EdgeTuple)

    G.add_nodes_from(ListOfNodes)
    G.add_weighted_edges_from(ListOfEdges)
    #nx.draw(G,with_labels=True) #These lines can be used to print the directed graph if needed
    #plt.savefig("graph.png")
    #plt.show()

    return G

def get_route_nodes(car):
    route = traci.vehicle.getRoute(car)
    route_nodes = []
    end_node = -1

    for edge in route:
        route_nodes.append(edge.split('-')[0][1:])
        end_node = edge.split('-')[1][1:]
    route_nodes.append(end_node)
    #pad with -1 to keep uppaal happy
    route_nodes += [-1] * (57 - len(route_nodes))  
    
    return route_nodes

def update_time_on_edge(cars):
    placeHolderList = listOfCarTimeLists.copy()
    for car in cars:
        hasEntry = False
        if listOfCarTimeLists:
            #print(len(placeHolderList))
            for elem in placeHolderList:
                if(elem[0] == car and elem[1] == traci.vehicle.getRoadID(car)):
                    elem[2] = elem[2] + 1
                    hasEntry = True
                elif(elem[0] == car):
                    hasEntry = True
                    elem[1] = traci.vehicle.getRoadID(car)
                    elem[2] = 0
            if(hasEntry == False):
                listOfCarTimeLists.append([car, 
                                    traci.vehicle.getRoadID(car), 
                                    0])
        else:
            listOfCarTimeLists.append([car, 
                                    traci.vehicle.getRoadID(car), 
                                    0])

def get_time_on_edge(car):
    for elem in listOfCarTimeLists:
        if(elem[0] == car and elem[1] == traci.vehicle.getRoadID(car)):
            return elem[2]

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