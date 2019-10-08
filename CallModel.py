#!/usr/bin/python
import sys
import os
import time
import string
import math
import VerifierPath as VP
from os.path import expanduser
from subprocess import Popen, PIPE, STDOUT

rootDir = os.path.abspath(os.getcwd())
pathToResults = os.path.join(rootDir,'results')
pathToModels = os.path.join(rootDir,'UppaalModels')

def runModel(com, args, query, simStep):
    query = "\"" + query + "\""
    f = Popen(com+args+query, stdout = PIPE, stderr = PIPE, shell=True)
    out, outerror = f.communicate()
    #print(outerror)
    """

    out_string = str(out)
    log_text = out_string.split('--')

    log_file = open("LogFile.txt", "a")
    cpu_log_file = open("CPU-LogFile.txt", "a")

    log_file.write("simStep: " + str(simStep))
    cpu_log_file.write("simStep: " + str(simStep))

    for line in log_text:
        if "Throughput" not in line:
            log_file.write("\n" + str(line))
            if "CPU" in line:
                cpu_log_file.write("\n" + str(line))


    log_file.write("\n\n\n")
    cpu_log_file.write("\n\n\n")

    cpu_log_file.close()
    log_file.close()
    """
    #f = os.popen(com+args+query) Used for stratego
    #out = f.read()
    return outerror

def modelCaller(model,query,expId,simStep,cars, network_nodes):
    newModel = createModel(model,expId,simStep,cars, network_nodes)
    veri = VP.veri
    com = veri +  ' -o 1 -t 0 -u '
    args = "\"" + newModel + "\" "
    #newQuery = createQuery(query, expId, cars) Used for stratego
    out = runModel(com,args,query, simStep)
    print(out)
    #carSpeeds = getStrategy(out, cars)
    
    #' -o 1 -t 0 '
    """
    ' --learning-method ' + str(3) \
      + ' --good-runs ' + str(20) \
      + ' --total-runs ' + str(20) \
      + ' --runs-pr-state ' + str(30) \
      + ' --eval-runs ' + str(10) \
      + ' --max-iterations ' + str(10) \
      + ' --filter 0 '
    """
    
    #return carSpeeds
    print("Done")

def getStrategy(outStr, cars):
    carSpeeds = []

    for i in range (0,len(cars)):
        strStart = "Cars(" + str(i) + ").newSpeed"
        #carSpeeds.append(float(strategoGetSubString(outStr,strStart)))

    print("\nNew speeds:" + str(carSpeeds) +"\n")
 
    return carSpeeds

def strategoGetSubString(outStr, key):
    speedLoc = "(1,"
    key_len = len(key)
    found = outStr.find(key)
    start = found + key_len + 11
    end = outStr.find(speedLoc, start) + len(speedLoc) + 3
    value = (outStr[start:end]).strip()
    return value[:-1]

def standardGetSubString(outStr, key):
    delim = "="
    key_len = len(key)
    outStr = str(outStr)
    found = outStr.rfind(key)
    start = found + key_len
    end = outStr.find(delim, start) + len(delim) + 3
    value = (outStr[start:end]).strip()
    return value[1:]

def createModel(master_model,expId,simStep,cars,network_nodes):
    fo = open(master_model, "r+")
    str_model = fo.read()
    fo.close()

    toReplace = "//HOLDER_NUMBER_OF_CARS"
    value = "const int N = " + str(len(cars)) + ";\n"
    str_model = str.replace(str_model, toReplace, value, 1)

    toReplace = "//HOLDER_CAR_PID"
    value = "{"
    for i in range (0,len(cars)):
        value += str(cars[i][0][-1:]) + ","
    value = value[:-1]
    value += "};"
    str_model = str.replace(str_model, toReplace, value, 1)

    #Car routes are assumed to be set up as an array of the node numbers of the route
    toReplace = "//HOLDER_CAR_ROUTE"
    value = "{"
    for i in range (0,len(cars)):
        value += "{"
        for j in range (0, network_nodes):
            value += str(cars[i][1][j]) + ","
        value = value[:-1]
        value += "},"
    value = value[:-1]
    value += "};"
    str_model = str.replace(str_model, toReplace, value, 1)

    modelName = os.path.join(pathToModels, 'tempModel' + str(expId) + '.xml')
    text_file = open(modelName, "w")
    text_file.write(str_model)
    text_file.close()
    return modelName

