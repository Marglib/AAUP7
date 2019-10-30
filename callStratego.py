#!/usr/bin/python
import sys
import os
import time
import string
import math
import VerifierPath as VP
from os.path import expanduser

home = expanduser("~")
rootDir = os.path.abspath(os.getcwd())
pathToResults = os.path.join(rootDir,'results')
pathToModels = os.path.join(rootDir,'UppaalModels')

def runStratego(com, args, query):
    #print('calling stratego with command: ' + com + args + query) 
    start_time = time.time()
    f = os.popen(com+args+query)
    out = f.read()
    total_time = time.time() - start_time
    return total_time, out

# Verifying formula 2 at line 9
#  -- Formula is satisfied.
# signal[1]:
# [0]: (0,0) (0,0) (0,1) (0,1) (30,1) (30,0) (30,0) (90,0)
# signal[2]:
# [0]: (0,0) (0,0) (0,1) (0,1) (30,1) (30,0) (30,0) (90,0)
# signal[3]:
# [0]: (0,0) (0,0) (0,1) (0,0) (36,0) (36,0) (36,1) (36,1) (76,1) (76,0) (76,0) (90,0)
# signal[4]:
# [0]: (0,0) (0,0) (0,1) (0,0) (36,0) (36,0) (36,1) (36,1) (76,1) (76,0) (76,0) (90,0)


def myGetSubString(mstr, key, greenModel):
    #print("myGetSubstring"+mstr)      
    delim = "\n" #Start of next signal line

    key_len = len(key)
    found = mstr.find(key)
    if found == -1:
        return "no-strategy"        
    else:
        start = found + key_len     
        end = mstr.find(delim, start+5) +1 #To make sure we search the next line for linebreak 
        return mstr[start:end]
    
def getTuple(mstr, pos):
    #print("getTuple:"+mstr) 
    startKey = "("
    endKey = ")"
    splitKey = ","
    pos1 = mstr.find(startKey,pos)
    pos2 = mstr.find(splitKey,pos1)
    pos3 = mstr.find(endKey,pos2)
    val1 = mstr[pos1+1:pos2]
    val2 = mstr[pos2+1:pos3]
    return int(val1),int(val2), pos3

def getSignalStrategy(signaliStr):
    found = False
    pos = 0
    oldval1 = 0
    oldval2 = 0
    val1 = 0
    val2 = 0
    while not found:
        oldval1 = val1
        oldval2 = val2
        val1,val2,pos=getTuple(signaliStr,pos)        
        if val1 > oldval1:
            found = True
            if oldval2 == 1:
                enabled = True
            else:
                enabled = False
            return enabled,val1 #val1 is the delay of the phase, oldval2 indicates if phase is enabled
    return -1,-1
    
def getStrategy(outStr,greenModel,numberOfSignals):
    sigEnabled = [False] * numberOfSignals
    sigDuration = [0] * numberOfSignals
    for i in range(1,numberOfSignals+1):
        strStart = "signal["+str(i)+"]:"
        signaliStr = myGetSubString(outStr,strStart,greenModel)
        sigEnabled[i-1],sigDuration[i-1] = getSignalStrategy(signaliStr)
    return sigEnabled,sigDuration
    
def arrayToStratego(arr):
    arrstr = str(arr)
    arrstr = str.replace(arrstr, "[", "{", 1)
    arrstr = str.replace(arrstr, "]", "};", 1)
    return arrstr 

def convertPhase(phase,binaryPhaseIndices):
    for i in range(0,len(binaryPhaseIndices)):
        if phase == binaryPhaseIndices[i]:
            return str(i)

def createModel(master_model,expId,carsAreal,carsJammed,phase,duration,simStep,binaryPhasesDecimal,binaryPhaseIndices,tlID,nrOfSignals,yellowTime,greenModel,greenTimer):
    fo = open(master_model, "r+")
    str_model = fo.read()
    fo.close()

    if greenModel:
        toReplace = "//HOLDER_INITIAL_PHASE"
        value = "const max_signal_conf_t initialPhase = " + \
          convertPhase(phase,binaryPhaseIndices) + ";"
        str_model = str.replace(str_model, toReplace, value, 1)
        toReplace = "//HOLDER_GREEN_TIMER"
        value = "int greenTimer = " + \
          str(greenTimer) + ";"
        str_model = str.replace(str_model, toReplace, value, 1)

    #Setting different tl specific variables:
    toReplace = "//HOLDER_AMOUNT_OF_SIGNALS"
    value = str(nrOfSignals) + ";"
    str_model = str.replace(str_model, toReplace, value, 1)

    toReplace = "//HOLDER_SIGNAL_CONFS"
    value = ""
    for i in range(0,nrOfSignals):
        value += "2*"
    value = value[:-1]
    value += "-1;"
    str_model = str.replace(str_model, toReplace, value, 1)

    toReplace = "//HOLDER_FALSE_TIMES_SIGNALS"
    value = ""
    for i in range(0,nrOfSignals):
        value += "false,"
    value = value[:-1]
    str_model = str.replace(str_model, toReplace, value, 1)

    toReplace = "//HOLDER_COMP_SIGNALS"
    value = str(len(binaryPhasesDecimal)) + ";"
    str_model = str.replace(str_model, toReplace, value, 1)    
    
    #Placeholders in the bottom of the model:
    toReplace = "//HOLDER_CARS_AREAL"
    value = "int carsAreal[signal_t] = " + arrayToStratego(carsAreal)    
    str_model = str.replace(str_model, toReplace, value, 1)

    toReplace = "//HOLDER_CARS_JAMMED"
    value = "int carsJammed[signal_t] = " + arrayToStratego(carsJammed)
    str_model = str.replace(str_model, toReplace, value, 1)

    toReplace = "//HOLDER_SIM_STEP"
    value = "//SIM_STEP=" + str(simStep)
    str_model = str.replace(str_model, toReplace, value, 1)

    toReplace = "//HOLDER_BINARY_PHASES"
    value = ""
    for i in range (0,len(binaryPhasesDecimal)):
        value += str(binaryPhasesDecimal[i]) + ","
    value = value[:-1]
    str_model = str.replace(str_model, toReplace, value, 1)
        
    modelName = rootDir + "/UppaalModels/TrafficLightTempModels/tl-" + str(tlID) + "-" + str(expId) + ".xml"
    text_file = open(modelName, "w")
    text_file.write(str_model)
    text_file.close()
    return modelName

def createQuery(master_query,nrOfSignals,tlID):
    fo = open(master_query, "r+")
    str_query = fo.read()
    fo.close()

    toReplace = "//HOLDER_QUERY"
    value = ""
    for i in range (1,nrOfSignals+1):
        value += " signal[" + str(i) + "],"
    value = value[:-1]
    str_query = str.replace(str_query, toReplace, value, 1)

    queryName = rootDir + "/UppaalModels/TrafficLightTempModels/tempQuery" + str(tlID) + '.q'
    text_file = open(queryName, "w")
    text_file.write(str_query)
    text_file.close()
    return queryName

    
def cStratego(model,query,learningMet,succRuns,maxRuns,goodRuns,evalRuns,maxIterations,expId,
              carsAreal,carsJammed,phase,duration,simStep,nrOfSignals,binaryPhasesDecimal, 
              binaryPhases, binaryPhaseIndices,tlID,yellowTime,greenModel=False,greenTimer=0):      
    newModel = createModel(model,expId,carsAreal,carsJammed,phase,duration,simStep,binaryPhasesDecimal,binaryPhaseIndices,tlID,nrOfSignals,yellowTime,greenModel,greenTimer)
    newQuery = createQuery(query,nrOfSignals,tlID)
    stratego = VP.veriStratego + " "
    #'time '
    com = stratego
    args = "\"" + newModel+"\"" \
      + ' --learning-method ' + learningMet \
      + ' --good-runs ' + succRuns \
      + ' --total-runs ' + maxRuns \
      + ' --runs-pr-state ' + goodRuns \
      + ' --eval-runs ' + evalRuns \
      + ' --max-iterations ' + maxIterations \
      + ' --filter 0 '
    query = "\"" + newQuery + "\""

    #print("Calling stratego for traffic light strategy \n")
    time_avg_sim, out1 = runStratego(com,args,query)
    sigEnabled,sigDuration = getStrategy(out1,greenModel,nrOfSignals)
    #if(tlID == 'n15'):
        #print(out1)
        #print(sigEnabled)
    #print(sigDuration)
    #we hardcode the output to the concrete crossing where:
    #signals 1 2 are WE EW and 3 4 are NS SN
    # if no flag --stratego is provided, the programm would be the following:
    #    <tlLogic id="0" type="static" programID="0" offset="0">
    # the locations of the tls are      NESW
    #        <phase duration="31" state="GrGr"/>
    #        <phase duration="6"  state="yryr"/>
    #        <phase duration="31" state="rGrG"/>
    #        <phase duration="6"  state="ryry"/>
    #    </tlLogic>
    # we start with phase 2 where EW has green
    phase = 0
    duration = 0
    yellowPhase = 0
    #todo: check if we need yellowPhase
    signalsInBinary = ""
    for sig in sigEnabled:
        if sig:
            signalsInBinary += "1"
        else:
            signalsInBinary += "0"

    signalsInBinary = signalsInBinary[::-1]
    
    for i in range(0, len(binaryPhases)):
        if(binaryPhases[i] == signalsInBinary):
            phase = i

    """
    if sigEnabled[0]:
        phase = 0
        yellowPhase = 1
        duration = sigDuration[0]
    else:
        phase = 2
        yellowPhase = 4
        duration = sigDuration[5]
    """
    return phase,duration,yellowPhase

            
        
    
    
