import os
import sys
import random
import optparse
import subprocess
import math
import pandas as pd

from ReadResultFile import generate_results

def generate_multi_results():
    resultFiles = []
    startID = 4121
    endID = 4138
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

    resultFrame.to_csv("results/resultsMerge_start" + str(startID) + "_end" + str(endID)+ ".csv")

if __name__ == "__main__":
    resultFiles, startID, endID = generate_multi_results()
    get_stats(resultFiles, startID, endID)
