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
import copy
import pdb
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

#------------setup for basicConrtoller without uppal-----------------------
currentCarInformation = {}
currentEdgeInformation = {}
listOfEdges = []
tryRuns = 50
#------------END-------------------------

def callSimulator(networkGraph, listOfEdges, currStep):
    bestTry = {}
    bestTryRun = 0
    fewestTotalCongestedEdges = float("inf")   #we start at highest possible so the first sim is always smaller than this
    for i in range(0, tryRuns):
        setupInformation(listOfEdges, currStep)
        #TODO change so we stop trying this branch in the tree if it does not look like it is getting better
        simData, totalCongestedEdges = simulateTrafficFlow(currentCarInformation, currentEdgeInformation, currStep, 100)
        ttt = getTotalTravelTime(simData)
        changeRoutes(simData, networkGraph)
        #print(totalCongestedEdges, fewestTotalCongestedEdges)
        if(totalCongestedEdges < fewestTotalCongestedEdges): #fewestTotalCongestedEdges  decides which try is best
            fewestTotalCongestedEdges = totalCongestedEdges
            bestTry = copy.deepcopy(currentCarInformation)
            bestTryRun = i
    setRoutesToBestTry(bestTry)
    print(bestTryRun)

def getTotalTravelTime (simData):
    result = 0
    #car : [edge, step, route] 
    initialCarData = simData[1][0]
    initialEdgeData = simData[1][1]
    for car in initialCarData:
        travelTimeForCar = 0
        currentEdge = initialCarData[car][0]
        stepOfEntry = initialCarData[car][1]
        carRoute = initialCarData[car][2]

        firstEdgeTT = initialEdgeData[currentEdge][0] - stepOfEntry
        travelTimeForCar += firstEdgeTT

        nextStepToLookUp = firstEdgeTT
        foundCurrentEdge = False
        for edge in carRoute:
            if edge == currentEdge:
                foundCurrentEdge = True
            
            if foundCurrentEdge:
                nextEdge = getNextEdgeForCar(currentEdge, initialCarData[car][2])
                currentEdge = nextEdge
                if nextEdge != "Goal" and nextEdge != "Error":
                    if nextStepToLookUp in simData:
                        edgeData = simData[nextStepToLookUp][1]
                        edgeTT = edgeData[nextEdge][0]
                        nextStepToLookUp += edgeTT
                        travelTimeForCar += edgeTT
                    else:
                        #just look on edged from initial data as we are out of bounds for our simulation
                        edgeData = initialEdgeData
                        edgeTT = edgeData[nextEdge][0]
                        nextStepToLookUp += edgeTT
                        travelTimeForCar += edgeTT
        result += travelTimeForCar
    return result

def changeRoutes(simData, networkGraph):
    for key in simData:
        #[carData, edgeData, congestedEdges, currentStep + i]
        simCarData = simData[key][0]
        simEdgeData = simData[key][1]
        simCongestedEdges = simData[key][2]
        simStep = simData[key][3]
        for edge in simCongestedEdges:
            carsAtRisk = simEdgeData[edge][1]
            if len(carsAtRisk) > 0:     
                carsAtRisk = random.sample(carsAtRisk, int(len(carsAtRisk)/2)) #TODO NEED BETTER WAY TO CHOOSE
                for car in carsAtRisk:
                    newRoute = makeNewRoute(edge, networkGraph, car) #TODO NEED BETTER WAY TO REROUTE
                    if newRoute != "":
                        try:
                            traci.vehicle.setRoute(car, newRoute)
                        except:
                            pass


def setupInformation(listOfEdges, step):
    for edge in listOfEdges:
        if edge in currentEdgeInformation:
            currentEdgeInformation.update({edge : [traci.edge.getTraveltime(edge), [x for x in traci.edge.getLastStepVehicleIDs(edge)]]})
        else:
            currentEdgeInformation[edge] = [traci.edge.getTraveltime(edge), [x for x in traci.edge.getLastStepVehicleIDs(edge)]]
        
        carsOnEdge = traci.edge.getLastStepVehicleIDs(edge)
        for car in carsOnEdge:
            route = traci.vehicle.getRoute(car)
            
            if car in currentCarInformation:
                if currentCarInformation[car][0] == edge:
                    pass
                else:
                    currentCarInformation.update({car : [edge, step, route] })
            else:
                currentCarInformation[car] = [edge, step, route]

def simulateTrafficFlow(carData, edgeData, currentStep ,horizon):
    simulationData = {}
    totalCongestedEdges = 0

    for i in range(1, horizon):
        congestedEdges = []
        keysToDelete = []

        for carKey in carData:
            singleCarData = carData[carKey]
            currentEdge = singleCarData[0]
            enterTime = singleCarData[1]
            travelTimeForEdge = edgeData[currentEdge][0]
            timeOnEdge = (currentStep - enterTime) + i
            
            if timeOnEdge >= travelTimeForEdge:
                nextEdge = getNextEdgeForCar(singleCarData[0], singleCarData[2])

                if nextEdge == "Goal":
                   keysToDelete.append(carKey)
                elif nextEdge == "Error":
                    print("-an error occured-" * 200)
                    keysToDelete.append(carKey)
                else:
                    carData.update({carKey : [nextEdge, currentStep + i, singleCarData[2]]})
                    newCarsOnCurrentEdge = edgeData[currentEdge][1]
                    if carKey in newCarsOnCurrentEdge:
                        newCarsOnCurrentEdge.remove(carKey)
                    newCarsOnNewEdge = edgeData[nextEdge][1]
                    newCarsOnNewEdge.append(carKey)
                   
                    edgeData.update ({currentEdge : [edgeData[currentEdge][0] -  getTravelTimeCoefficient(currentEdge), newCarsOnCurrentEdge]}) 
                    edgeData.update({nextEdge : [ edgeData[nextEdge][0] + getTravelTimeCoefficient(nextEdge), newCarsOnNewEdge]})
                    if  isEdgeCongested( edgeData[nextEdge], nextEdge):
                        if nextEdge not in congestedEdges:
                            congestedEdges.append(nextEdge)
                            #Used to see which simulation is best
                            totalCongestedEdges += 1
        for key in keysToDelete:
            del carData[key]

        simulationData[i] = [copy.deepcopy(carData), copy.deepcopy(edgeData), congestedEdges.copy(), currentStep + i]

    return simulationData, totalCongestedEdges
                        
            
def isEdgeCongested(singleEdgeData, edgeID):
    value = 10
    if traci.edge.getLaneNumber(edgeID) >= 2:
        value = 20
    if len(singleEdgeData[1]) > value:
        return True
    else:
        return False


def getNextEdgeForCar(currentEdge, route):
    for i in range(0,len(route)):
        if route[i] == currentEdge:
            if i <= (len(route) - 2):
                return route[i+1]
            else:
                return "Goal"
    return "Error"

def makeNewRoute(edgeToAvoid, networkGraph, car):
    if(len(traci.vehicle.getRoute(car)) > 0):
        if(not(traci.vehicle.getRoadID(car)[0] == ':')):
            k = 5
            oldRoute = traci.vehicle.getRoute(car)
            currEdge = traci.vehicle.getRoadID(car)
            nextJunction = traci.vehicle.getRoadID(car).split("-")[1]
            sourceNode = nextJunction
            targetNode = oldRoute[len(oldRoute)-1].split("-")[1]

            kShortestPaths = find_k_shortest_paths(networkGraph, sourceNode, targetNode, k) #5 shortest paths

            routeGood = False
            i = 0
            candidateRoute = []
            while(routeGood == False):
                if i <= len(kShortestPaths) - 1: 
                    candidateRoute = nodesToRouteEdges(kShortestPaths[i], currEdge)
                    if(edgeToAvoid in candidateRoute):
                        i = i + 1
                    else:
                        routeGood = True
                else:
                    break
                
            if(not len(candidateRoute) <= 1):
                return tuple(candidateRoute)
            else:
                return ""
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

def getCongestedEdges(edgeDict):
    congestedEdges = []
    for key in edgeDict:
        if edgeDict[key][1] > 5:
            congestedEdges.append(key)
    return congestedEdges

def find_k_shortest_paths(G, source, target, k):
    return list(islice(nx.shortest_simple_paths(G, source, target, weight='weight'), k))

def setRoutesToBestTry(bestTryCarData):
    i = 0
    j = 0
    for car in bestTryCarData:
        if(traci.vehicle.getRoute(car) != bestTryCarData[car][2]):
            try:
                print("--------------------------------------------------------------------------------------")
                print(car)
                print(traci.vehicle.getRoute(car))
                print(bestTryCarData[car][2])
                i = i  + 1
                traci.vehicle.setRoute(car, bestTryCarData[car][2])
            except:
                j = j + 1
                print(traci.vehicle.getRoute(car))
                print(bestTryCarData[car][2])
                print(traci.vehicle.getRoadID(car))
                pass
    print(i>j)

#data from https://github.com/Marglib/AAUP7/blob/criticalDensity/Results/travelTime_per_car_with_regression_80th_percentile.png
def getTravelTimeCoefficient(edgeID):
    numLanes = traci.edge.getLaneNumber(edgeID)

    if numLanes == 2:  
        return 0.171021
    elif numLanes == 3:
        return 0.4368
    elif numLanes == 4:        
        return 0.8380
    else:        
        return 1.5354
                



