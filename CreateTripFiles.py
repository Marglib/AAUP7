import os
import sys
import random
import optparse
import subprocess
import math
from subprocess import Popen, PIPE, STDOUT, call

listOfLoads = [3000,3500,4000,4500,5000]
index = 0

def generate_tripfile(trips, ID):
    generateLoadProcess = Popen("py -3 SUMOfiles/TripGenerator.py --trips " + str(trips) + " --time 2000 --edgeFile SUMOfiles/MasterEdgeFile.edg.xml -o FiftyOfEachExp/None/tripFile" + str(ID) + " --useProbFile", stdout = PIPE, stderr = PIPE, shell=True)
    out, outerror = generateLoadProcess.communicate()
    create_config_file(ID)
    print(out, outerror)
    generateLoadProcess.wait()

def create_config_file(ID):
    cfg = open("SUMOfiles/ConfigPlaceholder.sumocfg", "r+")
    str_cfg = cfg.read()
    cfg.close()

    create_netfile_copy(ID)

    toReplace = "//HOLDER_TRIP_FILE"
    value = "tripFile" + str(ID) +".rou.xml"
    str_cfg = str.replace(str_cfg, toReplace, value, 1)

    toReplace = "//HOLDER_NET_FILE"
    value = "MasterNetFile" + str(ID) +".net.xml"
    str_cfg = str.replace(str_cfg, toReplace, value, 1)

    cfgName = os.path.join("SUMOfiles/FiftyOfEachExp/None/config" + str(ID) +".sumocfg")
    text_file = open(cfgName, "w")
    text_file.write(str_cfg)
    text_file.close()


def create_netfile_copy(ID):
    netfile = open("SUMOfiles/MasterNetFile.net.xml","r+")
    str_net = netfile.read()
    netfile.close()
    netfile_name = os.path.join("SUMOfiles/FiftyOfEachExp/None/MasterNetFile" + str(ID) +".net.xml")
    text_file = open(netfile_name,"w")
    text_file.write(str_net)
    text_file.close()



for j in range(0,len(listOfLoads)):
    for i in range(0,50):
        generate_tripfile(listOfLoads[j], index)
        index += 1

    