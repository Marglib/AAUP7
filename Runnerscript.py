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
#import pandas as pd

# we need to import python modules from the $SUMO_HOME/tools directory
try:
     tools = os.path.join(os.environ['SUMO_HOME'], "tools")
     sys.path.append(tools)
except:   
     sys.exit("please declare environment variable 'SUMO_HOME'")

from sumolib import checkBinary
import traci
from CallModel import modelCaller

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
    ListOfNodes, ListOfEdges = preprocess()    

    print("Starting simulation expid=" + str(options.expid))

    while traci.simulation.getMinExpectedNumber() > 0:
        print(">>>simulation step: " + str(step))
                
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
                print(traci.vehicle.getRoute(car))


            ListOfCarsPlaceholder = list(CarsInNetworkList)

        traci.simulationStep()
        step += 1    
    traci.close()
    sys.stdout.flush()


def preprocess():
    get_external_edges()
    ListOfNodes, ListOfEdges = configure_graph_from_network()

def get_external_edges():
    edgeList = []
    EdgeTuple = traci.edge.getIDList()

    for edge in EdgeTuple:
        if((edge[0] == ":") == False):
            edgeList.append(edge)

def configure_graph_from_network():
    #Initialize empty list of nodes and edges (graph)
    
    TupleOfNodes = traci.junction.getIDList()
    ListOfNodes = []
    ListOfEdges = []
    EdgeTuple = ()

    for node in TupleOfNodes:
        if((node[0] == ":") == False):
            ListOfNodes.append(node)

    #Retrieving netfile from the sumo cfg
    mydoc = minidom.parse(options.sumocfg)
    netFile = ""
    netFileName = mydoc.getElementsByTagName('net-file')
    netFileDirectory = get_directory()
    for name in netFileName:
        netFile = name.attributes['value'].value

    netFile = minidom.parse(netFileDirectory + netFile)

    connections = tuple(netFile.getElementsByTagName('connection'))
    for conn in connections:
       fromStr = str(conn.attributes['from'].value)
       toStr = str(conn.attributes['to'].value)

       if(((fromStr[0] == ":") == False) and ((toStr[0] == ":") == False)):
           keyLoc = conn.attributes['from'].value.find("-")
           EdgeTuple = (conn.attributes['from'].value[:keyLoc], conn.attributes['from'].value[keyLoc + 1:])
           ListOfEdges.append(EdgeTuple)

           keyLoc = conn.attributes['to'].value.find("-")
           EdgeTuple = (conn.attributes['to'].value[:keyLoc], conn.attributes['to'].value[keyLoc + 1:])
           ListOfEdges.append(EdgeTuple)

    ListOfEdges = list(set(ListOfEdges))
    return ListOfNodes, ListOfEdges

def get_directory():
    key = "/"
    keyLen = len(key)
    keyLoc = options.sumocfg.rfind(key)
    return options.sumocfg[:keyLoc+keyLen]

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
    optParser.add_option("--load", type="string", dest="load",default="reserve")
    optParser.add_option("--controller", type="string", dest="controller",default="static")    
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
    #emissioninfofile = "results/emission" + str(options.expid) + ".xml"
    #tripinfofile = "results/tripinfo" + str(options.expid) + ".xml"
    #sumoProcess = subprocess.Popen([sumoBinary, "-c", options.sumocfg, "--tripinfo-output", 
     #                               tripinfofile, "--emission-output", emissioninfofile, "--remote-port", str(options.port)], stdout=sys.stdout,
      #                             stderr=sys.stderr)
    sumoProcess = subprocess.Popen([sumoBinary, "-c", options.sumocfg, "--remote-port", str(options.port)], stdout=sys.stdout,
                                   stderr=sys.stderr)
    run(options)
    sumoProcess.wait()