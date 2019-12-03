import os
import sys
import random
import optparse
import subprocess
import math
import pandas as pd

from ReadResultFile import generate_results

destFileString = ""

def generate_multi_results():
    resultFiles = []
    startID = 4178
    endID = 4180
    for i in range(startID,endID+1): #4000, 4084
        resultDestFile = "results/Results_" + str(i)+ ".csv"
        resultFiles.append(resultDestFile)
        generate_results(resultDestFile, "results/tripinfo" + str(i) + ".xml", "results/queueinfo" + str(i) + ".xml", i)
    
    return resultFiles, startID, endID

def get_stats(resultFiles, startID, endID):
    li = []
    for filename in resultFiles:
        df = pd.read_csv(filename, index_col=None, header=0)
        li.append(df)

    frame = pd.concat(li, axis=0, ignore_index=True)
    #Group every third
    frame = frame.groupby(frame.index // 3)

    results = []
    for grp in frame.groups:
        results.append(frame.get_group(grp).mean())

    resultFrame = pd.DataFrame(results)
    resultFrame.loc['mean'] = resultFrame.mean()
    resultFrame.loc['max'] = resultFrame.max()
    resultFrame = round(resultFrame,3)
    
    destFileString = "results/resultsMerge_start" + str(startID) + "_end" + str(endID)+ ".csv"
    resultFrame.to_csv(destFileString)

    return resultFrame, destFileString

def prep_table(frame, destFileString):
    frame = frame.drop(['ExperimentID', 'AverageQueueLengthExp', 'maxQueueLengthExp','95thPercentileLengthExp'], axis=1)
    frame = frame.rename(columns={"AverageDuration" : "ATT", "AverageTimeLoss":"AD", "AverageWaitingTime":"AWT", "AverageQueueLength":"AQL", "maxDuration":"MTT", "maxTimeLoss":"MD", "maxWaitingTime":"MWT", "maxQueueLength":"MQL","95thPercentileLength":"95%"})
    frame.to_csv(os.path.splitext(destFileString)[0] + "_latexrdy.csv")


if __name__ == "__main__":
    resultFiles, startID, endID = generate_multi_results()
    frame, destFileString = get_stats(resultFiles, startID, endID)
    prep_table(frame, destFileString)
