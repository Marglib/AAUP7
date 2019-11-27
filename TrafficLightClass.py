from xml.dom import minidom
import os
import sys
import optparse
import subprocess
import random
import time
import math
import copy
import re

try:
     tools = "/user/d704e19/sumo/tools"
     sys.path.append(tools)
except:   
     sys.exit("please declare environment variable 'SUMO_HOME'")

from sumolib import checkBinary
import traci
import sumolib
from callStratego import cStratego

class smartTL:
    def __init__(self,tlID,programID,yellowTime=8,initPhase=0,radius=200):
        self.tlID = tlID
        self.programID = programID
        self.yellow = yellowTime
        self.binaryPhases,self.binaryPhasesDecimal,self.binaryPhaseIndices,self.yellowOnlyPhases,self.nrOfSignals = self.get_phases_for_program()
        #if(self.tlID == 'n15'):
        #    print(self.binaryPhases,self.binaryPhasesDecimal,self.binaryPhaseIndices,self.yellowOnlyPhases,self.nrOfSignals)

        #Initial values for important variables
        self.duration = yellowTime
        self.phase = initPhase
        self.inYellow = True
        self.nextPhase = self.phase + 1
        self.strategoRunTime = 4
        self.phaseTimer = self.yellow
        self.strategoTimer = self.phaseTimer - self.strategoRunTime
        self.strategoMaxGreen = 120 #max time in green in one direction
        self.strategoGreenTimer = 0
        self.radius = radius

    def update_tl_state(self,strategoMasterModel,strategoMasterModelGreen,strategoQuery,strategoLearningMet,strategoSuccRuns,strategoMaxRuns,strategoGoodRuns,strategoEvalRuns,strategoMaxIterations,expid,step):
        #Old Functions: self.get_lane_func(traci.lane.getLastStepVehicleNumber, self.tlID)[::-1]
        carsAreal = self.get_cars_areal_in_radius(self.tlID, self.radius)[::-1]
        carsJammed = self.get_lane_func(traci.lane.getLastStepHaltingNumber, self.tlID)[::-1]
        phasePlaceholder = 0
<<<<<<< HEAD
	#if(self.tlID == 'n15'):
=======
        #if(self.tlID == 'n15'):
>>>>>>> UppaalModel
        #    print(carsAreal)
        #    print(carsJammed)
        
        if self.strategoTimer == 0:
            if self.inYellow:
                phasePlaceholder,_,_ = cStratego(strategoMasterModel,strategoQuery,
                                            strategoLearningMet,strategoSuccRuns,
                                            strategoMaxRuns,strategoGoodRuns,
                                            strategoEvalRuns,strategoMaxIterations,
                                            expid,carsAreal,carsJammed,
                                            self.phase,self.duration,step,self.nrOfSignals,
                                            self.binaryPhasesDecimal,self.binaryPhases,self.binaryPhaseIndices,self.tlID,self.yellow)
                if(phasePlaceholder != -1):
                    self.nextPhase = phasePlaceholder
                else:
                    print("No strategy found")
<<<<<<< HEAD
                
=======

>>>>>>> UppaalModel
                self.duration = 10
                self.inYellow = False
                self.strategoGreenTimer = 0
            else:
                phasePlaceholder,_,_ =  cStratego(strategoMasterModelGreen,strategoQuery,
                                            strategoLearningMet,strategoSuccRuns,
                                            strategoMaxRuns,strategoGoodRuns,
                                            strategoEvalRuns,strategoMaxIterations,
                                            expid,carsAreal,carsJammed,
                                            self.phase,self.duration,step,self.nrOfSignals,
                                            self.binaryPhasesDecimal,self.binaryPhases,self.binaryPhaseIndices,self.tlID,self.yellow,
                                            greenModel=True,
                                            greenTimer=self.strategoGreenTimer)
                if phasePlaceholder != -1:
                    self.nextPhase = phasePlaceholder
<<<<<<< HEAD
                else:
                    print("No strategy was found")
=======
                else: 
                    print("No strategy found")  

>>>>>>> UppaalModel
                if self.nextPhase == self.phase:
                    self.duration = 5
                else:
                    self.nextPhase = self.phase +1 
                    self.duration = self.yellow   
                        
        if self.phaseTimer == 0:
            self.phase = self.nextPhase
            traci.trafficlight.setPhase(self.tlID,self.phase)
            if (self.phase in self.yellowOnlyPhases):
                self.inYellow = True
            else:
                self.inYellow = False
            if not self.inYellow:
                traci.trafficlight.setPhaseDuration(self.tlID,self.duration)
            self.strategoTimer = self.duration - self.strategoRunTime
            self.phaseTimer = self.duration

        self.strategoGreenTimer = self.strategoGreenTimer + 1   
        self.strategoTimer = self.strategoTimer - 1
        self.phaseTimer = self.phaseTimer - 1

    def get_phases_for_program(self):
        phaseDefiniton = traci.trafficlight.getCompleteRedYellowGreenDefinition(self.tlID)
        phaseDefiniton = str(phaseDefiniton)
        phaseList = []
        connectionsList = []

        #Finding all the relevant phases
        for match in re.finditer('state',phaseDefiniton):
            startOfPhase = match.end() + 2
            endOfPhase = phaseDefiniton.find(',',match.end()) -1
            phaseList.append(phaseDefiniton[startOfPhase:endOfPhase])

        #Creating the amount of connections from each signal
        links = traci.trafficlight.getControlledLinks(self.tlID)
        lastLane = ""
        currentConnections = 1
        for i in range(0,len(links)):
            currLane = links[i][0][0]
            if(currLane == lastLane):
                currentConnections = currentConnections + 1
            elif(lastLane != ""):
                connectionsList.append(currentConnections)
                currentConnections = 1
            if(i == len(links) -1):
                connectionsList.append(currentConnections)

            lastLane = currLane
        
        #Creating the binary phases and their indices
        binaryPhases = []
        binaryPhaseIndices = []
        for i in range(0, len(phaseList)):
            index = 0
            binaryPhase = ""
            for j in range (0, len(connectionsList)):
                signalConf = phaseList[i][index:index + connectionsList[j]]
                if('G' in signalConf or 'g' in signalConf):
                    binaryPhase += "1"
                else:
                    binaryPhase += "0"
                index = index + connectionsList[j]
            binaryPhases.append(binaryPhase)
            binaryPhaseIndices.append(i)

        #Removing any phases that dont have any green. These are not interesting for the model
        binaryToDecimalPhases = []
        yellowOnlyPhases = []
        for i in range(0,len(binaryPhases)):
            if(int(binaryPhases[i],2) != 0):
                binaryToDecimalPhases.append(int(binaryPhases[i],2))
            else:    
                binaryPhaseIndices.remove(i)
                yellowOnlyPhases.append(i)

        #print(len(connectionsList))
        return binaryPhases, binaryToDecimalPhases, binaryPhaseIndices, yellowOnlyPhases, len(connectionsList)
                                                 
    def get_lane_func(self, func, tlID):
        controlledLanes = self.get_controlled_lanes(tlID)
        res = [0] * len(controlledLanes)

        for i in range (0,len(controlledLanes)):
            res[i] = func(controlledLanes[i])
        return res
    
    def get_controlled_lanes(self, tlID):
        controlledLanesWithDupes = traci.trafficlight.getControlledLanes(tlID)
        uniqueControlledLanes = []

        for lane in controlledLanesWithDupes:
            if lane not in uniqueControlledLanes:
                uniqueControlledLanes.append(lane)

        return uniqueControlledLanes
    
    def get_cars_areal_in_radius(self, tlID, radius):
        controlledLanes = self.get_controlled_lanes(tlID)

        jammedOppositeCars = self.get_opposite_cars_jammed(controlledLanes)

        res = [0] * len(controlledLanes)
        junctionPosition = traci.junction.getPosition(tlID)
        for i in range (0, len(controlledLanes)):
            vehicleIDs = traci.lane.getLastStepVehicleIDs(controlledLanes[i])
            numberOfCars = 0
            for vehicle in vehicleIDs:
                vehiclePosition = traci.vehicle.getPosition(vehicle)
                distance = math.sqrt(sum([(a - b) ** 2 for a, b in zip(junctionPosition, vehiclePosition)]))
                if(distance < radius):
                    numberOfCars = numberOfCars + 1
            
            value = numberOfCars - jammedOppositeCars[i]
            if(jammedOppositeCars[i] >= 6):
                res[i] = max(value,0)
            else:
                res[i] = numberOfCars
        
        #print(res)
        return res

    def get_opposite_cars_jammed(self, controlledLanes):
        links = traci.trafficlight.getControlledLinks(self.tlID)
        dictOfLanes = {}
        jammedCars = []

        for i in range(0,len(links)):
            currLane = links[i][0][0]
            outLane = links[i][0][1]
            if currLane in dictOfLanes:
                dictOfLanes[currLane].append(outLane)
            else: 
                dictOfLanes[currLane] = [outLane]
        
        for lane in controlledLanes:
            jammed = []
            averageJam = 0
            for link in dictOfLanes[lane]:
                jammed.append(traci.lane.getLastStepHaltingNumber(link))
            
            averageJam = sum(jammed) / len(jammed)
            jammedCars.append(int(round(averageJam)))

        return jammedCars


                
            

