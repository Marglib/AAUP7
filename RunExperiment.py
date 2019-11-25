import sys
import os
import time
import string
import math
import optparse
from os.path import expanduser
from subprocess import Popen, PIPE, STDOUT, call

def create_netfile_copy(uid):
    netfile = open("AAUP7/SUMOfiles/MasterNetFile.net.xml","r+")
    str_net = netfile.read()
    netfile.close()
    netfile_name = os.path.join("AAUP7/SUMOfiles/ExperimentSUMOfiles/MasterNetFile" + str(uid) +".net.xml")
    text_file = open(netfile_name,"w")
    text_file.write(str_net)
    text_file.close()

def create_edge_file_copy(uid):
    edgefile = open("AAUP7/SUMOfiles/MasterEdgeFile.edg.xml","r+")
    str_edges = edgefile.read()
    edgefile.close()
    edgefile_name = os.path.join("AAUP7/SUMOfiles/ExperimentSUMOfiles/MasterEdgeFile" + str(uid) +".edg.xml")
    text_file = open(edgefile_name,"w")
    text_file.write(str_edges)
    text_file.close()

def create_config_file(load,uid):
    cfg = open("AAUP7/SUMOfiles/ConfigPlaceholder.sumocfg", "r+")
    str_cfg = cfg.read()
    cfg.close()

    create_netfile_copy(uid)

    toReplace = "//HOLDER_TRIP_FILE"
    value = "/user/d704e19/experiments/AAUP7/SUMOfiles/ExperimentSUMOfiles/trip" + str(load) + "-2000-" + str(uid) +".rou.xml"
    str_cfg = str.replace(str_cfg, toReplace, value, 1)

    toReplace = "//HOLDER_NET_FILE"
    value = "/user/d704e19/experiments/AAUP7/SUMOfiles/ExperimentSUMOfiles/MasterNetFile" + str(uid) +".net.xml"
    str_cfg = str.replace(str_cfg, toReplace, value, 1)

    cfgName = os.path.join("AAUP7/SUMOfiles/ExperimentSUMOfiles/ConfigPlaceholderExp" + str(uid) +".sumocfg")
    text_file = open(cfgName, "w")
    text_file.write(str_cfg)
    text_file.close()


def create_result_files(pyv,expIDs,i):
    print("Creating result files for run:" + str(i))
    for j in range(0,4):
        sumoProcess = Popen(pyv +" AAUP7/ReadResultFile.py --tripinfofile tripinfo" + str(int(expIDs[j]) + i) + " --queuefile queueinfo"  + str(expIDs[j])+ str(i), stdout = PIPE, stderr = PIPE, shell=True)
        out, outerror = sumoProcess.communicate()
        sumoProcess.wait()


def run_experiment(pyv,load,runs,expIDs,uid,port):
    for i in range(0,runs): 
        print("run: " + str(i))
        create_config_file(load,uid)
        create_edge_file_copy(uid)

        generateLoadProcess = Popen(pyv +" AAUP7/SUMOfiles/TripGenerator.py --trips " + str(load) + " --time 2000 --edgeFile AAUP7/SUMOfiles/ExperimentSUMOfiles/MasterEdgeFile"+ str(uid) +".edg.xml -o trip" +str(load)+"-2000-"+ str(uid) + " --useProbFile", stdout = PIPE, stderr = PIPE, shell=True)
        out, outerror = generateLoadProcess.communicate()

        print("Running simulation with TNC only:")
        sumoProcess = Popen(pyv +" AAUP7/Runnerscript.py --nogui --sumocfg AAUP7/SUMOfiles/ExperimentSUMOfiles/ConfigPlaceholderExp" + str(uid) +".sumocfg --expid " + str(int(expIDs[0]) + i) + " --port "+ str(port) +" --controller TrafficNetworkController", stdout = PIPE, stderr = PIPE, shell=True)
        out, outerror = sumoProcess.communicate()
        print(out,outerror)
        sumoProcess.wait()

        print("Running simulation with TNC and smart TL:")
        sumoProcess = Popen(pyv +" AAUP7/Runnerscript.py --nogui --sumocfg AAUP7/SUMOfiles/ExperimentSUMOfiles/ConfigPlaceholderExp" + str(uid) +".sumocfg --expid " + str(int(expIDs[1]) + i) + " --port " + str(port) + " --controller TrafficNetworkController --trafficlight smart", stdout = PIPE, stderr = PIPE, shell=True)
        out, outerror = sumoProcess.communicate()
        print(out,outerror)
        sumoProcess.wait()

        print("Running simulation with smart TL only:")
        sumoProcess = Popen(pyv +" AAUP7/Runnerscript.py --nogui --sumocfg AAUP7/SUMOfiles/ExperimentSUMOfiles/ConfigPlaceholderExp" + str(uid) +".sumocfg --expid " + str(int(expIDs[2]) + i) + " --port " + str(port) + " --trafficlight smart", stdout = PIPE, stderr = PIPE, shell=True)
        out, outerror = sumoProcess.communicate()
        print(out,outerror)
        sumoProcess.wait()

        print("Running simulation without any modifications:")
        sumoProcess = Popen(pyv +" AAUP7/Runnerscript.py --nogui --sumocfg AAUP7/SUMOfiles/ExperimentSUMOfiles/ConfigPlaceholderExp" + str(uid) +".sumocfg --expid " + str(int(expIDs[3]) + i) + " --port " + str(port), stdout = PIPE, stderr = PIPE, shell=True)
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
                         help="The experiment ids to run. Should be 4.") #Example: 4000,4010,4020,4030 Currently has to be four (the four configs)
    optParser.add_option("--load", type="int",
                         default="0", dest="load",
                         help="The load used for the experiments") 
    optParser.add_option("--runs", type="int",
                         default="5", dest="runs",
                         help="The amount of runs needed") 
    optParser.add_option("--pythonV", type="string",
                         default="py", dest="pythonV",
                         help="The python command used to run. Example: py, python3 etc.")  
    optParser.add_option("--uid", type="int",
                         default="0", dest="uid",
                         help="The unique ID for this specific experiment. Used to search for the CFG")      
    optParser.add_option("--port", type="int",
                         default="0", dest="port",
                         help="Port to be used for the experiment") 
                                                  
    options, args = optParser.parse_args()
    return options
                  
# this is the main entry point of this script
if __name__ == "__main__":
    options = get_options()
    
    if(options.expIDs == ""):
        sys.exit("You have to pass some experiment IDS to start from")
    if(options.load == 0):
        sys.exit("You have to pass a load")
    if(options.uid == 0):
        sys.exit("You have to pass a unique ID for the experiment")
    if(options.port == 0):
        sys.exit("You have to give a port for the experiment")
    
    listOfExpIds = extract_options(options)
    run_experiment(options.pythonV, options.load, options.runs, listOfExpIds, options.uid, options.port)
    #print("Creating statistics for the experiment in the filename:" + options.filename)
