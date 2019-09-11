
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
pathToModels = os.path.join(rootDir,'Uppaal')
icavQuery = os.path.join(pathToModels, 'ICAV.q')
icavModel = os.path.join(pathToModels, 'IcavSpeed2.xml')


def run(options):
    """execute the TraCI control loop"""
    print("starting run")
    traci.init(options.port)
    step = 0

    print("Starting simulation expid=" + str(options.expid))
    
    while traci.simulation.getMinExpectedNumber() > 0:
        print(">>>simulation step: " + str(step))
                
        if options.controller == "StandardTrafficLight":
            ListOfCars = traci.vehicle.getIDList()

            for carID in ListOfCars:
                traci.vehicle.getSpeed(carID)


        if options.controller == "P7Controller":
            CarsInNetworkList = traci.vehicle.getIDList()

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
    emissioninfofile = "results/emission" + str(options.expid) + ".xml"
    tripinfofile = "results/tripinfo" + str(options.expid) + ".xml"
    sumoProcess = subprocess.Popen([sumoBinary, "-c", options.sumocfg, "--tripinfo-output", 
                                    tripinfofile, "--emission-output", emissioninfofile, "--remote-port", str(options.port)], stdout=sys.stdout,
                                   stderr=sys.stderr)
    run(options)
    sumoProcess.wait()