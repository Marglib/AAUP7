#!/usr/bin/python
import sys
import os
import time
import string
import math
import VerifierPath as VP
from os.path import expanduser
from subprocess import Popen, PIPE, STDOUT
import traci

rootDir = os.path.abspath(os.getcwd())
pathToResults = os.path.join(rootDir,'results')
pathToModels = os.path.join(rootDir,'UppaalModels')

def runModel(com, args, query, simStep):
    query = "\"" + query + "\""
    f = Popen(com+args+query, stdout = PIPE, stderr = PIPE, shell=True)
    out, outerror = f.communicate()
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
    #f = os.popen(com+args+query) #Used for stratego
    #out = f.read()
    return out

def modelCaller(model,query,expId,simStep,cars, networkGraph, nodePositions):
    newModel = createModel(model,expId,simStep,cars, networkGraph, nodePositions)
    newQuery = createQuery(query,cars,nodePositions,expId)
    veri = VP.veri
    com = veri +  '   --learning-method ' + str(3) \
      + ' --good-runs ' + str(20) \
      + ' --total-runs ' + str(50) \
      + ' --runs-pr-state ' + str(70) \
      + ' --eval-runs ' + str(40) \
      + ' --max-iterations ' + str(30) \
      + ' --filter 0 -o 1 '
    args = "\"" + newModel + "\" "
    #newQuery = createQuery(query, expId, cars) Used for stratego
    out = runModel(com,args,newQuery, simStep)
    newRoutes = get_strategy(str(out), cars)
    #print(newRoutes)
    
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
    return newRoutes

def get_strategy(outStr, cars):
    newRoutes = []

    for i in range (0,len(cars)):
        strStart = "pid[" + str(int(cars[i][0]) + 1000) + "]"
        strEnd = "route[" + str(i) + "][48]"
        pid = str(int(cars[i][0]))
        numCar = str(i)
        strategyUnformated = get_sub_string(outStr,strStart,strEnd)
        strategyFormated = extract_strategy(strategyUnformated,numCar,pid)
        newRoutes.append(strategyFormated)
 
    return newRoutes

def extract_strategy(strat,numCar,pid):
    endOfStr = "\\n"
    listOfValues = []
    reroutes = []
    rerouteTuple = ()

    for i in range(0,48):
        value = ""
        curr = "route[" + numCar + "][" + str(i) + "]:\\n[0]:"
        currLen = len(curr)
        start = strat.find(curr)
        end = strat.find(endOfStr, start+currLen)
        value = strat[start+currLen:end]
        listOfValues.append(value)

    print("VALUES FOR CAR: " + numCar)
    for i in range(0,len(listOfValues)):
        if(len(listOfValues[i]) > 7):
            print("ROUTE NODE " + str(i) + "=" + listOfValues[i])
            rerouteTuple = (pid,i,clean_strategy(listOfValues[i]))
            reroutes.append(rerouteTuple)
    
    return reroutes

def clean_strategy(stratString):
    delim = "(0,0)"
    timestep = 0
    node = 0

    start = stratString.find(delim)
    split = stratString[delim:].split(",")
    timestep = split[0][-1:]
    node = split[1][:-1]
    print(timestep,node)

    return (timestep,node)

def get_sub_string(outStr,key,end):
    keyLoc = outStr.find(key)
    endOfKey = outStr.find(end, keyLoc)
    value = outStr[keyLoc:endOfKey + 20]
    return value

def replace_car_strings(str_model,cars,nodePositions):
    toReplace = "//HOLDER_NUMBER_OF_CARS"
    value = "const int N = " + str(len(cars)) + ";\n"
    str_model = str.replace(str_model, toReplace, value, 1)

    toReplace = "//HOLDER_CAR_PID"
    value = "{"
    for i in range (0,len(cars)):
        value += str(int(cars[i][0]) + 1000) + ","
    value = value[:-1]
    value += "};"
    str_model = str.replace(str_model, toReplace, value, 1)

    #Car routes are assumed to be set up as an array of the node numbers of the route
    toReplace = "//HOLDER_CAR_ROUTE"
    value = "{"
    for i in range (0,len(cars)):
        value += "\n{"
        for j in range (0, len(nodePositions)):
            value += str(cars[i][1][j]) + ","
        value = value[:-1]
        value += "},"
    value = value[:-1]
    value += "};"
    str_model = str.replace(str_model, toReplace, value, 1)

    return str_model

def replace_node_strings(str_model,nodePositions,cars):
    toReplace = "//HOLDER_NODE_POSITIONS"
    value = "const int nodePositions[" + str(len(nodePositions)) + "][3] = {"
    for i in range (0,len(nodePositions)):
        value += "{" + str(nodePositions[i][0]) + "," + str(int(nodePositions[i][1][0])) + "," + str(int(nodePositions[i][1][1])) + "},"
        if(i % 20 == 0):
            value += "\n"
    value = value[:-1]
    value += "};"
    str_model = str.replace(str_model, toReplace, value, 1)

    toReplace = "//HOLDER_NUMBER_OF_NODES"
    value = str(len(nodePositions)) + ";"
    str_model = str.replace(str_model, toReplace, value, 1)

    toReplace = "//HOLDER_CURRENT_START_NODE"
    value = "{"
    for i in range(0,len(cars)):
        routeCar = traci.vehicle.getRoute(cars[i][0])
        routeIndex = traci.vehicle.getRouteIndex(cars[i][0])
        edge = routeCar[routeIndex]
        keyLoc = edge.find("-")
        value += str(edge[1:keyLoc]) + ","
    value = value[:-1]
    value += "};"
    str_model = str.replace(str_model, toReplace, value, 1)

    return str_model

def replace_edge_strings(str_model,networkGraph):
    toReplace = "//HOLDER_NUMBER_OF_EDGES"
    value = str(len(networkGraph.edges())) + ";"
    str_model = str.replace(str_model, toReplace, value, 1)

    toReplace = "//HOLDER_EDGES"
    edges = list(networkGraph.edges)
    value = "int networkEdges[" + str(len(edges)) + "][5] = {"
    for i in range(0,len(edges)):
        nrOfLanes = traci.edge.getLaneNumber(edges[i][0] + "-" + edges[i][1])
        weight = networkGraph.get_edge_data(edges[i][0], edges[i][1])
        value += "{" + str(edges[i][0][1:]) + "," +  str(edges[i][1][1:]) + "," + str(nrOfLanes) + "," + str(int(weight.get('weight'))) + "," + str(len(traci.edge.getLastStepVehicleIDs(edges[i][0] + "-" + edges[i][1]))) + "},"
        if(i % 20 == 0):
            value += "\n"
    value = value[:-1]
    value += "};"
    str_model = str.replace(str_model, toReplace, value, 1)

    return str_model

def replace_time_passed_current_edge(str_model, cars):
    toReplace = "//HOLDER_TIME_PASSED"
    value = "{"
    for car in cars:
        time_on_edge = car[2]
        value += str(time_on_edge)
        value += ","
    value = value [:-1]
    value += "};"
    str_model = str.replace(str_model, toReplace, value, 1)

    return str_model

def createModel(master_model,expId,simStep,cars,networkGraph,nodePositions):
    fo = open(master_model, "r+")
    str_model = fo.read()
    fo.close()

    str_model = replace_car_strings(str_model,cars,nodePositions)
    str_model = replace_node_strings(str_model,nodePositions,cars)
    str_model = replace_edge_strings(str_model,networkGraph)
    str_model = replace_time_passed_current_edge(str_model,cars)    

    modelName = os.path.join(pathToModels, 'tempModel' + str(expId) + '.xml')
    text_file = open(modelName, "w")
    text_file.write(str_model)
    text_file.close()
    return modelName

def createQuery(master_query,cars,nodePositions,expId):
    fo = open(master_query, "r+")
    str_query = fo.read()
    fo.close()

    toReplace = "//HOLDER_QUERY"
    value = ""
    for i in range(0,len(cars)):
        value += " pid[" + str(int(cars[i][0]) + 1000) + "],"
        for j in range(0,len(nodePositions)):
            value += " route[" + str(i) + "][" + str(j) + "],"
    value = value[:-1]
    str_query = str.replace(str_query, toReplace, value, 1)

    queryName = rootDir + "/UppaalModels/TNCtempQuery" + str(expId) + '.q'
    text_file = open(queryName, "w")
    text_file.write(str_query)
    text_file.close()
    return queryName
