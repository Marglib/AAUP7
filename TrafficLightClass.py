from xml.dom import minidom
import os
import sys
import optparse
import subprocess
import random
import time
import math
import copy
import traci
import sumolib
from callStratego import cStratego

class smartTL:
    def __init__(self, id, numDetectors, detectors, phases, programID, yellowTime,initPhase):
        self.id = id
        self.numDetectors = numDetectors
        self.detectors = detectors
        self.phases = phases
        self.programID = programID
        self.yellow = yellowTime

        self.duration = yellowTime
        self.phase = initPhase
        self.inYellow = True
        self.nextPhase = phases[phase+1]
        self.strategoRunTime = 4
        self.phaseTimer = yellow
        self.strategoTimer = phaseTimer - strategoRunTime
        self.strategoMaxGreen = 120 #max time in green in one direction
        self.strategoGreenTimer = 0
        self.carsPassed = carsPassed = [0] * numDetectors
        self.carsJammed = carsJammed = [0] * numDetectors
        self.carsJammedMeters = carsJammedMeters = [0] * numDetectors
        self.carsPassinge2 = carsPassinge2 = [0] * numDetectors
        self.meanSpeed = meanSpeed = [0] * numDetectors

    phaseWE = 0
    phaseToNS = 1 # from here a transition to NS start
    phaseNS = 3
    phaseToEW = 4


def change_(self,strategoMasterModel,strategoMasterModelGreen,strategoQuery,strategoLearningMet,strategoSuccRuns,strategoMaxRuns,strategoGoodRuns,strategoEvalRuns,strategoMaxIterations,expid,options,step):
    if self.strategoTimer == 0:
        if self.inYellow:
            self.nextPhase,_,_ = cStratego(strategoMasterModel,strategoQuery,
                                        strategoLearningMet,strategoSuccRuns,
                                        strategoMaxRuns,strategoGoodRuns,
                                        strategoEvalRuns,strategoMaxIterations,
                                        expid,self.carsPassinge2, self.carsJammed,
                                        self.phase,self.duration,step,options)
            self.duration = 10
            self.inYellow = False
            self.strategoGreenTimer = 0
        else:
            self.nextPhase,_,_ =  cStratego(strategoMasterModelGreen,strategoQuery,
                                        strategoLearningMet,strategoSuccRuns,
                                        strategoMaxRuns,strategoGoodRuns,
                                        strategoEvalRuns,strategoMaxIterations,
                                        options.expid,self.carsPassinge2, self.carsJammed,
                                        self.phase,self.duration,step,options,greenModel=True,
                                        greenTimer=self.strategoGreenTimer)
            if self.nextPhase == self.phase:
                self.duration = 5
            else:
                self.nextPhase = phaseToNS
                self.duration = self.yellow              
    if self.phaseTimer == 0:
        self.phase = self.nextPhase
        traci.trafficlights.setPhase(idTL,phase)
        print("setting phase:" + str(phase) + " with duration:" + str(duration))
        if phase == phaseToNS or phase == phaseToEW:
            self.inYellow = True
        else:
            self.inYellow = False
        if not self.inYellow:
            traci.trafficlights.setPhaseDuration(idTL,duration)
        self.strategoTimer = self.duration - self.strategoRunTime
        self.phaseTimer = self.duration

    self.strategoGreenTimer = self.strategoGreenTimer + 1   
    self.strategoTimer = self.strategoTimer - 1
    self.phaseTimer = self.phaseTimer - 1
                                              

def get_max_green(programID):
    if programID == 'max':
        return 64,40
    if programID == 'mid':
        return 54,26
    if programID == 'low':
        return 36,20
    if programID == '0':
        return 54,26

def print_dets_state(msg,dets,res):
    print(msg + " detectors: " +str(dets) + " values: " + str(res))