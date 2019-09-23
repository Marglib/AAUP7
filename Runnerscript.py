#!/usr/bin/env python
from __future__ import absolute_import
from __future__ import print_function
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
    EdgesInNetwork = traci.edge.getIDList()
    

    print("Starting simulation expid=" + str(options.expid))
    
    for edge in EdgesInNetwork:
        NrOfLanes = traci.edge.getLaneNumber(edge)
        for i in range(0,NrOfLanes):
            print("lane: " + edge + "_" + str(i) + " is connected with: " + str(traci.lane.getLinks(edge + "_" + str(i))))

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
    
            #Possible Routes for cars spawning on n1-n2 going to n3-n12:
            # ['n1-n2','n2-n3','n3-n12']
            # ['n1-n2','n2-n5','n5-n6','n6-n3','n3-n12']

            #Possible Routes for cars spawning on n1-n2 going to n2-n11:
            # ['n1-n2','n2-n3','n3-n12']
            # ['n1-n2','n2-n5','n5-n6','n6-n3','n3-n12']

            # ['n8-n9','n9-n10','n10-n6','n6-n7']      
            # ['n1-n2','n2-n5','n5-n6','n6-n7']
            # ['n4-n5','n5-n2','n2-n3','n3-n6','n6-n7']
            # ['n1-n2','n2-n3','n3-n6','n6-n7']
            # ['n1-n2','n2-n3','n3-n6','n6-n7']
            # ['n1-n2','n2-n3','n3-n6','n6-n7']
            # ['n1-n2','n2-n3','n3-n6','n6-n7']




        traci.simulationStep()
        step += 1    
    traci.close()
    sys.stdout.flush()

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