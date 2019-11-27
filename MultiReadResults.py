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
    startID = 4063
    endID = 4083
    for i in range(startID,endID+1): #4000, 4084
        resultDestFile = "results/Results_" + str(i)+ ".csv"
        resultFiles.append(resultDestFile)
        generate_results(resultDestFile, "results/tripinfo" + str(i) + ".xml", "results/queueinfo" + str(i) + ".xml", i)
    
    return resultFiles, startID, endID

def get_stats(resultFiles, startID, endID):
    li = []
    if len(resultFiles) % 3 != 0:
        sys.exit("Wrong amount of files entered")
    


    for fileNumber in range(0 , len(resultFiles) , 3):
        df1 = pd.read_csv(fileNumber[fileNumber], index_col=None, header=0)
        df2 = pd.read_csv(fileNumber[fileNumber+1], index_col=None, header=0)
        df3 = pd.read_csv(fileNumber[fileNumber+2], index_col=None, header=0)

        result_df = pd.concat([df1, df2, df3], axis=0, ignore_index=True)
        li.append(result_df.mean())
       

    frame = pd.concat(li, axis=0, ignore_index=True)
    frame.loc['mean'] = frame.mean()
    frame.loc['max'] = frame.max()

    frame.to_csv("results/resultsMerge_start" + str(startID) + "_end" + str(endID))

if __name__ == "__main__":
    resultFiles, startID, endID = generate_multi_results()
    get_stats(resultFiles, startID, endID)
