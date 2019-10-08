from xml.dom import minidom
import os
import sys
import optparse
import subprocess
import random
import time
import math
import copy

try:
     tools = os.path.join(os.environ['SUMO_HOME'], "tools")
     sys.path.append(tools)
except:   
     sys.exit("please declare environment variable 'SUMO_HOME'")

from sumolib import checkBinary
import traci
import sumolib
from callStratego import cStratego

class smartTL:
    def __init__(self, tlID, numDetectors, detectors, phases, programID, yellowTime, initPhase):
        self.tlID = tlID
        self.numDetectors = numDetectors
        self.detectors = detectors
        self.phases = phases
        self.programID = programID
        self.yellow = yellowTime

        #Setting phaseWE, phaseToNS, phaseNS and phaseToEW depending on what the programID is
        self.phaseWE, self.phaseToNS, self.phaseNS, self.phaseToEW = get_programID_phases(self)

        #Initial values for important variables
        self.duration = yellowTime
        self.phase = initPhase
        self.inYellow = True
        self.nextPhase = phases[self.phase+1]
        self.strategoRunTime = 4
        self.phaseTimer = self.yellow
        self.strategoTimer = self.phaseTimer - self.strategoRunTime
        self.strategoMaxGreen = 120 #max time in green in one direction
        self.strategoGreenTimer = 0
        self.carsPassed = [0] * self.numDetectors
        self.carsJammed = [0] * self.numDetectors
        self.carsJammedMeters = [0] * self.numDetectors
        self.carsPassinge2 = [0] * self.numDetectors
        self.meanSpeed = [0] * self.numDetectors

    def update_tl_state(self,strategoMasterModel,strategoMasterModelGreen,strategoQuery,strategoLearningMet,strategoSuccRuns,strategoMaxRuns,strategoGoodRuns,strategoEvalRuns,strategoMaxIterations,expid,options,step):
        setPhase = False
        setDurr = False
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
                    self.nextPhase = self.phaseToNS
                    self.duration = self.yellow              
        if self.phaseTimer == 0:
            self.phase = self.nextPhase
            setPhase = True
            if self.phase == self.phaseToNS or self.phase == self.phaseToEW:
                self.inYellow = True
            else:
                self.inYellow = False
            if not self.inYellow:
                setDurr = True
            self.strategoTimer = self.duration - self.strategoRunTime
            self.phaseTimer = self.duration

        self.strategoGreenTimer = self.strategoGreenTimer + 1   
        self.strategoTimer = self.strategoTimer - 1
        self.phaseTimer = self.phaseTimer - 1

        return setPhase, setDurr
                                                

    def get_max_green(self):
        if self.programID == 'max':
            return 64,40
        if self.programID == 'mid':
            return 54,26
        if self.programID == 'low':
            return 36,20
        if self.programID == '0':
            return 54,26

    def get_programID_phases(self):
        if(self.programID == '0'):
            return 0, 1, 3, 4

    def print_dets_state(msg,dets,res):
        print(msg + " detectors: " +str(dets) + " values: " + str(res))