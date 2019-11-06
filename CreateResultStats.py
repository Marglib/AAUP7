import sys
import os
import optparse
from os.path import expanduser
from subprocess import Popen, PIPE, STDOUT, call
import pandas as pd

rootDir = os.path.abspath(os.getcwd())
pathToFiles = os.path.join(rootDir,'results')

def create_concat_df(listOfFiles):
    frames = []
    for f in listOfFiles:
        frames.append(pd.read_csv(os.path.join(pathToFiles,f)))

    result = pd.concat(frames)    
    return result

def generate_list_of_files(expIDs,runs):
    listOfFiles = []

    for i in range(0,len(expIDs)):
        currId = expIDs[i]
        for j in range(0,runs):
            listOfFiles.append("Results_tripinfo" + str(int(currId) + j))

    return listOfFiles

def create_statistics_file(expIDs,runs,filename):
    listOfFiles = generate_list_of_files(expIDs,runs)
    df = create_concat_df(listOfFiles)
    resultDir = os.path.join(pathToFiles, filename)
    df.to_csv(resultDir, index=False)
