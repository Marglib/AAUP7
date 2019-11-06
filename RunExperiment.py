import sys
import os
import time
import string
import math
import optparse
from os.path import expanduser
from subprocess import Popen, PIPE, STDOUT, call
import pandas as pd
from CreateResultStats import create_statistics_file

def create_config_file(load):
    cfg = open("SUMOfiles/ConfigPlaceholder.sumocfg", "r+")
    str_cfg = cfg.read()
    cfg.close()

    toReplace = "//HOLDER_TRIP_FILE"
    value = "trip" + str(load) + "-2000.rou.xml"
    str_cfg = str.replace(str_cfg, toReplace, value, 1)

    cfgName = os.path.join('SUMOfiles/ConfigPlaceholderExp.sumocfg')
    text_file = open(cfgName, "w")
    text_file.write(str_cfg)
    text_file.close()


def create_result_files(pyv,expIDs,i):
    print("Creating result files for run:" + str(i))
    for j in range(0,4):
        sumoProcess = Popen(pyv +" ReadResultFile.py --tripinfofile tripinfo" + str(int(expIDs[j]) + i) + " --queuefile queueinfo"  + str(expIDs[j])+ str(i), stdout = PIPE, stderr = PIPE, shell=True)
        out, outerror = sumoProcess.communicate()
        sumoProcess.wait()


def run_experiment(pyv,load,runs,expIDs):
    for i in range(0,runs): 
        print("run: " + str(i))
        generateLoadProcess = Popen(pyv +" SUMOfiles/TripGenerator.py --trips " + str(load) + " --time 2000 --edgeFile SUMOfiles/MasterEdgeFile.edg.xml -o trip" +str(load)+"-2000 --useProbFile", stdout = PIPE, stderr = PIPE, shell=True)
        out, outerror = generateLoadProcess.communicate()
        create_config_file(load)

        print("Running simulation with TNC only:")
        sumoProcess = Popen(pyv +" Runnerscript.py --nogui --sumocfg SUMOfiles/ConfigPlaceholderExp.sumocfg --expid " + str(int(expIDs[0]) + i) + " --port 8873 --controller TrafficNetworkController", stdout = PIPE, stderr = PIPE, shell=True)
        out, outerror = sumoProcess.communicate()
        print(out,outerror)
        sumoProcess.wait()

        print("Running simulation with TNC and smart TL:")
        sumoProcess = Popen(pyv +" Runnerscript.py --nogui --sumocfg SUMOfiles/ConfigPlaceholderExp.sumocfg --expid " + str(int(expIDs[1]) + i) + " --port 8873 --controller TrafficNetworkController --trafficlight smart", stdout = PIPE, stderr = PIPE, shell=True)
        out, outerror = sumoProcess.communicate()
        print(out,outerror)
        sumoProcess.wait()

        print("Running simulation with smart TL only:")
        sumoProcess = Popen(pyv +" Runnerscript.py --nogui --sumocfg SUMOfiles/ConfigPlaceholderExp.sumocfg --expid " + str(int(expIDs[2]) + i) + " --port 8873 --trafficlight smart", stdout = PIPE, stderr = PIPE, shell=True)
        out, outerror = sumoProcess.communicate()
        print(out,outerror)
        sumoProcess.wait()

        print("Running simulation without any modifications:")
        sumoProcess = Popen(pyv +" Runnerscript.py --nogui --sumocfg SUMOfiles/ConfigPlaceholderExp.sumocfg --expid " + str(int(expIDs[3]) + i) + " --port 8873 ", stdout = PIPE, stderr = PIPE, shell=True)
        out, outerror = sumoProcess.communicate()
        print(out,outerror)
        sumoProcess.wait()

        print("Done with simulations")
        create_result_files(pyv,expIDs,i)

def extract_options(options):
    listOfExpIds = options.expIDs.split(",")
    return listOfExpIds

def get_options():
    optParser = optparse.OptionParser()
    optParser.add_option("--expIDs", type="string",
                         default="", dest="expIDs",
                         help="The experiment ids to run") #Example: [4000,4010,4020,4030] Currently has to be four (the four configs)
    optParser.add_option("--load", type="int",
                         default="0", dest="load",
                         help="The load used for the experiments") 
    optParser.add_option("--runs", type="int",
                         default="5", dest="runs",
                         help="The amount of runs needed") 
    optParser.add_option("--pythonV", type="string",
                         default="py", dest="pythonV",
                         help="The python command used to run. Example: py, python3 etc.")  
                                                  
    options, args = optParser.parse_args()
    return options
                  
# this is the main entry point of this script
if __name__ == "__main__":
    options = get_options()

    if(options.expIDs == ""):
        sys.exit("You have to pass some experiment IDS to start from")
    if(options.load == 0):
        sys.exit("You have to pass a load")
    
    listOfExpIds = extract_options(options)
    run_experiment(options.pythonV,options.load,options.runs,listOfExpIds)
    #print("Creating statistics for the experiment in the filename:" + options.filename)
